# Exact non-Java import filename regression

## Scope and baseline

Coordinator dispatched `shared_offline_followup` for the Go full-suite failure
reported in `test/content_code_import_test.dart` for ` padded.go`.

- Verified shared repository location/root: `D:/MyNewProjects/qfli_studio_core`.
- Owned service and shared import/Java test paths were clean before this change.
- Read parent context manifest, PRD, design and execution plan, plus
  `.trellis/spec/frontend/content-code-import.md` and existing shared import
  tests/history. History showed the faulty normalization was already present in
  checkpoint `b75f656`.
- Write scope: shared `lib/services/code_import_service.dart`, shared
  `test/content_code_import_test.dart`, and this evidence file. No tools grid,
  editor host, assets, platform code or sibling product source changed.

## Cause and minimal correction

`CodeImportService.isValidFileName` deliberately rejects leading/trailing
whitespace. `resolveImport` nevertheless trimmed raw names before validating and
returning them for non-Java examples. Consequently `openInEditor` and
`importIntoProject` could accept a name rejected by the validator and silently
write a different file. `ProjectStore.createProjectFromExample` already validated
the original name, so APIs disagreed.

The non-Java branch now validates and returns `rawName` exactly (two changed
lines). Java still uses its existing pasted class-name/path/`.java` normalization
and source renaming without modification.

The UI's `_fileName.text.trim()` calls were also inspected: `CodeSnippet`
validates the raw non-Java field first via `isValidFileName`, so they do not bypass
the rejection in the reachable form flow. No UI change is needed for this bug.

## Regression coverage

Expanded shared real-filesystem invalid-name regression to cover:

- leading/trailing ordinary spaces, tab/newline, leading NBSP and trailing
  ideographic space;
- raw `resolveImport`, independent editor import, existing project import and
  new project import;
- no files, directories or registry projects after rejected requests.

Added a positive filesystem regression proving `Mixed Case Entry.dart` keeps
case, interior spaces, extension and source bytes in both editor and existing
project imports.

Before editing the service, the expanded regression failed (exit 1) with
`resolveImport` returning `padded.dart` for raw ` padded.dart`. This establishes
the test catches the actual bug.

## Validation

All commands ran from `D:/MyNewProjects/qfli_go` using
`D:/ProgramFiles/flutter_ohos/bin/flutter.bat` and `--no-pub`.

```text
flutter test --no-pub --concurrency 1 \
  ../qfli_studio_core/test/content_code_import_test.dart \
  ../qfli_studio_core/test/java_import_rename_test.dart \
  ../qfli_studio_core/test/java_import_overwrite_test.dart \
  test/content_code_import_test.dart
=> 75 passed, exit 0 (37 shared content imports, 17 Java rename,
   4 Java overwrite, 17 Go content imports)

flutter analyze --no-pub \
  ../qfli_studio_core/lib/services/code_import_service.dart \
  ../qfli_studio_core/test/content_code_import_test.dart
=> No issues found, exit 0

git diff --check -- lib/services/code_import_service.dart \
  test/content_code_import_test.dart
=> exit 0
```

The existing Go rendering tests generated their normal screenshots under
`.artifacts/content-import`; these are test evidence, not product assets.
No full suite, package resolution, builds, device commands, staging or commits
were performed. Main owns final review/integration and release verification.

Suggested scoped commit: `fix(import): validate exact non-Java filenames`.
