# Go saved-workspace source handoff

Date: 2026-10-24, Asia/Shanghai. Owner: `workspace_go_1024`.

This is a source-only handoff. No Go, gofmt, Dart, Flutter, analyzer, test,
native build, package, WSL or device command was started. The new tests have
not been formatted, compiled or executed. They do not establish a host or OHOS
pass, and the all-product/task acceptance remains open.

## Changes and ownership

- Added `test/go_saved_workspaces_test.dart`, using the actual `goProfile`,
  public shared stores/widgets, two registered Go projects and real temporary
  filesystem fixtures. No main-profile replacement or product-key change.
- Updated only the workspace portion of `test/go_offline_profile_test.dart`:
  require the local workspace label and four local scopes, retaining the
  existing no-cloud assertion. Its pre-existing `ToolsGrid` import and card
  checks were preserved.
- Added this report. No shared core, `lib/`, native source, sibling product,
  task status, commit or branch was changed by this worker.

## Shared dependency is now present in source

At the beginning of this continuation the main-only guard was still present.
During authoring, the shared owner added the capability below. The earlier
source-gap finding in `go-product-integration-source-review-20261023.md` is
superseded for these entry guards by this snapshot; it remains historical
evidence rather than a claim of an executed failure.

- `StudioProfile.supportsSavedWorkspaces` defaults to true.
- `saved_workspace.dart` exports the capability separately from
  `isMainStudioRelease`.
- Home includes `_ProjectScope.workspace` when that capability is enabled and
  evaluates cloud policy independently. The real Go profile does not opt out.
- The unsaved explorer selects the named workspace dialog using the capability.
  Existing explicit saved sessions can still be managed.
- Legacy standalone history restoration continues to use `isMainStudioRelease`
  separately. The test file checks it independently of named save/reopen.

The parent acknowledged this fresh source change and authorized activating the
entry cases and replacing the former three-scope expectation. All eight new
cases are active; there are no skips or capability-faking branches.

The inspected shared `saved-workspaces.md` scope text still describes a
main-only entry. Its shared owner should reconcile that documentation with the
new optional standalone capability; this worker did not edit shared specs.

## New acceptance cases, all unexecuted

1. Real Go Home exposes the fourth local named-workspace scope and opens its
   actual `SavedWorkspacesTab`, while the cloud scope is absent.
2. A standalone Go explorer opens the named save dialog, selects the other Go
   root, persists ordered membership/primary metadata and preserves source.
3. An existing saved workspace is renamed and then removed through its settings
   and confirmation dialogs; source files and project registration survive.
4. A new store instance reloads the disk document. Its actual card opens the
   named session, followed by real `EditorPage` restoration of ordered files,
   owner names/paths/types, distinct cursors, active owner and source text.
   Toolbar collapse/reopen and full page reconstruction check both independently
   expanded roots. A conflicting legacy session does not replace the named
   session; workspace JSON excludes source buffers.
5. A standalone real Go profile independently restores legacy cross-root
   documents, active owner, cursors and expansion without creating a named
   workspace. This is migration preservation, not named-entry evidence.
6. Missing primary: the card visibly reports it, waits for confirmation,
   preserves workspace identity, selects the surviving owner and reconstructs
   only the surviving tree/tab.
7. Missing secondary: the same real path retains the original primary and skips
   the unavailable owner.
8. All members missing: the card offers an actionable refusal, opens no editor
   and preserves the record and parked fixture sources when closed.

The fixture creates fresh secondary stores in the real IO zone before awaiting
their first load. UI-originated queued writes drain through bounded fake-time
pumps interleaved with real IO, including `ProjectHistory.load` for both roots
after unmounting and before fixture deletion. No teardown framework exception
is discarded. Dialog entry/action checks use physical taps and hit-testable
finders; tree checks are scoped to their root and open the sidebar first.

## Validation and remaining execution

Source inspection checked public constructor/field names and the current
capability gates. Scoped `git diff --check` reported no whitespace errors in the
tracked offline test; Git emitted its existing LF-to-CRLF worktree notice.
Read-only Python inspection found no trailing whitespace in the two tests or
this report, and all thirteen recorded file hashes still matched on final read.
No Dart formatter or compiler validation is claimed for the new file.

After a new named grant, the coordinator should format/check the two Go tests,
run the eight new cases and the existing offline-profile suite serially, and
run scoped analysis against a stable shared snapshot. Any failure must retain
its real output and exact process handle. Current OHOS workspace behavior,
native runtime repairs and full umbrella checks remain separate open gates.

## Exact source snapshot

These SHA-256 values bind the inspected bytes, not a shared-core freeze. Go HEAD
was `82e17af4233e3aa2c6dd8eac2cb3f808f0f20a4f`; shared-core HEAD was
`e025805b60435fdedafd33e60082dc660afebe5a`, with current uncommitted shared
changes. Recompute before executing if the owner publishes another checkpoint.

| File, relative to Go repository | SHA-256 |
| --- | --- |
| `test/go_saved_workspaces_test.dart` | `1199ee3628f42bd14131aff4e9d8ae99066efbcdab3478f523cbc4ded581dc1b` |
| `test/go_offline_profile_test.dart` | `408c82044ebd373184646d8f42ac0b5bab7f48c520c44552dcc9fe14aad987ec` |
| `lib/main.dart` | `af2d50cc8a183c7131636bc6bacf4de6ed932efa0747fb69c4a5c78ed9fa0dd9` |
| `../qfli_studio_core/lib/services/studio_profile.dart` | `0368fe6860309229369814dedd656ec370f47d2db7f6f3d9e0141cd5cda9c81c` |
| `../qfli_studio_core/lib/workspace/saved_workspace.dart` | `f658b3ddca9dcf8152282304428523836b4b3b93ab95a1d034b43316f3bc5720` |
| `../qfli_studio_core/lib/pages/home_page.dart` | `84cdfc0f3e6fd16c001e2200b45447a470fe66e7eff363bbb54773f02085be3c` |
| `../qfli_studio_core/lib/editor/file_explorer.dart` | `57e662d534e721284dc41b7f90374d117e6d392925d09703c6998928beadae5c` |
| `../qfli_studio_core/lib/editor/editor_page.dart` | `487267b43bd2e80c60f412b74cf89fd8d9c3de349bd8e5943993249c99a6547e` |
| `../qfli_studio_core/lib/editor/project_history.dart` | `d90e00a4a0ed7f92729dc1d19aac4331ed035ca881afc6924ce669aac3337eba` |
| `../qfli_studio_core/lib/editor/retained_editor_host.dart` | `af9f514af1cd1ec7d94bbd2378cfc3029960ae7eaab0826761475ab01676fc77` |
| `../qfli_studio_core/lib/workspace/workspace_store.dart` | `1c1cd747f3b3c66b92399aa92a6f61703774a6e1754423ca61acf222a9fecf8d` |
| `../qfli_studio_core/lib/workspace/workspace_dialogs.dart` | `a947571b26fb23f513221e2955a5e81123beb0931d4031cd2ce2c3c424c00481` |
| `../qfli_studio_core/lib/workspace/saved_workspaces_tab.dart` | `d63e6e55d4cfadf4982ff841a2c3835d6d7ee727d966682a5a1914494b4536a5` |

## Host slot remains released

Read-only audit of global `qfli-core-release-sync` recovered the exact existing
release at seq287, timestamp `2026-10-23T02:35:25.396Z`:

- Final SDK nested-cancel/scoped-analysis handle **70405**, shell PID **64664**,
  **EXIT0**, **1/1 PASS**, analysis **No issues**.
- Earlier SDK late-output handle **21711**, **EXIT0**, **1/1 PASS**.
- Native handle **85731**, **EXIT1**, retained failure evidence.
- Go236 explicitly released to **Rust205, then C211**, with no live Go handle
  and no further command until a later explicit grant.

Global seq402 (`2026-10-23T22:33:27.434Z`) reaffirmed that Go236 remains
released and source-only work holds no reservation. This worker recovered and
reported those records to the parent; no new test handle, kill/reset or device
action was created to answer the release request.

## Same-ID regression addendum, 2026-10-24

This continuation changes only `test/go_saved_workspaces_test.dart` and this
addendum. The previous eight active cases are preserved. Three additional active
cases use the actual `goProfile`, public controllers/stores and real editor,
explorer, retained host and management dialogs:

1. `Go retained attachWorkspace replaces same-ID rename and keeps live state`
   saves a real external rename, attaches its same-ID document with unchanged
   members, and checks the mounted title, settings name and retained restore
   label. The retained key, page/explorer/controller and open-file identities
   must survive.
2. `Go same-key same-ID refresh updates name members and primary in place`
   saves new metadata, reverses the two existing members and changes primary,
   then updates the same keyed mounted page. It checks the new title, ordered
   roots, settings name and mandatory primary checkbox alongside live identity.
3. `Go editor same-ID rename reaches retained owner and restore label`
   physically saves through the explorer settings dialog and checks disk name,
   retained metadata/key, mounted title, restored label and the next settings
   dialog.

All three assert preservation of the dirty secondary buffer, its changed cursor,
the clean primary buffer/cursor, both open-file objects and the live nested tree
expansion. The nested directory is expanded after initial session restoration,
so reloading that initial view snapshot would lose visible `nested.go`. Fixture
source bytes remain unchanged and autosave remains disabled. These are now
eleven active, unexecuted cases: ten `testWidgets` declarations, one of which
registers both missing-primary and missing-secondary variants. There are no
skip arguments.

### Current shared gates and audit provenance

Fresh source reads found that C/main had already repaired the four propagation
gates before this continuation's final dependency capture:

- `RetainedEditorController.attachWorkspace` skips only an identical workspace
  object with identical ordered member paths; a renamed same-ID object replaces
  the retained metadata and notifies listeners.
- `EditorPage.didUpdateWidget` refreshes the same-ID metadata reference without
  applying an old session snapshot; member reconciliation remains separate.
- `FileExplorer.didUpdateWidget` refreshes rename-only saved metadata without
  rebuilding its tree. Changed member/primary paths capture live expansion
  before rebuilding the root view.
- `EditorPage._onWorkspaceChanged` calls `onWorkspaceSaved` whenever a saved
  workspace is present, including a same-ID edit.

The source-based expectation is therefore that these new regressions exercise
the repaired paths. No current source-derived red gate, executed reproduction
or runtime pass is claimed.

The earlier `same-id-workspace-propagation-source-audit-20261024.md` is
non-atomic: its defect prose describes earlier gates, while its hash table was
captured after C/main's repairs. Its editor/page/retained hashes equal the
repaired dependencies below and must not be cited as hashes proving the old
defects. The first handoff table in this document retains historical leads:
test `1199ee3628f42bd14131aff4e9d8ae99066efbcdab3478f523cbc4ded581dc1b`,
page `487267b43bd2e80c60f412b74cf89fd8d9c3de349bd8e5943993249c99a6547e`,
explorer `57e662d534e721284dc41b7f90374d117e6d392925d09703c6998928beadae5c`,
and retained host
`af9f514af1cd1ec7d94bbd2378cfc3029960ae7eaab0826761475ab01676fc77`.
Those are historical snapshot leads, not an isolated before/after patch proof.

The current shared saved-workspace/offline-workspace specs now document the
standalone capability and same-ID propagation contract. This supersedes the
earlier main-only documentation observation above; this worker edited neither
shared source nor shared specs.

`WorkspaceStore.saveSession` already reads current disk metadata inside its
serialized transaction and changes only the session field. No stale-session
metadata rollback defect is asserted. In the second new case, the saved result
is copied with the initial session solely as incoming widget data, deliberately
checking that metadata refresh does not reset live expansion. That copied
snapshot is never written to the store. Existing store transaction regressions
remain the coverage leads for stale writers and field ownership.

### Addendum source snapshot and validation

| File, relative to Go repository | SHA-256 |
| --- | --- |
| `test/go_saved_workspaces_test.dart` | `8bc09493a32ccd864320ad4617e2f1ca41388a7a2a9da706072914cd7f756345` |
| `test/go_offline_profile_test.dart` (unchanged in this continuation) | `408c82044ebd373184646d8f42ac0b5bab7f48c520c44552dcc9fe14aad987ec` |
| `../qfli_studio_core/lib/editor/editor_page.dart` | `8549c7e4d00692c27876636d436811100a231d04cb842f263d50eaaab7c07ca4` |
| `../qfli_studio_core/lib/editor/file_explorer.dart` | `6b99ad68a789e2a20d4f49f54ccbf9fa193e9eca852e34a8976bf0b13353a661` |
| `../qfli_studio_core/lib/editor/retained_editor_host.dart` | `58d91921b177173842222f1d2aecb1261f73633abe3a8fefeb4ae33f27e8ba78` |
| `../qfli_studio_core/lib/workspace/workspace_store.dart` | `1c1cd747f3b3c66b92399aa92a6f61703774a6e1754423ca61acf222a9fecf8d` |
| `../qfli_studio_core/lib/workspace/workspace_dialogs.dart` | `a947571b26fb23f513221e2955a5e81123beb0931d4031cd2ce2c3c424c00481` |
| `../qfli_studio_core/lib/editor/retained_editor_restore_control.dart` | `071f76e9931caa33f1641b867d9b10a0783b06b6865fbc85d0a3e3d703e87aae` |
| `../qfli_studio_core/.trellis/spec/frontend/saved-workspaces.md` | `4595cba6f1d7190003185bb1960c27fb362e0ee9b6fed8f6f838d50b166b700c` |
| `../qfli_studio_core/.trellis/spec/frontend/offline-workspace.md` | `47a27c88229e62472ad4e6b272b3d110d94d87aa0a4039f1d23e895730fd373a` |

Only source inspection and lightweight Python whitespace/hash checks were used.
The final read found no trailing whitespace in the two tests or this report and
confirmed the addendum's dependency hashes. Formatting, compilation, analysis
and execution of all eleven cases remain pending a later explicit named grant.
Recompute dependencies before that run because the shared worktree remains
concurrently owned and unfrozen. Source work holds no host reservation and
creates no new runtime/process evidence; the earlier release remains in force.
