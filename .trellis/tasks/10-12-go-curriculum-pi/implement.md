# Implementation plan — Go curriculum (120 tutorials + 120 examples)

## Preconditions

- User approves the planning summary. C1 (shared write) is a permission boundary
  for the final apply step only and does not block authoring; C2 locale resolved.
- `research/curriculum-map.md` (w8:p3) is complete and reviewed; this plan
  references it for the exact 120-topic list and desktop/mobile classification.
- No `task.py start` before the final review and a subsequent explicit approval.

## Durable layout (C3)

```
qfli_go/tool/go_curriculum/
  content/go/tutorials.json      # 120 Go lessons (source of truth)
  content/go/examples.json       # 120 Go examples
  samples/<topic-id>/            # runnable program or *_test.go per topic
  classify.json                  # topic -> {runtime, importKind}
  assemble.py verify.py dedup.py patch.py README.md
  evidence/                      # per-item verification results
```

## Ordered checklist

1. **Baseline snapshot.** Copy the current shared Go slice into
   `tool/go_curriculum/baseline/` for rollback and non-Go invariance checks.
2. **Scaffold tooling + layout** under `tool/go_curriculum/`.
3. **Author samples first.** For each of the 120 topics from the curriculum map,
   create `samples/<topic-id>/` as a runnable program or test package, offline and
   deterministic, labeled `single-file | test-package | module-project` and
   `desktop | mobile` (generics = desktop-only unless native-verified).
4. **Verify per item (AC3).** `verify.py` compiles and runs every sample with
   `native/build/go-sdk-1.27.1/go/bin/go.exe`. For stdout topics require exact
   match; for concurrent output use a pre-declared sorted/normalized or counted
   assertion; for benchmark topics require the benchmark to run and report
   metrics. Record per-item pass/fail + actual vs expected in `evidence/`.
5. **Write lessons.** For each topic, author `objective`, `prerequisites`,
   concept `explain`, code, `output` (matching step 4), `pitfalls` (≥2), and ≥1
   exercise; state runtime and the exact command for non-single-file topics.
6. **Assemble slice.** `assemble.py` builds `content/go/{tutorials,examples}.json`
   (120/120) satisfying the shared schema and validator field requirements.
7. **Validate.** Run `ContentCatalogValidator.validateForRelease` over the
   assembled catalog (Dart harness in the Go app) and require zero Go issues;
   assert exactly 120/120.
8. **Dedup gate (AC4).** `dedup.py` flags substantive template reuse with a
   primitive whitelist; allows identical trivial `output`s and a lesson sharing
   its own example's code; must report zero substantive hits.
9. **Load/import regression (AC5).**
   `flutter test --no-pub --concurrency 1 test/content_code_import_test.dart`
   and shared `content_repository_test.dart`; confirm the Go app renders the new
   content and the single-file import/`entryFile` contract is unchanged.
10. **Emit patch (AC7).** `patch.py` produces a reviewable Go-only patch plus the
    guarded apply function; applying requires authorization for the precise
    shared files and a single integrator or shared lock.
11. **Semantic review (AC6).** Per-chapter review recorded in the check phase.
12. **Handoff.** Report 120/120 counts, per-item evidence, runtime/import labels,
    residual limitations; no commit without instruction.

## Validation commands

```powershell
$env:GOMAXPROCS="2"; $env:GOFLAGS="-p=1"
# per sample (single-file)
& native\build\go-sdk-1.27.1\go\bin\go.exe run .\tool\go_curriculum\samples\<id>
# test / bench / fuzz
& native\build\go-sdk-1.27.1\go\bin\go.exe test .\tool\go_curriculum\samples\<id>
# native-runtime mobile check (before promoting any topic to mobile)
& native\build\go-sdk-1.27.1\go\bin\go.exe test -mod=vendor .\native\go_runtime

flutter test --no-pub --concurrency 1 test\content_code_import_test.dart
flutter test --no-pub --concurrency 1 ..\qfli_studio_core\test\content_repository_test.dart
flutter analyze --no-pub
```

## Test gates (all mandatory; counts/length never sufficient)

- **Exact count:** 120 Go tutorials and 120 Go examples; topics unique vs
  curriculum-map.
- **Schema:** `validateForRelease` zero Go issues; every lesson has non-empty
  `objective`/`prerequisites`/`pitfalls` and ≥1 distinct exercise.
- **Per-item compile/run:** every tutorial code sample and every example has
  recorded pass/fail with actual vs expected; concurrent/benchmark items use the
  pre-declared deterministic assertion (no silent exemption).
- **Dedup:** zero substantive template reuse (primitive whitelist; trivial
  identical outputs and lesson↔own-example code allowed).
- **Runtime honesty:** every mobile claim backed by a native-runtime run; all
  generics desktop-only unless proven; no test/module topic claims one-click
  mobile import.
- **Load/import:** regression tests pass; import contract unchanged; non-single
  -file topics carry correct file/command guidance.
- **Semantic:** per-chapter review recorded.
- **Invariance + integration:** Go-only patch; applied by one integrator or under
  a shared lock; abort on unexpected non-Go or unknown-Go changes.

## Risky files / rollback points

- `../qfli_studio_core/assets/content/{tutorials.json,examples.json}`: shared,
  concurrently edited. Highest risk; mitigated by patch-and-single-apply,
  baseline snapshot, and non-Go invariance checks. Never blind overwrite.
- Rollback: restore **only** the Go entries from the saved exact baseline Go
  slice, keeping the latest non-Go entries; never restore the whole file to an
  old snapshot.
- Do NOT touch: Go runner/native/terminal files, generated `.so`/`.h`, other
  languages' content.

## Follow-up checks before `task.py start`

- curriculum-map.md complete and reviewed.
- Durable `tool/go_curriculum/` layout agreed.
- `implement.jsonl`/`check.jsonl` contain real spec/research paths.
- Planning summary approved by the user in a subsequent message.
