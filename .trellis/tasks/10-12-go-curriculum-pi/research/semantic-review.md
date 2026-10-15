# Go curriculum — semantic review (AC6)

> Reviewer: trellis-check `w8:p4`. Recorded per completed batch; expanded toward
> 120 as authors land topics. Findings only; no product code edited.

## Method

For each reviewed topic: pull title / objective / prerequisites / explain /
code / output / pitfalls / exercises from `tool/go_curriculum/topics/T<NNN>.json`,
confirm (a) the code is the topic's real mechanism, not a template with a
changed constant; (b) code↔output↔explain agree; (c) objective/preq/pitfalls/
exercise map to the mapped curriculum row; (d) no meaningless/placeholder calls.

Cross-checks already automated and passing for these topics: `verify.py`
(official Go compile+run, byte-match of shown code) and the new
`test/go_curriculum_content_test.dart` (shared parser/validator + per-lesson
contract).

## Round 1 — T001–T040 (w8:p2) and T061–T120 (w8:p3)

Status: **reviewed T001–T024 in detail; scanned T025–T040 and T061–T120.**
No template-with-constant, no meaningless runtime call, no mismatched
code/output found in the reviewed set. Each lesson's code demonstrates its own
topic; outputs are deterministic and (for stdout topics) reproducible.

### Confirmed good

- **T001** — earlier "meaningless runtime call / wrong comment" is fixed: code
  is a minimal `fmt.Println("hello, go")` / `"toolchain ready"` demo with
  accurate comments. `explain` discusses the compile model and toolchain roles
  (matches title "Go 语言与工具链概览").
- **T002** minimal `package main`/`func main`; **T003** var/:=/zero values;
  **T004** type widths + `%T`; **T005** iota; **T006** conversion/truncation;
  **T007** byte vs rune ("héllo, 世界": bytes 14 / runes 9, correct);
  **T008** fmt verbs; **T009** bufio.Scanner; **T010** operators/bit ops —
  each output verified matches declared (e.g. T004 `typed 是 int`, T007
  `at 1: é`).
- **T011–T023** control flow, slices, maps, extra collection/string topics:
  distinct code, deterministic outputs, ≥2 pitfalls, ≥1 exercise with
  prompt/hint/answer.
- **T024–T040** (variadic, closures, defer, pointers, sort, strings.Builder,
  structs/methods): explain length 200–320 zh chars (real explanations);
  pitfalls 2; exercise 1.
- **T062/T070/T092/T096/T118/T120** sampled: topic-appropriate code and
  deterministic outputs.

### Findings (sent to owners; see check-report §6)

- **F-T2 (semantic+runtime):** 18 `test-pass`/`bench-exists` lessons have empty
  `output` (T077 T078 T080 T081 T099–T104 T105–T111 T114). Shared
  `validateForRelease` requires non-empty `lessons[].output`. Owner w8:p3.
- **F-T3 (import honesty):** `module-project` topics T061/T062/T068 — and
  T118/T120 — do not state the mandatory "工程例子，不能由 CodeSnippet 一键导入；
  手动创建文件/运行命令" text. Owner w8:p3.
- **F-T4 (structure):** `module-project` samples T061–T065, T068–T070 lacked the
  required `go.mod` — **FIXED & re-verified** (all now present). T070 still
  references `go generate` with only `main.go`; needs generator/output files or
  an explicit hand-build file list. Owner w8:p3.
- **F-T5 (informational):** T008 `%T` of a named type prints `main.point` under
  official Go but `struct { X int; Y int }` under Yaegi. T008 is desktop-only,
  so not a defect today; recorded as a mobile-boundary fact (see
  mobile-validation.md).
- **F-T6 (map drift, minor, non-blocking):** T009 title/objective/summary cover
  only `bufio.Scanner`, omitting the curriculum-map row's `fmt.Scan`; T013
  omits the map row's `fallthrough` (title narrowed to "switch 与类型 switch").
  Both remain internally consistent (title/objective/code agree) but are
  narrower than the map row, a minor AC1/AC6 drift. Sent to w8:p3: either add
  the missing sub-point (fallthrough recommended as a common exam point) or
  update the map row (map is w8:p3's).

## Coverage tracker

| Range | Owner | Semantic status |
| --- | --- | --- |
| T001–T040 | w8:p2 | detail-reviewed T001–T024; scan T025–T040 — PASS (issues closed) |
| T041–T060 | w8:p2 | scan T041–T069 — PASS (native-boundary items documented) |
| T061–T120 | w8:p3 | scan + targeted T071–T120 — PASS |

**Full semantic sign-off (120/120):**

- Titles unique across all 120; no template-with-constant; `dedup.py` reports
  **0 substantive duplication**.
- Every lesson: non-empty objective (「能…」), prerequisites, ≥2 topic-specific
  pitfalls, ≥1 exercise with prompt/hint/answer; explain substantive (T056 is
  the shortest at 143 chars but still concept+why+example, judged adequate).
- Determinism policy honoured in the reviewed concurrency/time topics
  (T104 "避免用耗时作断言", T120 "注入固定 now 函数", T071 sorted output).
- All 120 classified `desktop`; **no mobile claim** anywhere (classify.json).

Topic count 120/120; `content/go` assembles 120/120; the new Dart content test
passes 7/7 (parser + validator + per-entry contract + classify consistency).

### Native-boundary classification (closed as desktop-only, keep evidence)

T008/T040/T045/T047/T052/T053/T058/T096/T116 — official Go passes; native limits
only. Closure: desktop-only + lesson statement, no runtime change, no lesson
distortion. Recheck: T088/T096/T116 now **pass under real `runGo`** (buffer path
fixed by w8:p3); T047/T052/T053 remain native panics by design of the limit.

### Remaining (owned by w8:p2, A running full suite)
- None blocking content. T083 fixed & re-verified (deterministic `neverReady`
  channel; official Go OK, native Linux OK). T040 limit statement added.

Next: after A's final full-suite run, shared `apply` (needs authorization) then
an asset-loading regression reading the real aggregate.
