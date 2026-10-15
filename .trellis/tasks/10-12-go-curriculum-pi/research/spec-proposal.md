# Spec proposal — Go curriculum content and tooling

Status: **landed.** The authoritative contract now lives in
[`.trellis/spec/backend/go-curriculum-tooling.md`](../../../../spec/backend/go-curriculum-tooling.md)
(7 sections) with a short cross-link from `frontend/content-code-import.md`.
This file is retained only as the task's record; do not duplicate the contract
here.

## 1. Scope / Trigger

Triggers code-spec depth because it defines a cross-layer content contract
(app assets → Dart content model → UI/import) plus a maintainable authoring and
integration pipeline for the Go learning content.

## 2. Signatures

Tooling under `qfli_go/tool/go_curriculum/`:

```
assemble.py  [--topics-dir DIR] [--out DIR]        # topics -> content/go + classify.json
verify.py    [--only IDS] [--go PATH] [--json] [--race]   # compile/run + variant + optional real -race
dedup.py     [--topics-dir DIR]                    # substantive-duplication check
patch.py     emit | dry-run | apply | rollback
author.py    build_topic(...) / write_topic(...)   # authoring helper (byte-exact code)
```

Shared content assets consumed by the Go app (`goshift` → `type:"go"`):

- `../qfli_studio_core/assets/content/tutorials.json`
- `../qfli_studio_core/assets/content/examples.json`

## 3. Contracts

Topic source file `tool/go_curriculum/topics/T<NNN>.json`:

- top-level: `id(T<NNN>), runtime(desktop|mobile), importKind(single-file|test-package|module-project), runCommand, verification{kind,expected}, sampleFiles[], tutorial{}, example{}`.
- `verification.kind ∈ {stdout-exact, stdout-sorted, stdout-normalized, test-pass, bench-exists}`.
- `tutorial`: `id(go-tutorial-NNN), language="go", type="go", locale="zh-CN", level(enum), title, summary, concepts[], source, license, updatedAt, objective, prerequisites[], pitfalls[>=2], exercises[>=1 {prompt,hint,answer}], explain, code, output`.
- `example`: `id(go-example-NNN), …, code, expectedOutput, templateType="go"`.

Aggregate mapping (assemble.py) — must match the real shared schema:

- tutorial entry keys: `id, language, type, locale, level, title, summary, concepts, source, license, updatedAt, lessons[]`.
- `lessons[0]` = `{id:"<entry>-lesson", title, summary, concepts, explain, code, output, objective, prerequisites, pitfalls, exercises}`.
- example entry keys: `id, language, type, locale, level, title, summary, concepts, source, license, updatedAt, code, expectedOutput, templateType`.
- `license` = `Original QFLI curriculum; reference link retained. CC BY 4.0` (repo convention, unchanged).

Constraints (enforced by assemble.py):
- `tutorial.code` byte-identical to a `sampleFiles` entry.
- `tutorial.output` non-empty for **every** topic, including `test-pass`/`bench-exists` (shared `ContentCatalogValidator.validateForRelease` requires it).
- `example.code` = exactly one syntactically valid Go file (never concatenated).
- every `samples/T<NNN>/` has `go.mod` (`module qfli.example/tNNN`).

## 4. Validation & Error Matrix

| Condition | Result |
| --- | --- |
| Empty `tutorial.output` | assemble FAIL (names topic) |
| `tutorial.code` ≠ any sample file | verify FAIL |
| `runCommand` uses shell metacharacters / first token ≠ `go` | verify FAIL (anti-spoof) |
| `go build ./...` fails | verify FAIL |
| stdout ≠ expected (exact/sorted/normalized) | verify FAIL with want/got |
| `test-pass` non-zero exit | verify FAIL |
| `bench-exists` no Benchmark output | verify FAIL |
| example `.code` ≠ tutorial and its output ≠ `expectedOutput` | verify FAIL |
| substantive template reuse | dedup FAIL |
| `patch apply` without `--confirm` | refuse, exit 2 |
| declared shared target missing | patch FAIL |

## 5. Good / Base / Bad Cases

- Good: `T007` tutorial + a distinct 2-line example variant, each asserted against its own expected output.
- Base: `T001` single-file `go run .` with fixed stdout.
- Bad: placeholder where only a title/constant differs (the case this task replaces); spoofed `runCommand` that echoes a string instead of compiling.

## 6. Tests Required (assertion points)

- `assemble.py` succeeds over the topic dir; rejects an empty-output topic.
- `verify.py` returns OK for each topic; a spoofed `runCommand` returns FAIL; `--race` records RACE-OK/RACE-FAIL via `mobile_check/run_race.sh`.
- `dedup.py` reports no substantive duplication.
- `patch.py dry-run` writes nothing; `apply` keeps non-Go and backs up old Go; `rollback` restores only Go and keeps the latest non-Go.
- Dart side (w8:p4): `test/go_curriculum_content_test.dart` parses the aggregate with the real `ContentCatalog.fromJson` + `validateForRelease`.

## 7. Wrong vs Correct

Wrong: write one flat tutorial object per topic into the aggregate (no `lessons[]`), or trust `runCommand` without compiling.
Correct: pack teaching fields into `lessons[0]` and force a real `go build` plus the declared run assertion per topic.

## Maintenance

- Content lives under `tool/go_curriculum/` (topics, samples, content/go, classify).
- `baseline/` holds the captured pre-change Go slice + shared hashes for rollback.
- Regenerate with assemble → verify → dedup → patch emit; apply is a single
  authorized integration step (dry-run first).
