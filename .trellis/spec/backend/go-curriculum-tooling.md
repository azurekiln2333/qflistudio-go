# Go Curriculum Tooling

Execution policy: apply `AGENTS.md` and [Cloud-Only Execution](cloud-only-execution.md).
All verification, generators and dependency/toolchain setup below run only in
GitHub-hosted Actions. Historical local results do not authorize local reruns.
The canonical sibling is `../qflistudio-core`; old `../qfli_studio_core` paths in
historical command examples describe the previous layout, not the target clone.
Shared-core writes remain with its assigned owner.

## 1. Scope / Trigger

Trigger: authoring, verifying, or integrating the Go learning content that the Go
app displays (`goshift` product → `type:"go"` entries). This is a cross-layer
contract: topic source → aggregate assets in `../qfli_studio_core` → Dart
content model → UI/import. Any change to the Go content slice, its verification,
or its shared-file integration must follow this spec.

Authoritative source of truth and tools live under `qfli_go/tool/go_curriculum/`.
The shared assets are written only by a single authorized integration step.

Learner-facing entry point: `tool/go_curriculum/GUIDE.md` (learning roadmap,
chapter index, how to run single-file/test/module samples, common-error
diagnostics, desktop/mobile limits). Keep it in sync when the topic set or
platform boundary changes.

## 2. Signatures

```
tool/go_curriculum/
  schema.md                                  # authoring contract (topic source)
  topics/T<NNN>.json                         # one topic = one tutorial + one example
  samples/T<NNN>/                            # runnable Go source (+ optional go.mod)
  content/go/{tutorials,examples}.json       # assembled Go slice
  classify.json                              # id -> runtime/importKind/runCommand/verification
  baseline/                                  # captured pre-change Go slice + shared hashes
  patch-go/                                  # emitted reviewable slice + manifest
  apply-backup/                              # exact previous Go slice after apply
  evidence/verify-results.json               # per-topic verification evidence

  assemble.py  [--topics-dir DIR] [--out DIR]
  verify.py    [--only IDS] [--go PATH] [--json] [--race]
  dedup.py     [--topics-dir DIR]
  patch.py     emit | dry-run | apply | rollback
  author.py    build_topic(...) / write_topic(...)
```

Commands:

```
python tool/go_curriculum/assemble.py
python tool/go_curriculum/verify.py
python tool/go_curriculum/dedup.py
python tool/go_curriculum/patch.py emit
python tool/go_curriculum/patch.py dry-run --shared ../qfli_studio_core/assets/content
python tool/go_curriculum/patch.py apply   --shared ../qfli_studio_core/assets/content --patch tool/go_curriculum/patch-go --confirm
python tool/go_curriculum/patch.py rollback --shared ../qfli_studio_core/assets/content --backup tool/go_curriculum/apply-backup --confirm
```

SDK (pinned, local): `native/build/go-sdk-1.27.1/go/bin/go.exe` (go1.27.1).

## 3. Contracts

Topic source (`topics/T<NNN>.json`):

- top-level: `id (T<NNN>)`, `runtime (desktop|mobile)`,
  `importKind (single-file|test-package|module-project)`, `runCommand`,
  `verification {kind, expected}`, `sampleFiles[]`, `tutorial{}`, `example{}`.
- `verification.kind ∈ {stdout-exact, stdout-sorted, stdout-normalized,
  test-pass, bench-exists}`.
- `tutorial`: `id (go-tutorial-NNN), language:"go", type:"go", locale:"zh-CN",
  level (beginner|intermediate|advanced), title, summary, concepts[],
  source, license, updatedAt, objective, prerequisites[], pitfalls[>=2],
  exercises[>=1 {prompt,hint,answer}], explain, code, output`.
- `example`: `id (go-example-NNN), language:"go", type:"go", locale:"zh-CN",
  level, title, summary, concepts[], source, license, updatedAt, code,
  expectedOutput, templateType:"go"`.
- `license` reuses the repository convention verbatim:
  `Original QFLI curriculum; reference link retained. CC BY 4.0`.

Aggregate mapping (what the shared schema actually is; produced by assemble.py):

- tutorial entry keys exactly: `id, language, type, locale, level, title, summary,
  concepts, source, license, updatedAt, lessons[]`.
- the flat `tutorial.*` teaching fields are packed into a single
  `lessons[0] = {id:"<entry-id>-lesson", title, summary, concepts, explain, code,
  output, objective, prerequisites, pitfalls, exercises}`.
- example entry keys exactly: `id, language, type, locale, level, title, summary,
  concepts, source, license, updatedAt, code, expectedOutput, templateType`.

Constraints enforced by `assemble.py`:

- `tutorial.code` byte-identical to a `sampleFiles` entry.
- `tutorial.output` **non-empty** for every topic, including `test-pass` /
  `bench-exists` (the shared `ContentCatalogValidator.validateForRelease` rejects
  an empty lesson `output`). Pass/fail is decided by `verification`, not `output`.
- `example.code` is exactly one syntactically valid Go file (never a
  concatenation of `go.mod` / `main.go` / `_test.go`).

`go.mod` policy: a sample directory **may** include a `go.mod`; its module path
is a teaching name and is **not** required to be `qfli.example/tNNN` (any valid
module path is allowed, e.g. `example.com/demo`). Directories without `go.mod`
are module-less single-file samples run via `go run .` / `GO111MODULE=off`.

## 4. Validation & Error Matrix

| Condition | Result |
| --- | --- |
| `tutorial.output` empty | assemble FAIL (names topic) |
| `tutorial.code` ≠ any `sampleFiles` `.go` file | verify FAIL |
| `runCommand` contains shell metacharacters | verify FAIL (anti-spoof) |
| `runCommand` first token ≠ `go`/`go.exe` or not a Go subcommand | verify FAIL |
| compile fails | verify FAIL |
| stdout ≠ expected (exact/sorted/normalized) | verify FAIL (want vs got) |
| `test-pass` non-zero exit | verify FAIL |
| `bench-exists` no `Benchmark` output | verify FAIL |
| example `.code` ≠ tutorial and its output ≠ `expectedOutput` | verify FAIL |
| substantive template reuse | dedup FAIL |
| `patch apply` without `--confirm` | refuse, exit 2 |
| `patch apply` on non-Windows OS | fail-closed (Windows file sharing locks required) |
| `patch` competing/non-cooperating writer holds the target | `CreateFileW` open fails; apply aborts, no change |
| declared shared target missing | patch FAIL |

`patch.py` integration contract (R8):

- `emit` writes the reviewable Go slice + manifest to `patch-go/`.
- `dry-run` runs the **same** transform and validation as apply and writes
  nothing.
- apply replaces only the contiguous Go run in `entries[]` via a **raw
  byte-splice**: prefix/suffix non-Go bytes are byte-identical (no whole-file
  JSON re-serialization). Each non-Go entry therefore keeps its **relative
  position around the Go block**; this is relative-block preservation, not an
  absolute byte-offset guarantee (the Go block length changes). Non-contiguous
  Go layout is an explicit failure.
- apply refuses if the current Go entries differ from `baseline/` (unknown Go
  edits), changing nothing.
- exclusivity (Windows-only mutation): apply opens both targets with
  `CreateFileW` denying write/delete sharing, so a competing writer — even a
  non-cooperating one that never takes our lock — is refused (open fails, apply
  aborts, no file changes). On any non-Windows platform mutation is **fail-closed**
  (`shared mutation requires Windows file sharing locks`); advisory `flock` is
  rejected as insufficient.
- both targets are verified before either is written; on a write failure the
  already-written targets (including a partially written one) are restored from
  the in-memory originals. This is **in-process exception recovery**, not a
  power-loss transaction; the `--backup` originals cover process-kill cases.
- `rollback --confirm` restores only the Go entries, preserving the latest
  non-Go edits, under the same `CreateFileW` exclusivity.

Compile rule (must not fail a runnable sample): if the sample dir has `go.mod`,
compile with `go build ./...`; otherwise compile module-less with
`GO111MODULE=off GOFLAGS= go build -o <tmp> .`. The compile step writes no binary
into the sample directory.

`--race` runs the real race gate via `mobile_check/run_race.sh` (WSL
`qfli-java-build`, project Linux SDK, `CGO_ENABLED=1`) and records
`RACE-OK`/`RACE-FAIL`; do not substitute plain `go test` for concurrency topics.

## 5. Good / Base / Bad Cases

- Good: `T007` tutorial plus a distinct 2-line example variant, each asserted
  against its own `expectedOutput`; module-less sample compiled with
  `GO111MODULE=off`.
- Base: `T001` single-file `go run .` with fixed stdout; `T059` is a
  `module-project` whose `sampleFiles` may include `go.mod` as a support file.
- Bad: template content where only a title/constant differs (the pattern this
  spec replaces); a spoofed `runCommand` that echoes a string instead of
  compiling; a wall-clock-racy assertion (fixed by waiting on a never-ready
  channel instead of racing a timeout).

## 6. Tests Required (assertion points)

- `assemble.py` succeeds over `topics/` (120/120) and rejects an empty-output
  topic.
- `verify.py` returns OK for every topic and writes
  `evidence/verify-results.json`; a spoofed `runCommand` returns FAIL.
- `dedup.py` reports no substantive duplication.
- `patch.py dry-run` writes nothing; `apply --confirm` keeps every non-Go entry
  and backs up the exact previous Go slice; `rollback --confirm` restores only
  Go entries and preserves the latest non-Go edits; non-Windows apply is
  fail-closed; a competing writer is refused without changing any file.
- Dart side: `test/go_curriculum_content_test.dart` parses the aggregate with the
  real `ContentCatalog.fromJson` + `validateForRelease` (owned by the review
  task).

## 7. Wrong vs Correct

Wrong:

```python
# one flat tutorial object per topic, no lessons[]; and trust runCommand
entry = {"id": "go-tutorial-001", "code": ..., "output": ...}   # no lessons[]
proc = run(topic["runCommand"])                                  # never compiles
```

Correct:

```python
# pack teaching fields into lessons[0]; force a real compile then assert
entry = {"id": "go-tutorial-001", ..., "lessons": [{"id": "go-tutorial-001-lesson", ...}]}
compile_sample(topic, go)     # go.mod-aware; GO111MODULE=off for module-less
assert_result(topic, run(topic["runCommand"]))
```

## Verification failures (2026-10-15)

Resolve explicit --go to an absolute existing file before subprocess cwd changes;
a missing explicit executable must fail rather than silently use the default SDK.
With --race, only exact RACE-OK is success. RACE-FAIL, missing topic results,
gate-script/executable absence, timeout and nonzero WSL exit all count as failures
and require nonzero CLI exit. Keep ordinary compiler verification independent.
`test_verify_race.py` asserts both totals and exit codes under injected gate
results; subprocess-level failures are also required to raise VerificationError.


## Controlled Chinese prose contract (2026-10-26)

Apply this contract when editing Chinese tutorial/example prose. Start the
mechanical check with `python scripts/ste-lint-zh.py <projection-files>`.
The check does not establish semantic acceptance.

- Keep one action per sentence. Instructions have at most25 characters;
  explanations have at most40. Check objective, exercise prompt and hint fields
  separately at25; a complete projection checked at40 cannot prove this limit.
- Use active voice and stable terms for the same concept. A lexical majority
  does not prove two technical concepts are equivalent. Do not merge rendered
  text width with terminal capacity, physical slot order with insertion order,
  human comparison with error validation, or panic with an error result.
- Preserve each field's exact `可能` and `也许` counts and meaning. Sentence
  splitting must keep a condition attached to its consequence and a warning
  attached to the operation it forbids. An isolated incorrect operation can
  read as a new instruction.
- Do not hide prose in inline code or fences to avoid findings. Inline code is
  appropriate for real data such as `a;b.txt`, not a sentence containing it.
- Preserve the complete code/output/verification/ID/runtime/source/license/
  prerequisite/sample-file data and JSON structure for a prose-only edit.
  Freeze the allowed string-leaf paths before editing. Replace only those leaves
  in a deep copy with `<MUTABLE_CHINESE_PROSE>`, then hash UTF-8 JSON with
  `ensure_ascii=False, sort_keys=True, separators=(',', ':')`. Compare with the
  frozen immutable hash. Independently compare every sample's byte SHA-256.
- Generate lint projections from current JSON in frozen path order using
  `## <dot.path>`, a blank line, and the literal field value. Compare projection
  contents back to JSON. Treat Windows newline conversion and final blank lines
  separately from actual literal CRLF teaching data.
- Advisory-only linter findings still need review against the user's active
  voice and precise-language rules. A zero exit code is not zero findings.
  A zero-finding scan cannot detect deleted boundary cases or invented behavior.
- Independently compare changed prose against the original and the real program.
  Correct factual prose defects explicitly: one basis point is1/10000,
  `1024²` means1024 multiplied by1024. Use the exact numeric expression
  rather than a mistranscribed Chinese number. Duplicate-file savings use each group's
  file count minus one. Record intentional factual corrections instead of
  treating an old numeric/identifier multiset as an immutable contract.

Required review examples: a ring buffer's physical slot order can differ from
chronological order; insertion order already expresses chronological writes.
A buffered report followed by `fmt.Print` does not establish an atomic file
replacement guarantee. Equal ledger totals can conceal both missing records
and offsetting incorrect amounts. A copied-map patch must apply operations in
the copy before committing. An input patch's sorted field names can include
supplied no-op values and are not just names of changed configuration values.

Record source/lint/semantic checks independently from compiler/native/FFI/OHOS
execution. A prose-only pass never permits draft promotion before the required
original-corpus OHOS baseline.


## Standalone catalog routing and archive proof (2026-10-26)

`lib/main.dart` installs `GoContentRepository` through the Go profile's
`contentRepositoryFactory` before `runApp`. That repository loads
`assets/curriculum/tutorials.json` and `examples.json` through `rootBundle`.
`pubspec.yaml` declares `assets/curriculum/`. The shared home page prefers the
profile factory; shared `AssetContentRepository` is only its fallback.

The content model parses `inputFixtures` for lessons and examples. The local
content adapter preserves them, the tutorial page passes them to `CodeSnippet`,
and `CodeImportService.projectFiles` validates and merges them into the imported
project. Check this complete source path before diagnosing fixture loss from a
comparison with the shared fallback catalog or an older extracted package.

For a fresh OHOS package, inspect byte equality at
`resources/rawfile/flutter_assets/assets/curriculum/{tutorials,examples,audit-manifest}.json`
with `tool/inspect_go_catalog_hap.py`. Source routing and old shared fallback
bytes do not prove the contents of a signed HAP. A fresh archive pass still does
not prove device execution. The shared-core `patch.py` target remains C-owned;
it is not required merely to expose fixtures in the current standalone source.

Source regression locations are `test/go_content_repository_test.dart` and
`test/go_curriculum_content_test.dart`. Inspecting them is source evidence only;
record actual execution and package/device gates separately.
