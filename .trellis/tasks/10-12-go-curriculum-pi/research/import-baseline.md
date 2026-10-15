# Import-test baseline investigation — `content_code_import_test.dart` invalid-filename failure

Read-only investigation requested by the user. Scope: determine whether the
`content_code_import_test.dart` invalid-filename failure is (a) old shared-contract
drift, or (b) interference from a newly added test file. No test assertions were
loosened; no shared source or runtime was modified.

## 1. Exact failing case and error

Command (qfli_go copy):

```powershell
flutter test --no-pub --concurrency 1 test/content_code_import_test.dart `
  --plain-name "invalid paths and reserved filenames create no files or projects"
```

Result: **1 failed**, with the first (and only) offending input being the
**leading-space name `' padded.go'`**:

```
Expected: throws <Instance of 'CodeImportException'>
          with `reason`: CodeImportFailure:<CodeImportFailure.invalidFileName>
  Actual: <Instance of 'Future<({String path, Project project})>'>
   Which: emitted ({String path, Project project}):
          <(path: ...\code_snippets\snippet_f63d423f\src\padded.go,
            project: Instance of 'Project')>
  padded.go
  test\content_code_import_test.dart 148:17
```

So `CodeImportService.openInEditor(..., fileName: ' padded.go')` **succeeds** and
writes `src/padded.go` instead of throwing `invalidFileName`.

Full-file run (qfli_go copy): **16 pass, 1 fail** — only this case fails; all
other import cases pass.

## 2. Root cause (shared-service contract behavior)

`../qfli_studio_core/lib/services/code_import_service.dart`:

- `isValidFileName` (line 161–163) **rejects untrimmed names**:
  `fileName == fileName.trim()` is part of the validity predicate.
- But `resolveImport` (line 131) validates the **already-trimmed** value:
  `_validateFileName(rawName.trim())`, and returns
  `(fileName: rawName.trim(), ...)`.
- `openInEditor` (line 250) then re-validates `resolved.fileName`, which is the
  trimmed `padded.go` — valid, so no exception is thrown.

Therefore the shared service **silently normalizes** a leading/trailing-space
filename rather than rejecting it. The test's expectation (reject untrimmed
input at `openInEditor`) does **not** match the shared service's actual behavior.

This is shared-contract behavior that predates and is independent of the Go
curriculum: it lives entirely in `code_import_service.dart`, which this task is
forbidden to modify, and it involves no Go tutorial/example content.

## 3. Evidence that this is NOT introduced by the Go curriculum task

1. **Shared canonical test passes.** The repo's canonical copy
   `../qfli_studio_core/test/content_code_import_test.dart` runs
   **36/36 pass**. Its invalid-basename list (line 349–359) is:
   `'', '.', '..', '../escape.dart', r'..\escape.dart', 'bad:name.dart',
   'bad\u0000.dart', 'NUL.dart', 'entry.dart.'` — it **does not include**
   `' padded.go'`. So the shared suite never exercises the trimmed-name case and
   is green; the failure only appears in the qfli_go copy, which added that case.

2. **The qfli_go copy is old and untracked, and pre-dates the task.**
   - `git ls-files test/content_code_import_test.dart` → empty (untracked).
   - `git log --all -- test/content_code_import_test.dart` → no history.
   - qfli_go file mtime `2026-10-02 01:03:51`; shared copy mtime
     `2026-10-01 05:43:57`; task created `2026-10-12`. The qfli_go copy is not
     a file authored by this task's writers.
   - The two files differ (qfli_go 36323 bytes vs shared 52208 bytes; different
     SHA-256), i.e. the qfli_go copy is a divergent/older variant, not a
     byte-identical import of the shared suite.

3. **Go-content changes cannot cause this.** The failing assertion is about a
   filesystem filename, on a path (`openInEditor`) that never reads Go tutorial
   or example content. The 120-topic data lives under `tool/go_curriculum/` and
   is not applied to shared assets yet.

## 4. Verdict

- **Old shared-contract drift / divergent local test copy — NOT introduced by
  the Go curriculum task.**
- The failure is a mismatch between an *older/divergent* qfli_go copy of the
  test (which asserts rejection of `' padded.go'`) and the shared service's
  documented `trim()`-before-validate behavior.
- The Go curriculum change set (topics, samples, tools, content slice) does not
  touch `code_import_service.dart`, this test's assertions, or the filename
  path; it is not the source of the failure.

## 5. Recommendation (no change made here)

- Per instructions, do **not** loosen the assertion and do **not** modify shared
  source. Options for the owners:
  - If `' padded.go'` must be rejected: that is a shared-service behavior change
    (make `resolveImport` validate the raw, untrimmed name) — outside this task's
    write scope, needs the shared owner.
  - If the intended contract is "trim then validate": the qfli_go test copy's
    `' padded.go'` expectation is the stale part; the copy should be
    re-synced from `../qfli_studio_core/test/content_code_import_test.dart`
    (which is green) rather than edited to weaken a shared assertion.
- This item is **not** a blocker for the Go content slice; it is a pre-existing,
  independent shared-import test divergence.
