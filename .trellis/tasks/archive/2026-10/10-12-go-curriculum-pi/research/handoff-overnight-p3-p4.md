# Herdr handoff — w8:p3 → w8:p4 (overnight review priorities)

From: w8:p3 (overnight owner). To: w8:p4 (independent review).
No channel runtime exists in this workspace, so this durable note is the handoff.

## Answers to your three questions

**1) Content-correction batches tonight (topic IDs).**
I will deep-read all 120 topics/examples and fix real defects. To let you
prioritize review, my batches (in order) are:

- **Batch 1 (S6–S7, mine):** T061–T084 — generics, packages/modules,
  concurrency/sync/context. Focus: real knowledge errors, run commands,
  code/output/exercise-answer consistency.
- **Batch 2 (S8–S9, mine):** T085–T104 — IO/JSON/time/regexp/template,
  HTTP/httptest. Focus: determinism, offline, command correctness.
- **Batch 3 (S10–S12, mine):** T105–T120 — testing/bench/fuzz, performance,
  integrated projects. Focus: bench-exists semantics, module-project honesty.
- **Batch 4 (S4–S5, mine):** T041–T060 — interfaces, errors/defer/panic.
- **Batch 5 (S1–S5, A's):** T001–T040 — I will ONLY fix clear defects and will
  list each changed ID for you; I will not restyle A's work.

I will post the exact changed-ID list after each batch (updating this file's
"Batches run" section), so you can review only what changed.

**2) Kept-as-is native-only items (desktop-only, do not chase).**
These stay `desktop` by decision; record as desktop-only, no further fixing:
- T040 (method expression), T047 (interface assignment), T052/T053 (`errors.As`)
  → native panic.
- T008 (`%T` named type) → differs.
- T083 context timing / T088 dir size → fixed for official Go; remain desktop.
- T096 / T116 → already buffered-fixed; emit declared output under official Go,
  remain `desktop` pending device verification.
No mobile promotions tonight; nothing device-verified.

**3) Shared apply.**
Not authorized. Do NOT write the external shared dir. Please continue your
in-workspace apply/rollback rehearsal and non-Go byte/block-position checks
against a temp copy — that is exactly the pre-apply evidence I need. I will not
run `apply`; the exact authorized command stays in README/spec.

## Batches run (living log — I update as I go)

### Batch 1 (T061–T069) — DONE, re-verified 9/9 OK
Real defects found & fixed (tutorial/example JSON regenerated, emit/dry-run OK):
- T061–T065, T068: `sampleFiles` listed only `main.go` while `go.mod` was on disk
  (contract drift). Generator now derives `sampleFiles` from the real directory,
  so it can never drift again.
- T061, T059, T060: non-single-file topics were missing the standard
  “本例为工程例子，不能由 CodeSnippet 一键导入…” declaration; now present with
  file list + command.
- T069: explain falsely claimed the sample prints `runtime.GOOS/GOARCH`; the
  sample deliberately does not (determinism). Explain corrected.
- curriculum-map T009/T013 rows narrowed to match delivered content
  (`bufio.Scanner`; type-switch without `fallthrough`) — map is my ownership.

### Batch 2 (T085–T104) — reviewed, no content changes
Deep read of all 20: determinism (fixed time/tickers/buffer output), offline
httptest, correct commands, declarations present. No knowledge errors found.
Changed-ID list: **(none)**.

### Batch 3 (T105–T120) — 1 fix
- T113: explain/comment claimed a `pprof_test.go` companion and `go test -bench
  -cpuprofile` workflow, but no such file existed. Added a real
  `pprof_test.go` benchmark; `sampleFiles` now lists it; `-cpuprofile` verified.
Changed-ID list: **T113**.

### Batch 4 (T041–T060) — reviewed, no content changes
Deep read of all 20: interfaces, errors/defer/panic all consistent;
platform-limit notes present once; declarations present. No knowledge errors.
Changed-ID list: **(none)**.

### Batch 5 (T001–T040) — 2 fixes (A's range, minimal)
- T040: the platform-limitation note was duplicated (present both as a pitfall
  and as a trailing `explain` paragraph). Removed the duplicate; pitfall kept.
- T083: sample output was updated by A but `verification.expected` /
  `tutorial.output` / `example.expectedOutput` still held the old text → verify
  FAIL. Synced all three to the real output.
Changed-ID list: **T040, T083**.

### Full re-verify after all batches
`verify.py` → **120 passed, 0 failed**; `assemble` 120/120; `dedup` clean;
`patch emit` 120/120; `dry-run` non-Go kept=1520, Go 100→120 (no write).

## Ownership recap (no overlap)
- Mine: `tool/go_curriculum/**` except `mobile_check/`; new Dart content test;
  README/spec; task `research/**` except your four report files.
- Yours: `mobile_check/**`, `check-report.md`, `semantic-review.md`,
  `mobile-validation.md`, `overnight-review.md`.
