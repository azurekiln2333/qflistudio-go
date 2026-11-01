# Go curriculum — topic source contract (shared by T001–T060 and T061–T120)

This is the authoring contract for the Go curriculum. Both authors (this Pi: T001–T060;
w8:p3 Pi: T061–T120) write **one file per topic** to the same layout, so the
assemble/verify/dedup/patch tools work uniformly.

## Topic file location and naming

```
tool/go_curriculum/topics/T<NNN>.json        # one topic = one tutorial + one example
tool/go_curriculum/samples/T<NNN>/            # runnable source backing that topic
tool/go_curriculum/classify.json             # generated; do not hand-edit across authors
```

`T<NNN>` is the topic id from `research/curriculum-map.md` (T001–T120). Do not
renumber. Do not edit another author's topic files or samples.

A `samples/T<NNN>/` directory may contain a minimal `go.mod`
(`module qfli.example/t<NNN>` / `go 1.21`) so `go run .` / `go test` work
regardless of the parent directory. `go.mod` is a support file and is **not**
listed in `sampleFiles` (which lists the run/source files).

## Topic JSON shape (one file, exactly one tutorial + one example)

```json
{
  "id": "T001",
  "runtime": "desktop",              // "desktop" | "mobile"
  "importKind": "single-file",       // "single-file" | "test-package" | "module-project"
  "runCommand": "go run .",          // exact command that produces the asserted output
  "verification": {
    "kind": "stdout-exact",          // "stdout-exact" | "stdout-sorted" | "stdout-normalized" | "test-pass" | "bench-exists"
    "expected": "hello, go\n"        // asserted expected result for stdout kinds; empty for test-pass/bench-exists
  },
  "sampleFiles": ["main.go"],        // files under samples/T<NNN>/ (relative names)
  "tutorial": {
    "id": "go-tutorial-001",         // stable aggregate id, keeps go-tutorial-NNN namespace
    "language": "go",
    "type": "go",
    "locale": "zh-CN",
    "level": "beginner",             // beginner | intermediate | advanced
    "title": "Go 语言与工具链概览",
    "summary": "一句话说明这一课解决什么问题。",
    "concepts": ["工具链", "go run", "gofmt"],
    "source": "https://go.dev/doc/",
    "license": "Original QFLI curriculum; reference link retained. CC BY 4.0",
    "updatedAt": "2026-10-12",
    "objective": "学完能……（可验证的能力，用「能……」句式）",
    "prerequisites": ["无"],
    "pitfalls": ["至少两条实质陷阱", "第二条…"],
    "exercises": [
      {"prompt": "练习要求", "hint": "提示", "answer": "参考答案"}
    ],
    "explain": "概念讲解 + 为什么 + 如何工作，按段落组织，不得只写一句模板。",
    "code": "package main\n...",     // 完整可运行源码，与 samples/T<NNN>/ 对应文件一致
    "output": "hello, go"            // 与 verification.expected 对应（stdout-exact 时去尾换行）
  },
  "example": {
    "id": "go-example-001",          // stable aggregate id, keeps go-example-NNN namespace
    "language": "go",
    "type": "go",
    "locale": "zh-CN",
    "level": "beginner",
    "title": "示例标题",
    "summary": "示例说明。",
    "concepts": ["工具链"],
    "source": "https://go.dev/doc/",
    "license": "Original QFLI curriculum; reference link retained. CC BY 4.0",
    "updatedAt": "2026-10-12",
    "code": "package main\n...",     // 恰好一个语法有效的 Go 文件，绝不拼接多文件
    "expectedOutput": "hello, go",
    "templateType": "go"
  }
}
```

### Shared-schema mapping (must match the real aggregate contract)

The aggregate tutorial entry carries a **`lessons[]` array**; lesson fields live
inside it. `assemble.py` must emit this real shape, not a flat tutorial object.

Top-level tutorial entry keys (exactly):
`id, language, type, locale, level, title, summary, concepts, source, license,
updatedAt, lessons[]`.

Each element of `lessons[]` (exactly):
`id, title, summary, concepts, explain, code, output, objective,
prerequisites[], pitfalls[], exercises[] {prompt,hint,answer}, inputFixtures`.

So a topic file's flat `tutorial.*` teaching fields are packed into ONE lesson
entry by `assemble.py`:

```
tutorial.id        -> entry.id
tutorial.title     -> entry.title  AND  lessons[0].title=tutorial.title
tutorial.summary   -> entry.summary AND  lessons[0].summary=tutorial.summary
tutorial.concepts  -> entry.concepts AND lessons[0].concepts=tutorial.concepts
tutorial.objective/prerequisites/pitfalls/exercises/explain/code/output
                   -> lessons[0].objective/prerequisites/pitfalls/exercises/explain/code/output
lessons[0].id      -> "<entry.id>-lesson"   (stable, unique)
```

Example entry keys (exactly):
`id, language, type, locale, level, title, summary, concepts, source, license,
updatedAt, code, expectedOutput, templateType, inputFixtures` (no `lessons`).

License: reuse the repository's existing convention verbatim —
`Original QFLI curriculum; reference link retained. CC BY 4.0`. Do not introduce
a new license or reattribute authorship.


1. **One tutorial + one example per topic**, ids `go-tutorial-NNN` /
   `go-example-NNN` matching the topic number (T007 → `go-tutorial-007`).
2. `tutorial.code` and `example.code` are each **exactly one syntactically valid
   Go file** — never concatenate `go.mod` + `main.go` + `_test.go`. For
   `test-package`/`module-project`, `code` is the single most representative
   file (`main.go` or `*_test.go`), and `explain`/`pitfalls` name the companion
   files and the exact commands.
3. `tutorial.code` must be byte-identical to the corresponding file in
   `samples/T<NNN>/` (the verifier asserts this). `example.code` may equal
   `tutorial.code` for a topic, or a focused variant, but must also compile/run.
4. `verification.kind`:
   - `stdout-exact`: stdout must equal the expectation after CRLF and one final newline normalization; other whitespace remains significant.
   - `stdout-sorted` / `stdout-normalized`: line order/whitespace normalized
     before comparison (concurrent or map-ordered output).
   - `test-pass`: actual test functions pass; a zero-exit helper or all-skipped suite fails.
   - `bench-exists`: `go test -bench . -run '^$'` runs at least one benchmark.
5. `runtime` = `mobile` requires execution through the current packaged FFI runtime on an actual supported target. Host interpreter results alone do not establish this claim. Retain desktop labels while the device gate is open.
6. Preserve language concepts and fix reproduced interpreter defects rather than replacing examples with easier code. Current source-backed regressions cover method expressions, source/native interfaces, errors, formatting and generic inference; old mobile-validation reports remain historical evidence.
7. `level` must be one of `beginner | intermediate | advanced`.
8. All text is Chinese (`zh-CN`). No filler; each lesson has real
   objective/prerequisites/≥2 pitfalls/≥1 exercise with answer.
9. No shared template `explain` across topics; no “same code with a different
   constant”. Reasonable shared primitive lines are allowed.
10. `sampleFiles` lists every file under `samples/T<NNN>/` needed to run.
11. `tutorial.output` must be **non-empty for every topic**, including
    `verification.kind` = `test-pass` / `bench-exists`. This is required by the
    shared `ContentCatalogValidator.validateForRelease` (which rejects an empty
    lesson `output`). Write the real result text (e.g. `ok` / `PASS` / the
    observed benchmark line). The pass/fail decision is still determined solely
    by `verification`; `output` is display text, not the assertion.

## Tooling

- `assemble.py` reads `topics/*.json` → `content/go/tutorials.json` +
  `content/go/examples.json` + `classify.json`.
- `verify.py` compiles/runs each topic's sample and records per-item evidence.
- `dedup.py` substantive-duplication check.
- `patch.py` emits the reviewable Go slice patch.

Do not hand-edit `content/go/*` or `classify.json`; regenerate via
`assemble.py`.

## Notifications

Contract changes must be mirrored here and announced to the other author before
relying on them.

## Actual imported project and product-owned catalogs (2026-10-22)

`assemble.py --app-out assets/curriculum` also writes `{schemaVersion:1,entries:[...]}` application catalogs. The tool `content/go` slices remain arrays for the existing patch tooling. No shared product catalog is mutated by this command.

Every lesson and example receives `inputFixtures: Map<String,String>` derived from all canonical support files. The displayed tutorial must match exactly one canonical Go source. That file is omitted from fixtures and imported unchanged as `src/main.go`, or `src/snippet_test.go` for test topics. Same-package helpers and data (including testdata/embed inputs) move alongside the source under `src/`; module metadata and complete imported-subpackage trees retain module-root paths. The actual shared `CodeImportService.suggestedFileName(type, code: code)` independently checks the default test filename. Fixture paths cannot collide with the source, escape the project or overwrite reserved metadata.

`audit_native.py` enumerates both displayed imported shapes and canonical projects plus otherwise-unexecuted support tests. Native test acceptance requires `testExecution.engine == qfli-embedded-testing-v1`, complete nonnegative consistent execution counts, no failed/skipped tests, every declared test/fuzz and required benchmark, fuzz-seed counts, and a genuine passing transcript. The test engine records actual benchmark measurements; curriculum authoring must not invent performance numbers. A host pass and a packaged OHOS pass are separate evidence levels.

The native audit starts outside each materialized project and the device harness never assigns `Directory.current`. Each call must leave the host process working directory unchanged; a mutation is a recorded case failure, not something the harness restores. The production interpreter resolves relative file operations from the selected entry's directory. Official compiler commands also start in that directory, matching the desktop run action, while module lookup can find go.mod in a parent directory. Each manifest case records its workingDirectory explicitly.
