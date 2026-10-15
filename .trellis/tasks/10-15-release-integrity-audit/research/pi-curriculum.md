# Pi w8:p6 — Go curriculum integrity review (parent: 10-15-release-integrity-audit)

Owner: **w8:p6** (Go 教程示例完整性负责人).
Workspace: `D:\MyNewProjects\qfli_go` (verified: `Get-Location` and
`git rev-parse --show-toplevel` both resolve to `D:\MyNewProjects\qfli_go`).
Scope (writable): `tool/go_curriculum/**`, `test/go_curriculum_content_test.dart`,
necessary root Go tutorial/example files. Shared core read-only. No `git add`/
`commit`/`reset`/`checkout`. No app build / device. No shared-aggregate write.

## 0. Verdict

**Go content slice is release-ready (120 tutorials + 120 examples), 120/120
verified. Main controller has since run the exclusive `patch.py apply`: the
shared aggregates now carry the 120/120 Go slice and the Dart asset-load test is
8/8 green.** No placeholder, no template-with-constant, no false desktop/mobile
claim remains. Two follow-up fixes requested by the controller were applied; see
§11.

## 1. What the Go app actually consumes (proof, before any change)

- `pubspec.yaml:13-14` → `qfli_studio_core: {path: ../qfli_studio_core}`.
- `../qfli_studio_core/pubspec.yaml:42-44` declares assets `assets/tutorials/`
  and `assets/content/`.
- `../qfli_studio_core/lib/content/asset_content_repository.dart` loads exactly
  `assets/content/tutorials.json` and `assets/content/examples.json`
  (keys tried: `packages/qfli_studio_core/<asset>` then `<asset>`).
- qfli_go `pubspec.yaml` declares **no** `tutorials.json`/`examples.json` asset.
- Therefore the two real aggregates are
  `../qfli_studio_core/assets/content/{tutorials,examples}.json`.
  The Go app filters `productKey == 'goshift'` → `type:'go'`.

## 2. Root-level `tutorials.json` / `examples.json` — misleading stale decoys

Finding (recorded, **not** modified — outside ownership and unsafe to delete):

- Location: `qfli_go/tutorials.json`, `qfli_go/examples.json`.
- **Untracked, not in `.gitignore`, referenced by no code** (repo-wide grep for
  `tutorials.json`/`examples.json` outside the shared assets and the tool dir
  returns nothing).
- Content: a **10/12 03:13 snapshot** of the shared aggregates — same
  `schemaVersion 1`, `kind`, `updatedAt 2026-10-11`, 1620 entries, but carrying
  the **100-entry Go placeholder** (`go-tutorial-001..100`, single shared
  `explain` body, weighted-sum code with a changed seed).
- Hashes differ from the real shared files
  (root `3D6FAC28…`/`F9CC95CA…` vs shared `4822AE29…`/`AADB0AAE…`).
- Risk: a reviewer could mistake these for the app's content source and validate
  the wrong file. They are **not** consumed.
- Recommendation (owner action, not mine): `git clean` them or add to
  `.gitignore`; do not treat as release content. Deleting untracked user data is
  out of my authorization, so I left them in place.

## 3. Commands run and results (all in this workspace, pinned SDK)

SDK: `native/build/go-sdk-1.27.1/go/bin/go.exe` → `go version go1.27.1 windows/amd64`.

| Step | Command | Result |
| --- | --- | --- |
| assemble | `python tool/go_curriculum/assemble.py` | **ASSEMBLE OK: 120 tutorials, 120 examples from 120 topics** |
| dedup | `python tool/go_curriculum/dedup.py` | **DEDUP OK: no substantive duplication in 120 topics** |
| verify | `python tool/go_curriculum/verify.py --go <abs path to go.exe> --json` | **VERIFY: 120 passed, 0 failed** |
| patch emit | `python tool/go_curriculum/patch.py emit` | **PATCH EMIT OK: 120/120 → patch-go/** |
| patch dry-run | `python tool/go_curriculum/patch.py dry-run --shared ../qfli_studio_core/assets/content` | **OK** tutorials *non-Go kept=1520, Go 100→120*; examples same; **nothing written** (mtime unchanged) |
| Dart test | `flutter test --no-pub --concurrency 1 test/go_curriculum_content_test.dart` | **7 pass / 1 fail** (expected pre-apply; see §6) |
| Dart analyze | `flutter analyze test/go_curriculum_content_test.dart` | **No issues found** |

Note on invocation: `verify.py --go` must be given an **absolute** path. Passing a
relative path makes `run_command` prepend a relative dir to `PATH` while running
with `cwd=<sample dir>`, so the child `cmd.exe` cannot find `go` and every topic
reports `'go' is not recognized`. That first failure was an invocation error, not
a content defect; the absolute-path run is the valid evidence. (Worth hardening
in `verify.py`: resolve `--go` to an absolute path.)

Fresh evidence: `tool/go_curriculum/evidence/verify-results.json` is a 120-element
list (all 120 ids present, unique), `runtime` all `desktop`,
`importKind` {single-file 87, test-package 18, module-project 15},
`verification` {stdout-exact 101, test-pass 15, bench-exists 3, stdout-sorted 1}.

## 4. Semantic review — 12 chapters, 120/120 (AC6)

Method: automated invariant sweep over all 120 `topics/T<NNN>.json`, then a
**manual per-chapter read** of title / objective / concepts / prerequisites /
explain / output / example title+expectedOutput for every topic
(`.artifacts/go-curriculum/chapter-dump.txt`, deterministic, UTF-8).

Automated sweep results (`.artifacts/go-curriculum/semantic_audit.py`):

- missing-field violations: **0** (objective/explain/output non-empty,
  prerequisites ≥1, pitfalls ≥2, exercises ≥1 with prompt/hint/answer).
- duplicate `explain` bodies: **0**; duplicate exercise prompts: **0**.
- unique titles: **120/120**; empty concepts: **0**.
- non-single-file topics: **33**, **all** contain the mandatory
  「工程例子，不能由 CodeSnippet 一键导入；按文件清单手动创建 + 官方命令」
  declaration (machine-checked).
- `mobile` runtime claims: **0** (honest — no device/native verification done).
- license identical to repo convention for all 120; explain length
  min/med/max = 143/242/477 zh chars; levels {beginner 37, intermediate 58,
  advanced 25}.
- example code shape: 0 issues (every example `code` is one valid Go file, never
  `go.mod`/multi-file concatenation). 117 examples share their tutorial's code
  (allowed by R4); 3 are distinct variants each asserted to its own
  `expectedOutput` (T007 `bytes: 14\nrunes: 9`, T024 `6\n0`, T027 `fib(10)=55`).

Chapter walk-through (each lesson teaches its mapped topic; code↔explain↔output
agree):

- **S1 T001–T010** environment/basics — compile model, first program, var/zero
  values, type widths + `%T`, iota, conversion/truncation, byte-vs-rune
  (`héllo, 世界` → bytes 14 / runes 9, correct), fmt verbs, bufio.Scanner,
  operators. PASS.
- **S2 T011–T022** control flow + collections — if-scope, switch (expr/none),
  type switch, for forms, range (+map order note), label, goto single-exit, array
  value semantics, slice len/cap growth, slice aliasing trap, copy/delete/dedup,
  map comma-ok. PASS.
- **S3 T023–T036** functions/pointers/collections — multi/named return, variadic,
  higher-order, closures, memoized fib, defer LIFO, pointers by value vs ref,
  slice header semantics, new/&, sort.Slice, sort.Search, set/group maps,
  strings, Builder. PASS.
- **S4 T037–T048** structs/methods/interfaces — literals, embedding/promotion,
  value vs pointer receivers, method value vs expression, duck typing, type
  assertion (comma-ok vs panic), any/type switch, interface composition,
  Stringer/error, sort.Interface, composition over inheritance, typed-nil trap.
  PASS.
- **S5 T049–T058** errors — error as value, sentinel + `%w`, unwrap chain,
  Is-vs-As, custom error + Unwrap, panic/recover boundary, defer cleanup +
  `errors.Join`, layered context, logging boundary, concurrency-safe error
  collection. PASS.
- **S6 T059–T070** packages/modules/generics — package/init order (手搭),
  go.mod (手搭), internal (手搭), generics Min/Max, union constraints `~int|~float64`,
  generic Stack, generics-vs-interface, DI, functional options, MVS (手搭),
  build tags `-tags special` (手搭), go:generate boundary (手搭). PASS.
- **S7 T071–T084** concurrency — goroutine+WaitGroup (sorted), unbuffered
  handoff, buffered cap + `select/default`, close+range, select timeout,
  directional channels, Mutex (`test-pass`), RWMutex, Once, sync.Pool (bench),
  atomic, context cancel/propagate, WithTimeout/DeadlineExceeded, worker pool +
  standard-library error collection. PASS.
- **S8 T085–T098** stdlib IO/JSON/time/regexp — io.Reader/Writer + custom reader,
  file IO in temp dir, bufio Scanner (lines/words), os.ReadDir (sorted),
  json Marshal/Unmarshal, tags/omitempty/`-`, Decoder stream + strict, fixed-time
  formatting, Timer/Ticker counts, regexp submatch, ReplaceAllStringFunc/Split,
  text/template (buffer-rendered), strconv, SHA-256 known vectors. PASS.
- **S9 T099–T104** net/http (all `test-pass` via httptest, offline) — client GET,
  ServeMux handler, method/header/status 405, JSON API envelope, middleware +
  recover, timeouts + graceful shutdown. PASS.
- **S10 T105–T111** testing (all `test-pass`) — table-driven, t.Helper,
  t.TempDir/t.Cleanup, benchmark + b.RunParallel (`bench-exists`), coverage,
  fuzz target, interface stub. PASS.
- **S11 T112–T117** performance/engineering — escape analysis hint, pprof
  (`hot(1000)=2997`), prealloc/batch (`bench-exists`), vet/gofmt baseline, slog
  (time stripped for determinism), config precedence. PASS.
- **S12 T118–T120** projects — CLI todo + JSON persistence, concurrent word
  count (parallel==serial), minimal HTTP service (routes + httptest). PASS.

Only cross-inconsistency considered and **resolved**: T024 example
`expectedOutput='6\n0'` differs from tutorial `output='6\n15'` because the
example is a distinct variant demonstrating the empty-variadic call `sum()` → 0;
`verify.py` asserts each against its own expected value. Not a defect.

`source` is `https://go.dev/doc/` for all 120 — **by contract** (`schema.md`
fixes this value and the license reads "reference link retained"), not a
placeholder symptom. Left unchanged (changing it would break the authoring
contract for content owned jointly with w8:p2/w8:p3).

## 5. Aggregate contract conformance

`patch-go/go-tutorials.json` (120) entry keys exactly
`id,language,type,locale,level,title,summary,concepts,source,license,updatedAt,lessons[]`;
`lessons[0]` keys exactly
`id,title,summary,concepts,explain,code,output,objective,prerequisites,pitfalls,exercises`.
`patch-go/go-examples.json` (120) keys exactly
`id,language,type,locale,level,title,summary,concepts,source,license,updatedAt,code,expectedOutput,templateType`.
`content/go/*` also 120/120. Manifest = `{goTutorialCount:120, goExampleCount:120}`.

## 6. Dart regression (owned by the review task)

`test/go_curriculum_content_test.dart`: **7 pass / 1 fail**, `flutter analyze`
clean. The single failure is intentional and blocks nothing locally:

- failing test: “application asset bundle loads the exact 120/120 Go slice”
  → `Expected: 120 Actual: 100`, because the shared `assets/content/*` still
  holds the 100 old placeholder Go entries until the authorized `apply`.
- passing: real `ContentCatalog.fromJson` parse; per-entry release contract;
  example single-file shape; shared `ContentCatalogValidator` (Go, min 120);
  120/120 on the authored slice; classify runtime/importKind consistency; code
  round-trip.
- After `apply`, this one test turns green by construction (shared Go slice
  becomes 120/120). Re-run: `flutter test --no-pub --concurrency 1
  test/go_curriculum_content_test.dart`.

## 7. Baseline / apply-readiness (evidence for main controller)

- `patch.py apply` compares the **Go entry slice**, not the whole-file hash:
  `baseline/tutorials.json` (list of 100 Go entries) is **byte-equal** to the
  current shared Go entries (`cur == baseline` → True), same for examples. So
  `apply` will be accepted (no "unknown Go edits").
- Caveat recorded: `baseline/shared-sha256.json` holds **whole-file** hashes
  (`5691531b…`/`38744c5d…`) that no longer match the current shared files
  (`4822ae29…`/`aadboaa…`) — expected, because non-Go bytes were edited after the
  baseline capture; the **Go slice** is unchanged. This file is informational and
  does not gate `apply`. Left as-is (touching it is unnecessary and could confuse
  the controller); flagged here for transparency.
- `dry-run` proved read-only (shared mtime unchanged before/after).
- Emitted reviewable slice: `tool/go_curriculum/patch-go/{go-tutorials,go-examples}.json`
  (120/120) + `manifest.json`.

Exact integration command (main controller, authorized, exclusive `CreateFileW`
locks; Windows-only):

```powershell
python tool/go_curriculum/patch.py apply `
  --shared ../qfli_studio_core/assets/content `
  --patch tool/go_curriculum/patch-go `
  --baseline tool/go_curriculum/baseline `
  --backup tool/go_curriculum/apply-backup --confirm
```

Post-apply (controller): `flutter test --no-pub --concurrency 1
test/go_curriculum_content_test.dart` (expect 8/8).

## 8. Files changed by this pane

**None.** This was a verification/review task; it required no content or tooling
edit. All produced artifacts are local diagnostic/evidence files under
`.artifacts/go-curriculum/` (untracked, non-shipping):

- `.artifacts/go-curriculum/semantic_audit.py`
- `.artifacts/go-curriculum/chapter_dump.py`
- `.artifacts/go-curriculum/chapter-dump.txt`

Re-generated-by-tool files (already part of the tool workflow, not hand-edited):
`tool/go_curriculum/content/go/*`, `content/classify.json`,
`evidence/verify-results.json`, `patch-go/*` (refreshed deterministically by the
commands in §3).

## 9. Remaining items / blockers

- Apply: **done** by the main controller (exclusive step); see §11c.
- `verify.py` relative-`--go` hardening: **done** (§11a).
- Hygiene: stale root `tutorials.json` / `examples.json` decoys **removed** with
  user authorization (§11b).
- Honest limitations: `-race` **is** runnable in this environment (WSL
  `qfli-java-build` provides gcc; project linux SDK) and is now a fail-closed
  gate (§13); `-fuzz` full matrix not run; no device/native run → all 120
  correctly stay `desktop`; `text/template`/`log/slog` mobile capture caveat
  documented in `GUIDE.md` and `research/mobile-validation.md`.

## 10. Human-readable checklist vs task requirements
- [x] Root files checked: real consumers identified; local decoys removed with
      user authorization (§11b).
- [x] 120 tutorials + 120 examples semantic review (automated + per-chapter).
- [x] Complete runnable code: verify compiles + runs every topic; example
      variants asserted individually.
- [x] Explanation/output/exercise consistency: 0 field violations, 0 dup
      explains/exercises, 120 unique titles.
- [x] No placeholder / constant-only variants: dedup clean; manual read confirms
      topic-specific mechanisms.
- [x] Path/import + desktop/mobile labeling honest: 0 mobile claims; 33 non-single
      topics all declare hand-build; GUIDE documents limits.
- [x] assemble / verify(120) / dedup / patch emit / dry-run executed with
      recorded evidence.
- [x] UTF-8 Chinese preserved; no PowerShell-encoding artifact used as evidence
      (PYTHONIOENCODING/Console UTF-8 set for all Chinese dumps).
- [x] Only Go content + tooling touched; no runtime/main.dart/other tests/other
      languages; shared core read-only; no aggregate write; no git mutation.

## 11. Controller follow-up fixes (authorized this round)

### 11a. `verify.py` — resolve `--go` to an absolute path (bug fix)

Defect: passing a **relative** `--go` made every topic fail with
`'go' is not recognized as ...`. `run_command` binds `str(go.parent)` onto `PATH`
while the child runs with `cwd=<sample dir>`; a relative `go.parent` is therefore
an impossible PATH entry. `find_go` now `.resolve()`s the path (existence check
kept). Also hardened: an explicitly supplied-but-missing `--go` now fails loudly
(`VERIFY FAIL: --go SDK not found: ...`) instead of silently falling back to the
default SDK — a typo can no longer run a different toolchain.

File: `tool/go_curriculum/verify.py` (`find_go`).

Evidence:

| Case | Command | Result |
| --- | --- | --- |
| relative `--go`, 2 topics | `verify.py --go native/build/go-sdk-1.27.1/go/bin/go.exe --only T001,T099` | 2 passed / 0 failed, exit 0 |
| `./`-prefixed relative | `verify.py --go ./native/.../go.exe --only T024` | 1 passed / 0 failed, exit 0 |
| default (no `--go`) | `verify.py --only T002,T105` | 2 passed / 0 failed, exit 0 |
| missing explicit `--go` | `verify.py --go does/not/exist/go.exe --only T001` | **VERIFY FAIL: --go SDK not found**, exit 1 |
| **full suite, relative `--go`** | `verify.py --go native/build/go-sdk-1.27.1/go/bin/go.exe` | **VERIFY: 120 passed, 0 failed**, exit 0 |

### 11b. Root placeholder snapshots removed (authorized by user)

Deleted the two exact untracked, unreferenced root snapshots that carried the
100-entry Go placeholder (see §2):

- `D:\MyNewProjects\qfli_go\tutorials.json`  (sha256 `3D6FAC28…`, before delete)
- `D:\MyNewProjects\qfli_go\examples.json`   (sha256 `F9CC95CA…`, before delete)

Method: exact `Remove-Item -LiteralPath` on those two paths only. **No
`git clean`**; both were untracked and are gone (`Test-Path` → False). No other
root or untracked data was removed. `.artifacts/` and all other untracked items
remain.

### 11c. Post-apply state (main controller integrated the shared patch)

The controller ran the exclusive `patch.py apply`. Verified afterwards:

- `../qfli_studio_core/assets/content/tutorials.json` → 1640 entries, **120 Go**
  (`go-tutorial-001..120`); `examples.json` → 1640, **120 Go**
  (`go-example-001..120`). 1640 = 1520 non-Go (preserved) + 120 Go.
- `flutter test --no-pub --concurrency 1 test/go_curriculum_content_test.dart` →
  **8/8 pass** (previously 7/1; the asset-load 120/120 test is now green).
- `verify.py --go <relative>` full suite → **120 passed / 0 failed** after the
  fix.

## 12. Files changed this round

- `tool/go_curriculum/verify.py` — (a) `find_go` resolves to absolute path;
  explicit missing `--go` fails loudly; (b) **`--race` is now a fail-closed
  gate** (see §13).
- `tool/go_curriculum/test_verify_race.py` — **new** regression self-test for the
  race gate (mocked; temp evidence dir).
- `tool/go_curriculum/README.md` — Status/Shared-integration updated: the Go
  slice is now **integrated in `../qfli_studio_core` commit `8731df8`** (shared
  aggregates = 1640 entries each, 1520 non-Go preserved + 120 Go; app asset load
  + shared-parser suite 13 checks pass); no longer claims this round awaits
  authorization. Added the `verify.py --go` note (absolute/relative path,
  fail-loud on missing explicit SDK) and the `--race` fail-closed note. The rule
  that any **future** Go-content/tooling change must still go through a single
  authorized integration step is retained.
- Deleted (user-authorized, exact paths): `tutorials.json`, `examples.json` at the
  qfli_go root.
- `.trellis/tasks/10-15-release-integrity-audit/research/pi-curriculum.md` —
  this report (updated with §11–§13).

No content topics/samples, no Dart test, no shared aggregate, and no other files
were modified. No git staging/commit/reset/checkout.

## 13. `--race` fail-closed fix (independent reviewer finding)

Reported bug (confirmed by an independent reviewer): `main --race` fetched
`run_race_gate(...)` and only wrote a `race` field; a `RACE-FAIL`, a missing
result, or a gate error never landed in `failures`, so `--race` printed
`1 passed, 0 failed` and exited 0 even for a failing/absent race run. The WSL
subprocess return code was also ignored.

Fix (`tool/go_curriculum/verify.py`):

- `run_race_gate` is now **fail-closed**: raises `VerificationError` when the
  gate cannot run (missing script, `OSError`, `TimeoutExpired`) or when the WSL
  process exits non-zero; it never returns a partial dict that could be read as
  "nothing failed".
- `main --race` treats only an exact `RACE-OK` as a pass. `RACE-FAIL`, a missing
  result (`RACE-MISSING`), or a gate error all append to `failures`, set the
  per-topic line to `FAIL`, and force a non-zero exit. No race result is ever
  fabricated.
- `main` gained injection points (`race_gate`, `verify_topic_fn`, `evidence_dir`)
  so the gate can be regression-tested without a real compile or WSL; all
  default to the module globals, so CLI behavior is unchanged.

Regression: `tool/go_curriculum/test_verify_race.py` (unittest, temp evidence
dir). Five tests, **all pass**:

| Test | Injected gate | Expected |
| --- | --- | --- |
| `test_race_ok_passes` | `{T001: RACE-OK}` | rc 0, `1 passed, 0 failed`, evidence `race=RACE-OK` |
| `test_race_fail_fails` | `{T001: RACE-FAIL}` | **rc != 0**, `0 passed, 1 failed`, `race=RACE-FAIL` |
| `test_missing_race_result_fails` | `{}` | **rc != 0**, `race=RACE-MISSING` |
| `test_race_gate_error_fails` | raises `VerificationError` | **rc != 0**, `race=RACE-MISSING`, `raceError` recorded |
| `test_race_flag_absent_is_unaffected` | gate must not be called | rc 0, no `race` field invented |

Against the pre-fix code the middle three would have observed `1 passed, 0
failed` / rc 0 — i.e. the test genuinely catches the bug.

Real evidence this round (WSL + project linux SDK + distro gcc are present in
this environment; the gate is genuine, not stubbed):

- `verify.py --only T077,T078,T081,T119 --race` → **4 passed, 0 failed**, all
  `race=RACE-OK`.
- `verify.py` (non-race, full) → **120 passed, 0 failed** — unchanged by the fix.
- `python -m py_compile verify.py test_verify_race.py` → OK;
  `python -m unittest tool/go_curriculum/test_verify_race.py` → 5/5 OK.

Honesty note: earlier report text said `-race` was unexecutable for lack of a C
toolchain; that is no longer true in this environment (WSL `qfli-java-build` has
`gcc`), so `--race` is now both runnable **and** fail-closed. No race test is
claimed to pass that did not actually run.
