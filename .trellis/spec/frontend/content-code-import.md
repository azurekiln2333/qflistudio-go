# Learning Content and Code Import

Execution policy: apply `AGENTS.md` and [Cloud-Only Execution](../backend/cloud-only-execution.md).
Run all development verification, generators and dependency setup in GitHub-hosted
Actions only. The canonical target sibling is `../qflistudio-core`; historical
`../qfli_studio_core` references describe the previous layout. Do not edit or
inspect another product without the coordinator's ownership assignment.

> Go learning content authoring/verification and its Go-only shared-slice
> integration are specified in
> [`../backend/go-curriculum-tooling.md`](../backend/go-curriculum-tooling.md).
> This file keeps the content-model, localization, and import/entry contract; it
> does not repeat the tooling rules.

## 1. Scope / Trigger

Offline learning pages live in the sibling `../qfli_studio_core` package. Changes
to tutorial or example actions span content models, filesystem writes, project
registration, entry metadata, and editor navigation. Read the actual sibling
worktree before modifying these paths; multiple apps consume this shared code.

## 2. Signatures

```dart
typedef CodeImportResult = ({Project project, String path});

CodeImportService.suggestedFileName(String type);
CodeImportService.isValidFileName(String fileName);
CodeImportService.openInEditor(
  example: example, fileName: fileName, location: optionalStorage,
);
CodeImportService.importIntoProject(
  project: project, example: example, fileName: fileName, overwrite: false,
);
store.createProjectFromExample(
  name: name, example: example, fileName: fileName, location: optionalRoot,
);
```

The service returns the actual project and absolute imported path. ProjectStore
creation returns `ProjectResult` with nullable `error` and `project`.

## 3. Contracts

- Outer pages use MD3 `ListTile` titles and bounded summaries; no code surfaces.
- Lesson and example details use `CodeSnippet`. Copy and import read the current
  example controller text when the code is editable.
- Both offline tabs receive the live store, auth, and settings from `HomePage`.
- Filenames are exact, include their extension, and are editable in the dialog.
- Editor import creates a saved independent workspace; the dialog registers it
  with `addExisting` so it remains accessible from the project list.
- Existing-project import targets its template source directory and keeps the
  current project metadata. Overwrite requires a separate confirmation.
- New-project import replaces the template entry and writes its relative path to
  `.qfli/project.json` as `entryFile`; it must not leave a second Go main function.
- `RunnerService.findEntry` recognizes a valid contained `entryFile` before the
  legacy filename candidates.
- Navigation passes the exact imported path as `EditorPage.initialOpenPath`.
  Restoring older tabs must then select this explicit path.
- Before navigation, call `store.setBrowsedProject(imported.project)`. Otherwise,
  the editor file explorer may show a different remembered project.
- UI strings use `StudioLocalizations` in zh-CN, zh-TW, and English. Use the
  dedicated `codeImportFailed(reason)` message for import I/O failures.

## 4. Validation & Error Matrix

| Input / State | Result |
| --- | --- |
| Empty, nested path, control character, reserved name, trailing dot | `invalidFileName`; no writes |
| Existing regular file, overwrite false | `fileExists`; original preserved |
| Existing directory or symlink at destination | `fileExists` |
| Cloud / missing project, or resolved parent outside project | `projectUnavailable` |
| Missing writable application storage | `storageUnavailable` |
| Overwrite dialog cancelled | Remain in import form; original preserved |
| Import dialog cancelled | No file or project creation |
| Filesystem I/O failure | Localized error in dialog; allow correction or retry |

New filenames are reserved with `File.create(exclusive: true)` before writing.
Do not infer permission to overwrite from a filename collision.

## 5. Good / Base / Bad Cases

- Good: import edited Go code as `lesson.go` into a new project, then reopen it
  from the persisted registry with that file selected and recognized as entry.
- Base: import into an existing project under a new filename; preserve original
  files and tabs, and open the imported file in that project's editor.
- Bad: write custom code next to the unchanged generated `src/main.go`, or select
  a previous active tab after the user explicitly requested an imported path.

## 6. Tests Required

`test/content_code_import_test.dart` exercises the real shared package from the
Go app with temporary filesystem roots and the actual editor widget.

- Assert no code/copy controls in both lists, and both commands in details.
- Assert exact edited code bytes, custom names, project reload, and entry lookup.
- Assert invalid names and cancellations create no files/projects.
- Assert declined replacement preserves bytes; accepted replacement opens the
  occupied file containing the current displayed code.
- Restore a saved active file and a different remembered explorer project; assert
  the imported path is active and the target project's tree is shown.
- Inspect rendered phone, desktop, dark mode, and large-text list/detail/dialog
  screenshots. Assert commands stay within bounds and screenshots are nonblank.

## 7. Wrong vs Correct

An editor constructor alone does not select the file explorer root.

```dart
// Wrong: the explorer can restore an unrelated previously browsed project.
Navigator.of(context).push(MaterialPageRoute(
  builder: (_) => EditorPage(initialOpenPath: result.path, /* dependencies */),
));

// Correct: synchronize the destination and pass the exact imported file.
store.setBrowsedProject(result.project);
Navigator.of(context).push(MaterialPageRoute(
  builder: (_) => EditorPage(
    project: result.project,
    initialOpenPath: result.path,
    store: store,
    auth: auth,
    settings: settings,
  ),
));
```

## Widget Test Scheduling

Project navigation queues registry writes from the widget test's fake clock.
When testing a subsequent `store.refresh()`, start its future and continue
pumping the fake clock while `runAsync` gives filesystem and isolate callbacks
real time. Await the refresh after completion is observed. Directly awaiting
`tester.runAsync(store.refresh)` can stall earlier queued writes and cascade
into reentrant runAsync failures after the test times out.

`_refreshProjects` in `test/content_code_import_test.dart` applies this wait to
both the new-project and independent-editor reopen regressions.
