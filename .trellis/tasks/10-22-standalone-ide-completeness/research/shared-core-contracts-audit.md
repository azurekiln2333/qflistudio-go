# Shared core (`qfli_studio_core`) contracts audit — read-only research

Scope: R3 (language chips/badges), R5 (highlighting + diagnostics wave underlines),
R6 (explorer reopening + persisted multi-root workspace), R7 (Problems / Output /
Debug Console / Terminal / Ports panels). Read-only; **no file in
`qfli_studio_core` was modified by this worker.**

Baseline: `qfli_studio_core` @ `main` `6441a5a`, worktree **dirty and actively
changing** (see §0). This audit observed the tree at two moments; §1 records that
the content-explorer worker landed its chips/badge work **while this audit was
running**, so §1 is a state report, not a work request.

---

## 0. Ownership and baseline warnings (read first)

Two shared-core task directories already exist and are owned by the C coordinator
(`w1R:p1`). Do not create a third overlapping batch:

| Task | Owns |
| --- | --- |
| `.trellis/tasks/10-22-offline-content-explorer` | `pages/local_content_pages.dart`, `content/local_content_adapter.dart`, `models/tutorial.dart`, `services/example_code_store.dart`, badge widget/project-card reuse, focused tests |
| `.trellis/tasks/10-22-offline-editor-analysis` | `services/code_analysis.dart` (new), `services/studio_profile.dart`, new `editor/diagnostic*`, `editor/open_file.dart`, `editor/editor_page.dart` (diagnostic integration only), `editor/highlight_themes.dart`, diagnostic/highlighting tests |

Both designs explicitly **exclude** `file_explorer.dart`, `project_history.dart`,
content models/pages/stores (from the analysis task) and reserve them for other
owners.

### Uncommitted work already present (unowned — do not clobber)

`git status` in `qfli_studio_core`, **first observation** (start of this audit):

```
 M lib/editor/file_explorer.dart
 M lib/editor/project_history.dart
?? test/file_explorer_state_test.dart
?? test/project_history_concurrency_test.dart
?? tool/java_content/java_topics_language.dart
?? .trellis/tasks/10-22-offline-content-explorer/
?? .trellis/tasks/10-22-offline-editor-analysis/
```

`git status`, **second observation** (end of this audit — the content-explorer
worker was writing concurrently):

```
 M lib/content/local_content_adapter.dart
 M lib/editor/file_explorer.dart
 M lib/editor/project_history.dart
 M lib/models/tutorial.dart
 M lib/pages/local_content_pages.dart
 M lib/services/example_code_store.dart
 M lib/services/tutorial_service.dart
 M lib/widgets/project_card.dart
 M test/local_content_lazy_catalog_test.dart
 M tool/verify_java_content.dart
?? lib/content/java_catalog_audit.dart
?? lib/widgets/language_badge.dart
?? test/file_explorer_state_test.dart
?? test/project_history_concurrency_test.dart
?? tool/java_content/java_topics_language.dart
?? .trellis/tasks/10-22-offline-content-explorer/
?? .trellis/tasks/10-22-offline-editor-analysis/
```

Consequence: **any later reader must re-run `git status`/`git diff` in
`qfli_studio_core` before planning shared edits.** Two workers are already live in
that worktree. The `file_explorer.dart` / `project_history.dart` change set below
was unowned at both observations.

**The dirty `file_explorer.dart` already implements most of R6's sidebar half.**
The PRD/acceptance claim “`FileExplorer.initState` rebuilds the root without
calling `_restoreExpanded`” is **stale against the working tree**. Current dirty
code has:

- `_rebuildRoot()` now ends with `_restoring = _restoreExpanded();` — so
  `initState` restores expansion on first construction, and `_switchProject` no
  longer calls `_restoreExpanded()` separately (`lib/editor/file_explorer.dart`
  lines ~143–160).
- `int _treeGeneration` + `Future<void>? _restoring`; `_verifyBrowsing`,
  `_restoreExpanded`, `_loadChildren(…, {int? generation})` and `_refresh` all
  re-check `mounted && generation == _treeGeneration` before `setState`.
- `_restoreExpanded` normalizes, rejects paths outside the root
  (`p.isWithin(projectPath, abs)`), and uses async `Directory(abs).exists()`.
- `_toggle` became `Future<void>` and awaits `_restoring` before mutating
  `_expanded`, so a tap cannot be undone by a late restore nor persist an
  incomplete set.
- `project_history.dart` gained a per-root serialized write queue
  (`_writes`, `_enqueue`, `_write`, `_read`), snapshotting caller collections, so
  a reconstructed explorer that loads before a predecessor’s unawaited
  `saveExpandedDirs` finishes observes the queued write.

Committed state at `6441a5a`: `_rebuildRoot()` had **no** restore call;
`_restoreExpanded` had no generation guard; `_toggle` was sync; `ProjectHistory`
had no write queue. So R6 “reopening preserves expansion” is already addressed in
the dirty tree plus two new tests (`test/file_explorer_state_test.dart`,
`test/project_history_concurrency_test.dart`).

**Action for whoever owns R6:** identify that owner, keep the dirty diff, and
scope any further work to *only* the still-missing parts (§4 multi-root
workspace). Do not reset the worktree.

---

## 1. R3 — learning language chips and title badges

**Status: implemented in the dirty worktree by the content-explorer worker while
this audit ran; not committed and not yet independently verified.** See §0.

### Exact current paths

| Concern | Path | State |
| --- | --- | --- |
| Offline tutorial/example pages | `lib/pages/local_content_pages.dart` | **modified**: `_TutorialList`/`_ExampleCodeList` became `StatefulWidget`s; new `_ContentFilterSelection` (query/language/level), `_ContentFilterBar`, `_ContentTitle`, `_emptyResults`, `_ContentLabels`, `_contentLanguage(type, language)`; `itemCount` is now `rows.length + 1` with row 0 = filter bar |
| Shared badge (new) | `lib/widgets/language_badge.dart` | `languageKey()` (`'c++' → 'cpp'`), `languageLabel()` (C/C++ distinct, MD for markdown), `LanguageBadge` circular chip with `Semantics` + `FittedBox` |
| Adapter | `lib/content/local_content_adapter.dart` | passes `language:`/`level:` (small diff) |
| Page models | `lib/models/tutorial.dart` | `TutorialLesson.language/.level`, `ExampleCode.language/.level` (+25 lines dirty) |
| Project card | `lib/widgets/project_card.dart` | **modified** to reuse the shared badge |
| Aggregate models / filter | `lib/content/content_repository.dart` | `ContentEntry.language/.level/.type`; `ContentFilter{language,type,locale,types}` — **still no `level`**, and the new UI filters client-side over loaded rows, which matches the task design |
| Saved-example persistence | `lib/services/example_code_store.dart` | writes `language`/`level` only when non-empty; reads default `''` |
| Project language identity | `lib/services/project_templates.dart` | `ProjectLanguages.all` has distinct `'C'` and `'C++'` |
| Home-page chip pattern (pre-existing precedent) | `lib/pages/home_page.dart` ~640–720 | `FilterChip` row in a horizontal `SingleChildScrollView`, hidden when `showHomeTabs == false` or `chips.length <= 1` |

### Verified facts to build acceptance on

1. Chip candidates are derived from **loaded rows**
   (`for (final lesson in lessons) _contentLanguage(lesson.type, lesson.language)`
   and `lesson.level`) plus the profile, not from a hardcoded list — so a
   degraded/empty catalog cannot advertise a language it cannot serve. Keep it
   that way.
2. Levels in the shipped aggregate are `beginner | intermediate | advanced`;
   the bar renders a translated label via `_ContentLabels.level(...)`.
3. `ContentProductTypes.byProduct['forge'] == {'c','cpp'}` — the only shipped
   profile whose content spans several languages, i.e. **the** C/C++
   distinctness case. `script` = `{lua, javascript, typescript, shell}`;
   `webforge` = `{html, css, javascript}`; `qflistudio` = all 16.
4. Aggregate content facts (measured from `assets/content/tutorials.json`):
   `{schemaVersion, kind, updatedAt, entries[]}`; 16 languages
   (`c, cpp, css, dart, go, html, java, javascript, json, lua, markdown, python,
   rust, shell, sql, typescript`), counts `go` = 120, `python` = 120, others = 100.
   `assets/content/examples.json` is the 1.9 MB parallel aggregate. Per-language
   legacy files also still exist under `assets/tutorials/*.json`
   (`c, cpp, dart, java, lua, python, web`) — none for go/rust/sql.
5. `qfli_go` ships **no** `assets/content/` of its own and does not set
   `contentRepositoryFactory`; it reads the shared
   `packages/qfli_studio_core/assets/content/*.json`. Go entries (120, all
   `level: beginner|intermediate|advanced`) live in the shared aggregate. Note
   `qfli_go/ohos/entry/src/main/resources/rawfile/flutter_assets/...` contains a
   checked-in **stale copy** of that aggregate — never treat it as the source.

### Remaining verification work (not code gaps)

- Real widget tests for **C vs C++** chips on a `forge`-like profile, and for
  **combined** query + language + level + reset + no-result states on both tabs.
- Narrow-width / large-text checks: the filter bar plus circular badges must not
  overflow; `project_card.dart` already hides trailing metadata below 172 dp and
  above 1.6 text scale.
- Badge presence on **detail** titles (`ExampleDetailPage`, `_LessonPage`) —
  `LanguageBadge` now appears in the title widget and detail paths; assert it.
- `assets/tutorials/*.json` legacy per-language files are still parsed by
  `ContentCatalog.fromJson` compatibility paths; confirm they still load after
  the model change.

### Regression boundaries

- `test/local_content_lazy_catalog_test.dart` — **already updated** by the worker
  from `estimatedChildCount == 102` to `103` with the comment “One shared filter
  header, two chapter rows and one hundred lazy lessons”. Any further header row
  must update this deliberately, and the
  `childrenDelegate is SliverChildBuilderDelegate` assertion must keep passing
  (filtering must not degrade to an eager `ListView(children: …)`).
- `test/content_idle_frames_test.dart`, `test/content_code_import_test.dart`,
  `test/content_repository_test.dart`, `test/asset_content_performance_test.dart`,
  `test/home_content_repository_test.dart`, `test/java_content_render_test.dart`,
  `test/python_content_render_test.dart`, `test/tutorial_test.dart`,
  `test/structured_content_test.dart`.
- `ExampleCode.copyWith` only copies `code`/`summary`; saved edits must keep
  metadata via `withCatalogMetadata`. Do not add a `copyWith` field that drops it.
- `example_code_store.dart` `contentVersion = 2` purges legacy **Java** records on
  load — never bump it for a metadata-only change or users lose saved Java
  examples.
- `tool/java_content/java_topics_language.dart`, `lib/content/java_catalog_audit.dart`
  and `tool/verify_java_content.dart` are new/rewritten by that worker; they are
  outside the Go coordinator's scope but part of the same dirty tree.

---

## 2. R5a — missing Go/Lua/Rust/SQL highlighting

### Exact current path

`lib/editor/highlight_themes.dart`:

- imports only `c, cpp, css, dart, java, javascript, json, kotlin, markdown,
  python, xml` from `re_highlight/languages/*`.
- `static final Map<String, Mode> _languages` — 11 entries.
- `static const _extToLang` — `.dart .java .py .c .h .cpp .hpp .cc .cxx .kt .kts
  .js .mjs .ts .jsx .tsx .css .scss .html .htm .xml .svg .json .md .markdown`.
- `themeFor()` resolves `grammar?.scopeName ?? _extToLang[extension]`; returns
  `null` (plain text) on a miss; caches by language/`tm:`+scope with
  `settings.highlightRevision`/brightness invalidation; `maxFileSize = 256 KB`,
  `maxLineLength = 2048`.

### Verified facts

Installed dependency is `re_highlight 0.0.3`
(`D:\AppData\Local\Pub\Cache\hosted\pub.dev\re_highlight-0.0.3`), 196 grammars.
The four missing ones **already ship** as `final Mode` values:

```dart
import 'package:re_highlight/languages/go.dart';    // langGo
import 'package:re_highlight/languages/lua.dart';   // langLua
import 'package:re_highlight/languages/rust.dart';  // langRust
import 'package:re_highlight/languages/sql.dart';   // langSql
```

Also available and currently unused: `bash.dart` (`langBash`), `shell.dart`
(`langShell`), `typescript.dart`, `ini.dart`, `yaml.dart`, `plaintext.dart`.

Missing extension mappings relative to shipped profiles
(`qfli_lua` → `.lua/.luac`, `qfli_rust` → `.rs`, `qfli_sql` → `.sql`,
`qfli_go` → `.go`, `qfli_python` → `.py/.mpy`):

| Extension | Should map to | Today |
| --- | --- | --- |
| `.go` | `go` | none → plain text |
| `.lua`, `.luac` | `lua` | none |
| `.rs` | `rust` | none |
| `.sql` | `sql` | none |
| `.sh`, `.bash` | `shell` or `bash` | none |
| `.mpy` | `python` | none |
| `.yaml`, `.yml` | `yaml` | none |
| `.toml`, `.ini` | `ini` | none |
| `.ts` | `typescript` | mapped to `javascript` (existing behavior; changing it is a visible regression risk) |
| `.h` | currently `c` | keep `c` unless the C coordinator asks otherwise |

### Feasible change

Add 4 imports + 4 `_languages` entries + extension entries in
`_extToLang`. Add `tokenLabels`/`_tokenScopes` entries only if a new token class
must be themable. The `xml` branch registers `css`/`javascript` sub-modes;
`go`/`lua`/`rust`/`sql` need no sub-modes.

**Do not** touch `highlight_import.dart` (TextMate theme import) or
`textmate_grammar.dart`; they are a separate mechanism and already covered by
`test/highlight_preferences_test.dart` and `test/highlight_worker_test.dart`.

### Regression boundaries

- `test/highlight_worker_test.dart` exercises the **worker** path with a
  hand-built `CodeHighlightTheme(languages: {'css': …})`; it does not go through
  `_languages`. Adding grammars must not change its expectations.
- `HighlightThemes._cache` is invalidated on settings identity/revision/brightness;
  a new language must not require a new cache key dimension.
- Large-file guards (`maxFileSize` 256 KB, `maxLineLength` 2048) must still return
  `null` → plain text. `test/open_performance_test.dart` covers open behavior.
- New tests should assert **actual token spans** (keyword/string/comment ranges)
  for each new language, per the analysis task’s acceptance criteria, not just
  `themeFor(...) != null`.

---

## 3. R5b — diagnostics wave underlines (feasibility verified)

### Contract already published (frozen by the analysis task)

`package:qfli_studio_core/services/code_analysis.dart` (to be created) with
`CodeAnalyzer`, `CodeDocumentSnapshot{path,text,revision}`,
`CodeAnalysisRequest{projectPath,activeFilePath,language,revision,documents}`,
`CodeDiagnosticSeverity{error,warning,information,hint}`,
`CodeDiagnostic{filePath,startOffset,endOffset,message,severity,source,code}`
(UTF-16 half-open), `CodeAnalysisResult{diagnostics,unavailableReason}`; plus
`StudioProfile.codeAnalyzer`. See
`qfli_studio_core/.trellis/tasks/10-22-offline-editor-analysis/design.md`.

### Verified integration facts that constrain the implementation

1. **Span builder is constructor-only.** In the vendored editor
   (`qfli_studio_core/vendor/re_editor`, `re_editor 0.10.0`):

   ```dart
   // lib/src/code_line.dart
   typedef CodeLineSpanBuilder = TextSpan Function({
     required BuildContext context, required int index, required CodeLine codeLine,
     required TextSpan textSpan, required TextStyle style,
   });
   factory CodeLineEditingController({CodeLines codeLines, CodeLineOptions options,
     CodeLineSpanBuilder? spanBuilder});
   factory CodeLineEditingController.fromText(String? text, [CodeLineOptions options]);
   ```
   `spanBuilder` is a **`final` field** on `_CodeLineEditingControllerImpl`
   (`lib/src/_code_line.dart` line 17) — there is no setter. `fromText` does not
   forward it. Consumption is `_code_line.dart` ~1955:
   `return spanBuilder?.call(...) ?? textSpan;`

2. **`OpenFile` currently cannot carry a span builder.**
   `lib/editor/open_file.dart` builds
   `controller = CodeLineEditingController.fromText(content)`.
   Feasible, behavior-preserving replacement:

   ```dart
   controller = CodeLineEditingController(
     codeLines: content.codeLines,          // same extension fromText uses
     spanBuilder: (…) => …,                 // closure over a diagnostics store
   );
   ```
   (`_CodeLineEditingControllerImpl.fromText` is literally
   `_CodeLineEditingControllerImpl(codeLines: text?.codeLines ?? _kInitialCodeLines)`.)
   This is why the analysis task lists `editor/open_file.dart` as an owned file.

3. **Repaint hook exists:** `CodeLineEditingController.forceRepaint()`
   (`lib/src/code_line.dart` line 362 → `_render?.forceRepaint()`). Use it after
   diagnostics change instead of mutating `codeLines` (which would create undo
   entries and dirty the file).

4. **Revision semantics already exist and are exactly right.**
   `EditorController._markDirty` (`lib/editor/editor_controller.dart`) bumps
   `open.revision` **only** when `!identical(preValue.codeLines, value.codeLines)`,
   i.e. selection/composing changes do not bump it — so `revision` is a correct
   staleness key. `EditorController.onContentChanged` (constructor param) is the
   debounce trigger point. Do not add a second content listener.

5. **Owner root/file identity already exists.** `OpenFile.ownerProjectName` and
   `OpenFile.projectRootPath` are set by `EditorController.openPath(ownerProjectName:
   …, ownerProjectPath: …)` and used by `tabLabel()`. Diagnostics must resolve the
   **owning** root from these fields, not from `EditorController.project`.

6. **Retained editors keep running while offstage.** `retained_editor_host.dart`
   wraps retained sessions in `Offstage(offstage: !visible)` +
   `TickerMode(enabled: interactive)` + `ExcludeFocus/IgnorePointer`; the
   `EditorPage` **State stays mounted** and listeners stay attached.
   `EditorPage.retainedVisibility` (`ValueListenable<bool>?`, line 98, listener at
   line 198/238, callback `_onRetainedVisibilityChanged`) is the correct gate:
   suspend/limit analysis when it is not `true`. Without this, every minimized
   project keeps analyzing.

7. **Rendering target.** `EditorPage._buildCodeView` (`lib/editor/editor_page.dart`
   ~2331) builds `CodeEditor(controller: open.controller, …,
   style: CodeEditorStyle(..., codeTheme: theme, textColor: …))`. A wavy
   decoration must be applied by rebuilding `textSpan` children with
   `TextStyle(decoration: TextDecoration.underline,
   decorationStyle: TextDecorationStyle.wavy, decorationColor: …)` while
   preserving each child’s existing `color/fontWeight/background`. Splitting must
   be done on **UTF-16 offsets relative to the line text**, clipped to
   `[0, codeLine.text.length]`, and must tolerate empty ranges (insertion
   diagnostics → zero-width, draw nothing or a 1-px caret-width mark).

### Regression boundaries

`test/editor_run_test.dart`, `test/offline_editor_gates_test.dart`,
`test/retained_editor_test.dart`,
`test/retained_editor_restore_control_test.dart`,
`test/retained_editor_restore_control_integration_test.dart`,
`test/retained_editor_animation_test.dart`, `test/open_performance_test.dart`,
`test/highlight_worker_test.dart`, `test/editor_terminal_touch_test.dart`,
`test/file_history_test.dart` (read-only snapshots must not request analysis).

---

## 4. R6 — persisted multi-root workspace

### Exact current state (no workspace concept exists)

- `lib/store/project_store.dart`: `ProjectStore extends ChangeNotifier` with a
  flat `List<Project> _projects`, `String? lastBrowsedProjectId`,
  `setBrowsedProject(Project)` (persists immediately),
  `Future<ProjectResult> createProject/addExisting/importProjectArchive/…`,
  `refresh()`, `Future<void> _persist()` writing
  `{'version': 1, 'projects': [...], 'lastBrowsedProjectId': ...}` atomically
  (temp file + rename) with serialized writes (`_writes`, `_revision`) and
  `compute(_readProjectRegistry, path)` for reads.
- `lib/editor/project_history.dart`: **per project root** file
  `history.json` = `{version:1, openFiles, activeFile, expandedDirs, files{cursor}}`
  with `load/save/saveExpandedDirs`; dirty tree adds the write queue.
- `lib/editor/file_explorer.dart`: single browsing root `Project _browsing`,
  `_root`, `_children`, `_expanded`; `_switchProject` +
  `PopupMenuButton<Project>` for cross-project browsing.
- `lib/editor/editor_controller.dart`: one `final Project project`, but each
  `OpenFile` carries `ownerProjectName` / `projectRootPath`.
- `lib/store/settings_store.dart` and `lib/services/app_paths.dart`
  (`storageDirectory()`, `projectsRoot()`, `languageProjectsRoot()`): app-private
  JSON storage — the natural place for a workspace document.
- Grep for `workspace` in `lib/`: only unrelated strings
  (`/workspace` in the online terminal, a comment in `studio_profile.dart`).
  **No multi-root model, no workspace ID/name, no root ordering.**

### Feasible optional API (additive, migration-safe)

New file (new owner): `lib/services/workspace_store.dart` (or
`lib/store/workspace_store.dart`) with a versioned document, e.g.

```dart
class WorkspaceRoot { final String projectId; final String path; final int order; }
class Workspace { final String id, name; final List<WorkspaceRoot> roots; final String? activeProjectId; }
// persisted: {'schemaVersion': 1, 'activeWorkspaceId': ..., 'workspaces': [...]}
```

Constraints verified against existing code:

- Reference roots by **`Project.id`** plus a cached `path` **fallback**, because
  `_readProjectRegistry` already tolerates missing/corrupt entries and
  `ProjectConfig.readMetadata(path)` overrides name/language/type at read time.
  Load must degrade to “root missing” rows rather than dropping projects
  (R6 “missing roots”), and must never delete directories.
- Persist under `AppPaths.storageDirectory()` next to `registry.json`
  (`ProjectStore._resolveStorageFile`) so backup/restore
  (`services/app_backup_service.dart`) and `app_private_roots.dart` stay coherent.
- Migration: when no workspace document exists, synthesize
  `Workspace(id: 'default', roots: [lastBrowsedProjectId ?? first project])` so
  existing single-project sessions behave identically. Do **not** change
  `ProjectStore`’s registry `version: 1` schema; a sibling file keeps
  `_readProjectRegistry`/`compute` isolated.
- UI: `FileExplorer` currently takes `required Project project`. Multi-root needs
  either a roots list + per-root expansion keys (the `_expanded` set already keys
  on absolute paths, and `ProjectHistory` is already per-root — so the data model
  already supports N roots if the widget iterates roots), or a workspace-aware
  wrapper. Note `_persistExpanded()` filters with
  `p.isWithin(_browsing.path, path)` and stores **relative** paths, which is
  correct per root and must stay per root.
- Ownership of open files/run/diagnostics/history: already per-`OpenFile` and
  per-root `history.json`; the only change is that “current project” becomes
  “owning root of the active file” for run commands
  (`_activeFileRunError(open)` already receives `open`), terminals
  (`TerminalPane.workingDirectory`), and Problems navigation.

### Regression boundaries

- `test/file_explorer_state_test.dart`, `test/project_history_concurrency_test.dart`
  (new, unowned) assert single-root behavior, rapid project switching,
  `store.lastBrowsedProjectId`, and that an opened file’s
  `projectRootPath`/`ownerProjectName` match the browsed root — multi-root must
  keep all of that true.
- `test/app_backup_test.dart`, `app_backup_codec_test.dart`,
  `app_backup_recovery_test.dart`, `app_backup_validation_test.dart`,
  `app_backup_safety_test.dart`, `app_private_roots_test.dart`,
  `project_archive_test.dart`, `project_zip_test.dart` — any new persisted file
  under the storage dir can change backup contents/size expectations.
- `test/home_project_scope_test.dart`, `test/home_search_archive_test.dart`,
  `test/home_navigation_test.dart` cover project scoping on the home page.
- `test/file_history_test.dart` and `services/recycle_bin.dart` /
  `RecoveryService` — do not make a workspace delete anything.

---

## 5. R7 — Problems / Output / Debug Console / Terminal / Ports panels

### Exact current state

| Concern | Path | State |
| --- | --- | --- |
| Bottom panel selector | `lib/editor/editor_page.dart` line 51 `enum _BottomPanel { none, terminal, ai }`, field `_BottomPanel _bottomPanel`, getter `_terminalVisible` | **Exclusive two-slot design**, not a tab strip. No Problems/Output/Debug/Ports slot. |
| Terminal panel widget | `lib/editor/terminal_pane.dart` (`TerminalPane` + `TerminalPaneState`, ~69 KB) | Owns its own `_sessions` list, header/tab strip, prompt, output buffer |
| Terminal tab strip | `lib/terminal/widgets/terminal_tabs.dart` | Session pills (terminal sessions only) |
| Terminal sessions/state | `lib/terminal/models/terminal_session.dart`, `lib/terminal/state/terminal_manager.dart` | `TerminalManager` (used by the full-screen terminal), `TerminalSession` with bounded `_lines`, `maxLines`, `_history` |
| Terminal backends | `lib/terminal/shell/{shell_backend,sandbox_shell_backend,local_shell,portable_filesystem}.dart` | `SandboxShellBackend`, `OutputKind{stdout,stderr,control,system}` |
| Runtime output | `lib/services/runner_service.dart`, `lib/services/demo_run_service.dart`, `lib/services/process_supervisor.dart` | `ProgramRunResult{title,stdout,stderr,exitCode,cancel}`; `RunnerService` also starts `LocalWebServer` (line 146) |
| Only real local listener | `lib/services/local_web_server.dart` | `HttpServer.bind(InternetAddress.loopbackIPv4, 0)` → `port`, `url`, `debugBuffer` (bounded 500 → trims to 100), `stop()` |
| Profile capability fields | `lib/services/studio_profile.dart` | `runtimeKind`, `runtimeStatus` ('available' reserved for a tested path), `supportedFileExtensions`; nothing for debugger/ports |
| Temporary UI tracing | `lib/editor/editor_page_diag.dart` | `EditorPageDiag` — debug ring buffer, **not** diagnostics |

Grep confirms: **no `ServerSocket`/socket bind anywhere except
`local_web_server.dart`**; no debugger, breakpoint, `Ports`, `Output` or
`DebugConsole` implementation exists in `lib/`.

### Feasible design that fits what exists

1. **Widen the selector, do not rewrite the pane.**
   `enum _BottomPanel { none, terminal, problems, output, debugConsole, ports, ai }`
   and make the panel host a small header (Material `SegmentedButton`/`TabBar`)
   above either `TerminalPane` (existing, unchanged props:
   `workingDirectory, auth, onClose, onCollapseChanged, onResizeDelta,
   onResizeStart/End, onActivated, onInputFocusChanged, collapsed, compact`) or a
   new panel body. `TerminalPanelMetrics` (in `terminal_pane.dart`, lines 28–50)
   already centralizes heights; reuse it so the editor’s
   `compactPanel`/`collapsed` math and `TerminalPanelMetrics.collapseThreshold`
   logic keep working.
   Risk: `_terminalInputHasFocus` and the `Offstage(offstage: _bottomPanel !=
   _BottomPanel.terminal || …)` block (editor_page.dart ~1800–1830) assume a
   single visible panel; the keyboard-preserving rule (“never hide the terminal
   while its input holds focus”) must be preserved when switching tabs.

2. **Problems** — owned by `10-22-offline-editor-analysis` (adds a bottom-panel
   tab + navigation). It should land **first** and define the tab-selection
   mechanism the other panels reuse, otherwise two workers will edit the same
   `_BottomPanel` region concurrently.

3. **Output** — a bounded, labeled, cancellable log. Cheapest correct model:
   a per-run `Stream<String>` consumer mirroring
   `terminal_pane.dart`’s `attachOutput({stdout, stderr, exitCode})` and its
   `_maxLines` trimming (`lib/editor/terminal_pane.dart` ~826/979). Reuse
   `ProgramRunResult` rather than inventing a second run type. Distinguish
   `cancel` from `clear` (R7 requires this explicitly).

4. **Debug Console** — can only be an honest echo/eval-less transcript until a
   real backend exists. **No decorative breakpoints.** Real debugger
   feasibility: neither `ProgramRunner` nor `TerminalCommandDelegate` exposes
   pause/step; the Go runtime is Yaegi-over-FFI and the shared shell is an
   in-app sandbox — no ptrace/gdbserver path. Therefore the capability must be
   advertised as unsupported (`runtimeStatus`), and controls hidden or disabled
   with an explicit reason. Any “pause/step/resume/stop” UI without backend
   semantics fails R7.

5. **Ports** — genuinely feasible *only* for locally owned listeners. Today that
   is exactly one: `LocalWebServer` (ephemeral loopback port, created in
   `editor_page.dart` line 1026 and `runner_service.dart` line 146). Feasible
   minimal contract: an in-process registry (e.g.
   `lib/services/local_port_registry.dart`) that sessions register/unregister
   (`port`, `owner`, `url`, `protocol`, `projectPath`) and a panel that lists
   them with copy/open actions. **No automatic forwarding or exposure**
   (`0.0.0.0` bind, tunnels, remote debug) — that is explicitly excluded.
   Dart/Flutter has no portable “list my process’s listening sockets” API on
   OHOS, so do **not** claim enumeration of arbitrary listeners.

### Regression boundaries

- `test/terminal_pane_test.dart`, `test/terminal_tab_bar_test.dart`,
  `test/terminal_manager_delegate_test.dart`, `test/terminal_compact_focus_test.dart`,
  `test/terminal_input_behavior_test.dart`, `test/terminal_terminal_touch_test.dart`
  (`test/editor_terminal_touch_test.dart`), `test/sandbox_terminal_test.dart`,
  `test/shell_command_test.dart` — terminal behavior, focus and compact layout are
  heavily pinned; the panel-tab change must not alter them.
- Spec constraint: `qfli_studio_core/.trellis/spec/frontend/component-guidelines.md`
  — terminal Return **must** use `TerminalInputBehavior.action`
  (`TextInputAction.unspecified`) and
  `TerminalInputBehavior.focusAndShowKeyboard`; any new panel input (Output
  filter, Problems filter, Debug Console prompt) must follow the same rule.
- `test/editor_run_test.dart` (run → terminal output), `test/offline_tools_test.dart`,
  `test/tools_grid_test.dart`, `test/offline_background_and_shortcuts_test.dart`.
- `ProgramRunResult.exitCode` must keep using `kProgramNotRunExitCode` (127) for
  “backend never started”; panels must not reinterpret 127 as a program failure.
- Retained/minimized editor: panel state lives in `EditorPage` State, which
  survives minimization — `TerminalPane` is created lazily (`_terminalCreated`)
  and must stay lazy so offstage projects do not spawn sandboxes/servers.
- `LocalWebServer.stop()` closing `_debugController` then
  `_server.close(force: true)` — a Ports panel must not hold it open, and must
  tolerate already-stopped servers.

---

## 6. Suggested ordering for the shared integrator

Observed live state when this audit closed:

| Requirement | Live state in the `qfli_studio_core` worktree |
| --- | --- |
| R3 chips/badges | **Mostly landed**, dirty/uncommitted (content-explorer worker) |
| R5 grammar registration (Go/Lua/Rust/SQL) | **Not started** — `highlight_themes.dart` untouched |
| R5 diagnostics + Problems | **Not started** — design frozen, no `services/code_analysis.dart`; defines the bottom-panel tab mechanism |
| R6 sidebar restore | **Implemented**, dirty/unowned, plus two new tests |
| R6 multi-root workspace | **Not started**, no owner |
| R7 Output / Debug Console / Ports | **Not started**, no owner |

Ordering that avoids two workers in the same file:

1. Finish and verify R3 (content-explorer worker already owns those paths).
2. `10-22-offline-editor-analysis`: `code_analysis.dart` +
   `StudioProfile.codeAnalyzer` + grammars (§2) + Problems tab (it defines the
   bottom-panel tab mechanism the §5 panels must reuse).
3. Accept/commit the R6 sidebar change set (§0) under a named owner; keep its two
   tests.
4. New, unclaimed: multi-root workspace store (§4).
5. New, unclaimed: Output / Debug Console / Ports panels (§5), after step 2.

## 7. Honest open questions for the coordinator

- Who owns the uncommitted `file_explorer.dart` / `project_history.dart` change
  set and its two new tests? It is the de-facto R6 sidebar implementation.
- `lib/widgets/project_card.dart` is now also dirty (badge reuse) without being
  listed in either task's owned files — confirm the content-explorer worker owns
  it, since R3 requires consistency with project lists.
- Does any product actually need multi-root workspaces (which profile exposes a
  workspace UI), or is R6 satisfied with persisted per-project expansion?
  `ProjectStore` today is a flat registry with one `lastBrowsedProjectId`.
- Confirm the Debug Console is allowed to be a transcript-only panel with an
  explicitly unsupported debugger capability, since no backend exists (§5.4).
- Confirm Ports may list only app-owned listeners (§5.5): neither Dart nor the
  OHOS engine exposes a portable enumeration of arbitrary listening sockets.
