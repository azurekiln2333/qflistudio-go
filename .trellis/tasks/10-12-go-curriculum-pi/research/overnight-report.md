# Overnight report — w8:p3 (autonomous night)

Scope: `tool/go_curriculum/**` (except `mobile_check/`), the new Dart content
test, task `research/**`, related spec/README. No external shared write, no
commit/push.

## Completed

1. **Patch/doc wrap-up.** patch.py verified (emit/dry-run); README + spec synced
   to the implemented contract (Windows-only `CreateFileW` mutation, non-Windows
   fail-closed, relative block-position preservation, in-process recovery).
   Review audit `mobile_check/audit_patch.py` → **PATCH AUDIT OK**.
2. **Deep read of 120 tutorials + 120 examples** in 5 batches; real defects fixed:
   - T061–T065, T068: `sampleFiles` drifted from disk (missing `go.mod`).
     Generator now derives `sampleFiles` from the directory (drift-proof).
   - T059, T060, T061: missing the standard 工程例子 declaration; added.
   - T069: explain falsely claimed GOOS/GOARCH printing; corrected.
   - T113: claimed a nonexistent `pprof_test.go`; added a real benchmark.
   - T040: duplicated platform-limitation note; removed the duplicate.
   - T083: stale `expected`/`output` after A's sample change; synced (the only
     full-sweep FAIL).
   - curriculum-map T009/T013 narrowed to match delivered content.
3. **Learning aids:** added `tool/go_curriculum/GUIDE.md` — roadmap (S1–S12),
   chapter index, how to run single-file/test/module samples, common-error
   diagnostics, desktop/mobile limits. Linked from README + spec index.
4. **Full re-verify after changes:** `verify.py` → **120 passed / 0 failed**;
   `assemble` 120/120; `dedup` clean; `patch emit` 120/120; `dry-run` non-Go
   kept=1520, Go 100→120 (no write). `go test -race` (WSL) green for
   T077/T078/T080/T081; benches run.

## Verified (evidence)

- `evidence/verify-results.json` regenerated: 120/120 pass.
- `patch.py dry-run` output: two lines, non-Go kept=1520, Go 100→120.
- `test/go_curriculum_content_test.dart`: **7 pass / 1 fail** (honest) — the fail
  is the real-asset load test asserting 120 vs the shared 100 (apply not run).
  `flutter analyze` on the file: No issues found.
- Race: `go test -race` OK for the four concurrency test topics.

## Not done (with reason)

- **Shared `apply` not executed.** External-directory write needs separate
  authorization; not bypassed. Pre-apply evidence is green (dry-run + review Pi's
  in-workspace apply/rollback rehearsal).
- **Real-asset 120/120 load test cannot pass yet** — depends on the same apply.
  Reported truthfully; not claimed as passing.
- **Mobile promotion:** none. All 120 topics remain `desktop`; no device test.

## Known pre-existing issue (not ours, not masked)

`test/content_code_import_test.dart`: 16 pass / 1 fail (`' padded.go'`). Shared
`CodeImportService` trims before validating while the older qfli_go test copy
expects rejection. Canonical shared suite is 36/36 green. Recorded in
`research/import-baseline.md`; not weakened.

## One next step for the morning

Run the authorized integration once:

```powershell
cd D:\MyNewProjects\qfli_go
python tool/go_curriculum/patch.py emit
python tool/go_curriculum/patch.py apply `
  --shared ../qfli_studio_core/assets/content `
  --patch tool/go_curriculum/patch-go `
  --baseline tool/go_curriculum/baseline `
  --backup tool/go_curriculum/apply-backup --confirm
# then the now-expected-green real-asset test:
flutter test --no-pub --concurrency 1 test/go_curriculum_content_test.dart
```

Rollback if needed:
`python tool/go_curriculum/patch.py rollback --shared ../qfli_studio_core/assets/content --backup tool/go_curriculum/apply-backup --confirm`
