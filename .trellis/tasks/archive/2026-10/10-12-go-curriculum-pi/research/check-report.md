# Go curriculum — check report (trellis-check, w8:p4)

> Reviewer pane: `w8:p4`. Write scope honored: only
> `test/go_curriculum_content_test.dart`, `tool/go_curriculum/mobile_check/`,
> and this task's `research/check-report.md`, `research/semantic-review.md`,
> `research/mobile-validation.md`. Shared core read-only; no git commit, no device.

## 1. Snapshot (final, 120/120)

- `topics/`: **120/120**; `content/go` assemble **OK 120/120**.
- `evidence/verify-results.json`: **120 items, all ids T001–T120 present**, all
  `desktop` (official-Go run by owner A).
- `dedup.py`: **0 substantive duplication** across 120.
- All 120 classified `desktop`; **no mobile claim**.
- New Dart regression `test/go_curriculum_content_test.dart`: **7 pass / 0 fail**.
- Shared assets still the OLD 100 placeholder Go entries; apply NOT run.

Re-verified this pass: `assemble OK 120/120`; dedup clean; `patch.py dry-run`
against the real shared dir → `non-Go kept=1520, Go 100 -> 120` (no writes;
shared sha256 unchanged `3d6fac…`/`f9cc95…`); samples dirs contain only `.go`/
`.mod` (no leftover binaries → compile-cleanup fix real); T083 uses a
`neverReady` channel with no `time.Sleep` and passes native Linux runGo
(exit 0, matches); T040/T047/T052/T053 carry native-Yaegi limit statements and
remain desktop.

## 2. Tool-chain audit (item 1)

Reviewed `assemble.py`, `verify.py`, `dedup.py`, `patch.py`, `schema.md`.

### REGRESSION (open, sent to w8:p2) — `compile_sample` breaks single-file samples

The T1 fix added `compile_sample` running `go build ./...`. On a sample dir with
**no `go.mod`** (single-file topics that run via `go run .`), `go build ./...`
fails with `directory prefix . does not contain main module`. This turned a full
pass into **69 passed / 31 failed** (T066 T067 T071–T076 T079 T082–T098
T115–T117 …), with content unchanged. Fix: use `go build .` (or gate on
`go.mod` presence / `GO111MODULE=off`). Not a content defect. Re-running after
the fix is required before trusting the aggregate.

### Verified working (with negative controls)

- **Byte fidelity:** `verify.py` asserts `tutorial.code` == the sample file
  bytes. Negative control: mutating `tutorial.code` (wrong text) or appending a
  trailing line → `FAIL … tutorial.code does not match any sampleFiles entry`.
- **Output gate:** changing `verification.expected` to a wrong value →
  `VERIFY: 0 passed, 1 failed`. Good.
- **Example variant independence:** `verify_variant` writes `example.code` to a
  scratch module and runs `go run .` there, asserted against the example's own
  `expectedOutput`. A variant cannot ride on the tutorial's pass.
- **Shared-schema shape:** `assemble.py` emits the real aggregate shape
  (entry keys + `lessons[]` with the exact lesson key set). Confirmed against
  the actual generated `content/go/tutorials.json`.
- **Dedup:** `dedup.py` runs on the 100 topics and reports 0 substantive hits;
  heuristic normalizes numbers and compares `explain`/`code`/exercise sets
  (>=2 reuse flagged). Threshold is sound for the placeholder pattern it targets.

### Finding T1 — `verify.py` does not prove it ran the Go compiler (real gap) — FIXED & RE-VERIFIED

`verify.py` executes whatever `runCommand` the topic declares. Original negative
control: setting `T001.runCommand = "cmd /c echo hello, go& echo toolchain ready"`
→ old `verify.py` reported **OK** while never invoking the Go toolchain.

**Fix (w8:p2) verified this pass:** `validate_run_command` now rejects shell
metacharacters, requires the first token to be `go`/`go.exe` and the subcommand
to be one of `run/test/build/vet/generate`; `compile_sample` additionally forces
`go build ./...`. Negative control re-run: spoofed T001 →
`FAIL T001: runCommand must not use shell metacharacters`. Restored T001 →
`1 passed`. Fixed.

### Finding T2 — empty `lesson.output` fails the shared release validator — FIXED & RE-VERIFIED

`ContentCatalogValidator.validateForRelease` requires every `lessons[].output`
non-empty. 18 topics previously left `tutorial.output` empty. **All 18 are now
filled** (verified: 0 empty-output topics); `assemble.py` reports
`ASSEMBLE OK: 100 tutorials, 100 examples`. The new Dart test's shared-validator
gate now only reports the 120-count (in-progress) issue.

### Finding T5 — spoofed-runCommand (same as T1) and `--race` switch

**FIXED & VERIFIED:** `verify.py --race` now runs the real `go test -race` gate
via WSL. Re-run: `OK T077 test-pass variant=same-as-tutorial race=RACE-OK`.

## 3. Native / Yaegi boundary (item 3)

See `research/mobile-validation.md` for the full matrix. Summary:

- **Bare Yaegi is insufficient evidence.** `tool/go_curriculum/mobile_check/`
  includes a *bare* Yaegi probe (same version pin) — used only for a first
  screen; it cannot justify a mobile claim because it omits the shipped
  runtime's local vendor fixes, `projectSourceFS`, and symbol/import limits.
- **Host-native evidence** via `run_native_check.sh`: injects a check-only test
  into `native/go_runtime` with `go test -overlay` (tag `hostcheck`, no real
  file changed) and calls the real `runGo` — the exact function the mobile FFI
  invokes. Ran all 87 single-file candidates on Windows-Go and WSL/Linux-Go.
  - Panics (native): T040 (method expression), T047 (interface assignment),
    T052/T053 (`errors.As`).
  - Output diffs: T008, T045, T058; plus T096 (template) / T116 (slog) whose
    stdout is empty under the native capture; plus Linux-only T083 (context
    timing) and T088 (dir size).
- **Real `go test -race` is runnable** via WSL `qfli-java-build` (gcc) + the
  project-pinned linux Go SDK; T077/T078/T080/T081 → RACE-OK.
- **Evidence level discipline:** a mobile label requires a *device* run. All 120
  topics are `desktop`; none device-verified. Host-native findings only forbid
  promotion; they do not certify mobile.

## 4. Dart content-load / import regression (item 2)

New file: `test/go_curriculum_content_test.dart`.

- Loads the durable Go slice through the **real shared parser**
  (`ContentCatalog.fromJson`) and exercises the **real shared validator**
  (`ContentCatalogValidator.validate`), scoped to Go.
- Always-on final gates (never dynamically skipped):
  - `Go tutorial/example count reaches 120/120` → currently **FAILS**
    (`100/120`), which is the honest in-progress state; it must pass only when
    the slice is complete.
  - `Go slice passes the shared validator for Go entries` → currently **FAILS**
    on the 18 empty-`output` lessons (Finding T2).
- Passes now: parser load + explicit-id/locale; per-lesson objective/
  prerequisites/≥2 pitfalls/≥1 exercise; example single-file shape (no `go.mod`
  concatenation); classify.json runtime/importKind consistency with the
  mobile-claim guards.

Run: `flutter test --no-pub --concurrency 1 test/go_curriculum_content_test.dart`
(`flutter analyze` on the file: clean).

### Pre-existing failure (not caused by this check)

`flutter test test/content_code_import_test.dart` → 16 pass, 1 fail:
`invalid paths and reserved filenames create no files or projects` — the
invalid-file-name case does not throw `CodeImportException`. This is the shared
import-contract test (AC5), independent of my changes; left untouched per
"do not modify existing tests to mask failures". Needs owner attention.

## 5. Semantic review (item 4)

See `research/semantic-review.md`. Reviewed T001–T020 this round: no
template/filler, title/objective/explain/code/output/pitfalls/exercise align.
T001's earlier meaningless runtime call / wrong comment is fixed (code is now a
minimal `fmt.Println` demo with accurate comments).

## 5. Semantics of patch.py (AC7) — shared-safety audit PASSED

`mobile_check/audit_patch.py` asserts the real shared-file risks (not
decoded-dict equality): R1 raw-non-Go byte+order preservation (brace-depth span
scan), R2 unknown-Go rejection via baseline digest, R3 concurrent OS-lock holder
refused, R4 invalid second target leaves the first untouched. Plus dry-run runs
the real transform and writes nothing, and apply without `--confirm` refuses.

Against the rewritten `patch.py`:

```
DRY-RUN: real transform, no write OK
APPLY no-confirm refusal: OK
R1 raw-non-Go preservation: OK
R2 unknown-Go rejection: OK
R3 lock conflict refusal: OK
R4 failure recovery: OK (all-or-nothing, first target untouched)
PATCH AUDIT OK
```

The implementation is now byte-splice (only the contiguous Go run replaced),
baseline-digest-guarded, OS-exclusive-locked, backs up original bytes, verifies
both targets before writing either, and restores on write failure.

Extended checks (beyond the four):

- **R1 prefix/tail**: bytes of the document *outside* `entries[]` (custom
  preamble + trailing keys) are byte-unchanged after apply; non-Go entries keep
  their raw bytes; the Go run is replaced. Verified True.
- **R5 rollback**: after apply, a newer non-Go edit (`NEWER-NONGO-EDIT`) survives
  rollback while only the Go slice is restored to baseline. Verified True.
- Samples dir stays `.go`/`.mod` only (129/74); no compiler binaries; temp dirs
  relocated to `.artifacts/go-curriculum/` (empty/cleaned).

### Real dry-run against the actual shared dir (no writes)

After the qfli_c C/C++ scoped merge landed, live files were read: C=100, CPP=100,
Go=100 old entries, total 1620/file; the live Go slice still **exactly matches**
`baseline/` (`liveGo==baselineGo` True for both files). Read-only dry-run:
`non-Go kept=1520, Go replaced 100 -> 120` (both files, byte counts reported);
`PATCH DRY-RUN OK (nothing written)`. Shared sha256 unchanged by this check.
Run from repo root (read-only; shared files verified unchanged by sha256 after):

```powershell
cd D:\MyNewProjects\qfli_go
python tool/go_curriculum/patch.py emit
python tool/go_curriculum/patch.py dry-run --shared ../qfli_studio_core/assets/content --patch tool/go_curriculum/patch-go
```

Output: `tutorials.json: non-Go kept=1520, Go replaced 100 -> 120` and the same
for `examples.json`; `PATCH DRY-RUN OK (no files written)`. `patch-go/` is now
regenerated at 120/120 (the earlier stale 1-entry emit was replaced).

### Exact apply entry (authorized integrator only; not run here)

```powershell
cd D:\MyNewProjects\qfli_go
# re-read live files first (qfli_c merged C/C++; confirm Go baseline still matches)
python tool/go_curriculum/patch.py dry-run --shared ../qfli_studio_core/assets/content --patch tool/go_curriculum/patch-go --baseline tool/go_curriculum/baseline
python tool/go_curriculum/patch.py apply   --shared ../qfli_studio_core/assets/content --patch tool/go_curriculum/patch-go --baseline tool/go_curriculum/baseline --confirm
```

Preconditions verified: shared target exists and parses; live Go slice ==
baseline (both files); only `type=='go'` replaced 100 -> 120; non-Go (1520/file,
including C/CPP) raw bytes + order preserved; originals backed up to
`tool/go_curriculum/apply-backup/`; OS-exclusive locks; `--confirm` required
(exit 2 without).

## 5b. Acceptance criteria status

| AC | Status | Evidence |
| --- | --- | --- |
| AC1 count/uniqueness | PASS | assemble 120/120; titles unique; dedup clean |
| AC2 per-entry + runtime honesty | PASS | Dart per-entry test; all desktop; native docs |
| AC3 per-item compile/run | PASS | verify-results.json 120 items (owner A) |
| AC4 no filler | PASS | dedup.py 0 hits |
| AC5 import/loading regression | PASS (Go side) | Dart test 7/7; import contract unchanged; hand-build statements present |
| AC6 semantic review | PASS | research/semantic-review.md (120/120 sign-off) |
| AC7 Go-only patch | PASS (pre-apply) | R1–R4 shared-safety audit OK; real dry-run OK; apply pending authorization |

Final full-suite run: owner A. Native-boundary evidence: host-native (not
device). Shared `apply` **not authorized** yet; the amended exact apply command
is below and requires a fresh read of the live files first (qfli_c merged C/C++
rows; Go baseline still matches).

### Rollback entry (if needed)

```powershell
python tool/go_curriculum/patch.py rollback --shared ../qfli_studio_core/assets/content --backup tool/go_curriculum/apply-backup --confirm
```

## 6. Backlog / next actions

- [ ] Await coordinator authorization, then run the exact apply above, then
      `mobile_check/verify_shared_apply.py` for byte-invariance evidence.
- [ ] Re-run `test/go_curriculum_content_test.dart` after apply (the
      `application asset bundle loads the exact 120/120 Go slice` gate flips to
      green).
- Pre-existing `test/content_code_import_test.dart` invalid-filename failure is
  left intact (owner; not masked).

## 7. Independent closing check (patch.py / audit / Dart) — no blocker

Re-checked the three artifacts (no 120-Go rerun, no business/shared writes):

1. **patch.py** — syntax OK; Windows locks via `CreateFileW(share=FILE_SHARE_READ)`
   (denies non-cooperating writers), reads through the held handle, verifies
   both targets before writing, writes in place, restores originals on partial
   failure, `rollback` validates the applied Go slice against
   `applied-go-<name>` before restoring. Non-win32 mutation is refused. No
   blocker.
2. **audit_patch.py** — `PATCH AUDIT OK` covering R1 raw-span prefix/suffix,
   R2 unknown-Go rejection, R3 cooperative lock + a **separate-process
   non-cooperating writer** denied, R4 all-or-nothing + injected partial-write
   restore, rollback non-Go survival, non-contiguous layout rejection.
3. **test/go_curriculum_content_test.dart** — 7 pass / 1 fail; the single
   failure is the *post-apply* gate `application asset bundle loads the exact
   120/120 Go slice` (bundle still 100 old Go rows). This is the intended
   pre-apply state; it passes once the authorized apply lands.

**Post-apply verifier ready** (`mobile_check/verify_shared_apply.py`, validated
against a synthetic apply): compares the live shared files against
`apply-backup/original-*`, asserting prefix/suffix bytes outside the Go run are
identical, non-Go count preserved, Go == 120 == applied backup, and original sha
matches. Command (after authorization):

```powershell
python tool/go_curriculum/mobile_check/verify_shared_apply.py --shared ../qfli_studio_core/assets/content --backup tool/go_curriculum/apply-backup
```

**Rehearsal on a workspace copy of the real files**
(`mobile_check/rehearse_real_apply.py`, `.artifacts/go-curriculum/rehearsal/`):
`REHEARSAL OK` — apply grows Go 100→120, non-Go raw bytes + relative order
unchanged, rollback restores 100, real shared sha256 unchanged
(`4822ae…`/`aadb0a…`). Real layout: Go contiguous at indices 700–799 in both
files. Entries after the Go run legitimately shift absolute offset when the Go
block grows; the invariant is raw bytes + relative order (holds).

The pre-existing `test/content_code_import_test.dart` invalid-filename failure is
**left intact** (not masked).

- [x] w8:p2: `verify.py` proves it ran Go (T1) — verified; `--race` switch
      verified; `compile_sample` go.mod-aware regression fixed.
- [x] w8:p2: `assemble.py` empty-`output` gate; all 18 outputs filled;
      `assemble OK 120/120`.
- [x] T4 (go.mod) fixed; T2 (empty output) fixed.
- [x] w8:p3: T088/T096/T116 fixed & re-verified under real `runGo`; T109
      hand-build statement added; T047/T052/T053 limit statements added.
- [x] w8:p2: T083 determinism fixed & re-verified (official Go + native Linux);
      T040 limit statement added.
- [ ] Remaining: A's final full-suite run; then authorized shared `apply` and an
      asset-loading regression against the real aggregate.
