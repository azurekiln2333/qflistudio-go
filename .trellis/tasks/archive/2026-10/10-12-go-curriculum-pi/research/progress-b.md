# Progress — w8:p3 (T061–T120)

## Overnight autonomous pass — summary

- **Deep read of 120 tutorials + 120 examples** (5 batches, see
  `handoff-overnight-p3-p4.md`). Real defects found & fixed:
  - T061–T065/T068 `sampleFiles` drifted from disk (missing `go.mod`); generator
    now derives the list from the directory.
  - T059/T060/T061 missing the standard 工程例子 declaration; added.
  - T069 explain falsely claimed GOOS/GOARCH printing; corrected.
  - T113 claimed a `pprof_test.go` that did not exist; added a real benchmark.
  - T040 duplicated platform note (pitfall + explain); removed duplicate.
  - T083 expected output stale after A's sample change; synced (this was the
    only full-sweep FAIL).
  - curriculum-map T009/T013 narrowed to match delivered content.
- **Full re-verify: 120 passed / 0 failed**; assemble 120/120; dedup clean;
  patch emit 120/120; dry-run non-Go kept=1520, Go 100→120 (no write).
- **Learning aids added:** `tool/go_curriculum/GUIDE.md` (roadmap, chapter index,
  how-to-run per delivery form, common-error diagnostics, desktop/mobile limits).
  README + spec index link it.
- Temp work confined to `.artifacts/go-curriculum/`; shared files untouched
  (sha 4822ae…/aadb0a…); no commit/push; no external write.

## Real asset load/import verification — HONEST state (apply NOT run)

- `test/go_curriculum_content_test.dart` (8 tests) run now: **7 pass / 1 fail**.
  - **Pass:** durable slice parse via real `ContentCatalog.fromJson`; per-entry
    release contract; example single-file shape; shared validator (Go, min 120);
    120/120 count on the authored slice; classify runtime/importKind consistency;
    code round-trip.
  - **Fail (expected, blocks nothing yet):** “application asset bundle loads the
    exact 120/120 Go slice” → `Expected: 120  Actual: 100`, because the shared
    `assets/content/*` still holds the 100 old placeholder Go entries. This test
    will pass only after the authorized `apply`.
- `flutter analyze test/go_curriculum_content_test.dart` → No issues found.
- I did **not** run the shared `apply`; external-dir write needs separate
  authorization. The prereq evidence (read-only dry-run + review Pi's in-workspace
  apply/rollback rehearsal) is green; the exact command is in README/spec.

## Invalid-filename contract drift (recorded, not masked)

`test/content_code_import_test.dart` → 16 pass / 1 fail (`' padded.go'`), a
pre-existing divergence between the older qfli_go test copy and the shared
`CodeImportService` trim-before-validate behavior. Canonical shared suite is
36/36 green. See `research/import-baseline.md`. Not weakened; not caused by this
task; not blocking the Go slice.

## patch.py ownership takeover (w8:p3) — verified

- A stopped (context/500). patch.py/README/spec maintenance transferred to w8:p3;
  no concurrent writer. Main-controller then hardened patch.py (CreateFileW).
- `DEFAULT_SHARED` resolves to the sibling `../qfli_studio_core/assets/content` (verified).
- `emit` -> 120/120; `dry-run` read-only: non-Go kept=1520, Go 100->120 in both
  files, nothing written.
- Locking/recovery (as implemented): mutation is **Windows-only** via `CreateFileW`
  denying write/delete share (non-cooperating writers refused); non-Windows is
  **fail-closed**. Non-Go raw bytes preserved with **relative block position**
  (not absolute byte offsets). **In-process exception recovery** restores already-
  written targets on failure (not a power-loss transaction; `--backup` covers
  process kill). rollback uses the same exclusivity.
- Audit re-run green: `mobile_check/audit_patch.py` -> DRY-RUN no-write,
  no-confirm refusal, R1 raw-non-Go preservation, R2 unknown-Go rejection,
  R3 lock-conflict refusal, R4 failure recovery; plus non-cooperating-write,
  second-file partial-failure, rollback, non-contiguous-block cases — `PATCH AUDIT OK`.
- README.md + `.trellis/spec/backend/go-curriculum-tooling.md` synced to the above;
  README mobile note corrected (T096/T116 buffered, matrix = research/mobile-validation.md).
  `research/check-report.md` is review Pi's file — not edited.
- Temp trials confined to `.artifacts/go-curriculum/`; real shared files unchanged.
- Shared `apply` still gated on main-controller authorization; not run here.
- Post-apply (not yet run): `flutter test --no-pub --concurrency 1 test/go_curriculum_content_test.dart`
  (+ analyze on that file) to exercise the new real `AssetContentRepository` load test.

Owner: w8:p3 (this pane). Scope (writable): `tool/go_curriculum/topics/T061.json`–`T120.json`,
`tool/go_curriculum/samples/T061/`–`T120/`, and this file. Contract: `tool/go_curriculum/schema.md`.
Shared tooling/aggregation (`assemble.py`/`verify.py`/`dedup.py`/`patch.py`/`content/go/*`),
T001–T060 topics/samples, and all `../qfli_studio_core` files are owned by others and untouched.

## SDK / environment

- Go SDK: `native/build/go-sdk-1.27.1/go/bin/go.exe` → `go1.27.1 windows/amd64`.
- Verification env: `GOMAXPROCS=2`, `GOFLAGS=-p=1`; single-file samples `GO111MODULE=off`;
  test/module samples run from inside their dir (module mode).
- `-race` cannot run here: no C toolchain (CGO/gcc absent). Recorded honestly; `go test -race`
  is a documented desktop command, not an executed gate in this environment.

## Deliverables (all 60 complete)

- 60 samples under `tool/go_curriculum/samples/T061..T120/`.
- 60 topic JSONs under `tool/go_curriculum/topics/T061..T120.json`, generated by
  `research/gen_topics_b.py` + `research/data_b2..b7.py` (owner-owned helpers).

## Verification evidence (executed with pinned SDK)

Final sweep: **60/60 pass, 0 failures** (42 single-file `go run`, 18 test/bench `go test`).
Representative captured outputs (stdout-exact topics):

- T061 exported/unexported + internal note; T062–T065 generics Min/Max/Sum/Stack/interface-vs-generic;
  T066 dependency injection (下午好/上午好); T067 functional options; T068 MVS selects v1.5.3;
  T069 GOOS/GOARCH + `-tags special`; T070 Stringer-equivalent enum.
- T071 sorted worker output; T072 handoff; T073 buffer cap=2; T074 close+range sum 15;
  T075 select ready/timeout/one-of; T076 directional channels sum 14; T079 Once init count 1;
  T082 context cancel + child propagation; T083 timeout/canceled; T084 worker pool error 13 + sorted squares.
- T085 io.Copy + custom reader (fixed value→pointer receiver OOM bug found by real run);
  T086 file IO; T087 bufio lines=3 words=9; T088 sorted dir; T089 JSON round-trip;
  T090 tag/omitempty/`-`; T091 json.Decoder stream + strict; T092 fixed-time formatting;
  T093 Timer/Ticker counts; T094 regex submatch; T095 replace/split; T096 template; T097 strconv;
  T098 SHA-256 known vector "abc".
- T112 escape-analysis demo; T113 pprof hotspot hot(1000)=2997; T115 gofmt/vet-clean;
  T116 slog structured logs (time stripped for determinism); T117 config precedence 3 combos;
  T118 todo CLI+JSON reload; T119 parallel==serial + sorted freq; T120 miniapi routes.
- Test/bench topics all `ok`: T077 mutex, T078 RWMutex, T080 pool (+bench runs), T081 atomic,
  T099–T104 httptest HTTP, T105 table, T106 helper, T107 fixture, T108 bench, T109 cover,
  T110 fuzz (seeds; `-fuzz` also run for 5s earlier), T111 stub, T114 alloc patterns.

Extra executed evidence:
- T080 bench: `BenchmarkRenderPool 37.14 ns/op 16 B/op 1 allocs/op` vs
  `BenchmarkRenderNoPool 48.66 ns/op 80 B/op 2 allocs/op` (reported, not a gate).
- T108 bench: `BenchmarkSum 149.1 ns/op` / `BenchmarkSumParallel 24.58 ns/op`.
- T110 fuzz: `go test -fuzz FuzzParsePort -fuzztime 5s` → PASS, 569412 execs.
- T114 bench: `BenchmarkAppendNoPrealloc 8 allocs/op` vs `BenchmarkAppendPrealloc 0 allocs/op`.

## Structural validation

- 60/60 topic files parse as JSON; `id` matches filename; `tutorial.code` byte-identical to
  its representative sample file; `example.code == tutorial.code`; for `stdout-exact`,
  `tutorial.output == verification.expected`. 0 violations.

## Runtime/import labels (honest)

- `single-file` (importable single `main.go`): T061, T066, T067, T071–T076, T079, T082–T098,
  T112, T113, T115, T116, T117 (and module-project single-run topics T068–T070).
- `test-package`: T077, T078, T080, T081, T099–T111, T114 (each names go.mod + companion files + command).
- `module-project`: T068, T069, T070, T112, T113, T118, T119, T120.
- Generics (T062–T065): `desktop` only. All other topics `desktop` (no native-runtime run done →
  none promoted to `mobile`).

## Cross-review of T001–T060 (owner: w8:p2) — reported, not edited

Checked T001–T020 JSONs (the slice present at review time). Content quality is high
(real objective/prerequisites/≥2 pitfalls/≥1 exercise with answer, substantive `explain`).
One systematic inconsistency affecting **all 20**:

- `verification.kind == "stdout-exact"` but `verification.expected` ends with a trailing `"\n"`
  while `tutorial.output` omits it. Per `schema.md` rule 4, `stdout-exact` compares **trimmed**
  stdout, so `expected` should equal the untrailed `tutorial.output`. Whether this fails depends
  on `verify.py`'s trimming; flagging for the owner to normalize `expected` (drop trailing `\n`)
  or change `kind` to a normalized variant. Not a substance problem; a contract-consistency one.

## Limitations

- No device/emulator run; no mobile promotion.
- `-race` unexecutable (no CGO toolchain) — documented only.
- Cross-review covered T001–T020 (rest of T001–T060 not yet authored at review time); re-check
  once they exist.
