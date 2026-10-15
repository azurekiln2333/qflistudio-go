# Design — Go curriculum content, samples and integration

## Architecture and data flow

```
qfli_go/tool/go_curriculum/                      (durable, task-owned, this repo)
  content/go/tutorials.json    ← authored Go lessons (source of truth)
  content/go/examples.json     ← authored Go examples
  samples/<topic-id>/main.go (+ *_test.go)  ← runnable source per topic
  assemble.py  verify.py  dedup.py  patch.py   ← tooling
        │
        │ (1) author + compile/run locally with pinned SDK
        │ (2) assemble Go slice
        │ (3) emit reviewable patch vs shared aggregate files
        ▼
../qfli_studio_core/assets/content/{tutorials.json,examples.json}   (shared, applied later)
        │
        ▼
AssetContentRepository → ContentCatalog.fromJson → LocalContentAdapter
  → LocalTutorialsTab / ExampleCodeTab / _LessonPage / ExampleDetailPage
  → CodeSnippet → CodeImportService (unchanged single-file import contract)
```

Content authoring and all verification happen **in this workspace**. The shared
files are only touched by a single authorized integration step applying the
reviewed Go slice.

## Durable content locations (C3)

- `qfli_go/tool/go_curriculum/content/go/tutorials.json` — Go lesson slice
  (120 entries), same schema as the shared aggregate's Go entries.
- `qfli_go/tool/go_curriculum/content/go/examples.json` — Go example slice (120).
- `qfli_go/tool/go_curriculum/samples/<topic-id>/` — one runnable Go program (or
  test/benchmark package) per topic, the compile/run evidence source.
- `qfli_go/tool/go_curriculum/{assemble,verify,dedup,patch}.py` +
  `README.md` — maintainable tooling and usage.
- The task `research/` may hold review notes/evidence, but is not the only home
  for content or scripts.

## Content contract (must satisfy existing parser + validator)

Tutorial entry: `id, language="go", type="go", locale="zh-CN", level, title,
summary, concepts[], source, license, updatedAt, lessons[]`.
Lesson: `id, title, summary, concepts[], explain, code, output, objective,
prerequisites[], pitfalls[], exercises[]` (`{prompt,hint,answer}`).
Example: `id, language="go", type="go", locale="zh-CN", level, title, summary,
concepts[], source, license, updatedAt, code, expectedOutput, templateType="go"`.

The Go app maps each tutorial entry to one chapter (current shape), so 120
entries = 120 chapters/lessons. Keeping one lesson per chapter preserves the
adapter and navigation contract.

## Runtime honesty model (R5)

Classification is derived from **this project's** native runtime
(`native/go_runtime`, Yaegi + local fixes), verified by actually running samples
under the embedded interpreter, not from vendor documentation.

- **desktop-only by default**: all generics topics; `go.mod`/modules, `net/http`
  servers and listeners, `os/exec`, cgo, `//go:embed`, `//go:generate`,
  `testing`/benchmarks/`fuzz`, performance/profiling, `-race`.
- **mobile-candidate (Yaegi\*)**: only promoted to "mobile-safe" after a sample
  is executed under the actual native interpreter and passes. Until then the
  lesson is marked desktop-only with the exact command. Candidates are simple,
  deterministic stdlib topics (control flow, slices/maps, structs/methods,
  interfaces, errors/defer/recover, `strings/strconv/sort/fmt/encoding/json`,
  basic `context`, basic goroutine/channel).
- No lesson claims mobile support that the native runtime has not demonstrated.

Every lesson records `runtime: desktop|mobile` plus the verification command;
the JSON slice carries this in existing fields (`level`/`concepts`/`explain`
text and, where useful, a `source`/summary note) without adding schema fields.

## Honest representation of non-single-file topics (R6)

The import contract writes exactly one file and sets `entryFile` to it. Therefore
every example's `code` field is **always exactly one syntactically valid Go
file** — never a concatenation of `go.mod` + `main.go` + `_test.go` into an
invalid, unimportable blob. For topics that need more than one file, `code`
holds the single most representative file (usually `main.go`), and the lesson's
`explain`/`pitfalls` state the complete companion file set and commands. The
full, runnable file set always lives under the durable
`qfli_go/tool/go_curriculum/samples/<topic-id>/` path.

Per-topic labels (recorded in `classify.json` and stated in the lesson):

- **single-file importable**: one self-contained `package main` runnable via
  `go run main.go`; `code` is that file; `suggestedFileName('go') == 'main.go'`
  stays valid.
- **test-package**: `code` is exactly one valid `*_test.go` file. The lesson names
  the companion non-test file(s) it imports, the full tree under
  `samples/<topic-id>/`, and the command (`go test ./...`,
  `go test -bench . -benchmem`, `go test -fuzz FuzzX`). It does **not** claim
  one-click import.
- **module-project**: `code` is one valid `.go` file from the module. The lesson
  names `go.mod`, the package tree, and the commands (`go mod init ...`,
  `go build -tags ...`). It does **not** claim lossless multi-file import.

Decision recorded before coding: each of the 120 examples is labeled
`single-file | test-package | module-project`; `example.code` is one valid file;
companion files and commands live in the lesson text and the permanent samples
path.

## Shared-repo integration and concurrency (R8, AC7)

Two mechanisms, in order of preference:

1. **Single integrator (preferred).** This task emits a Go-slice patch (a JSON
   fragment plus a deterministic merge function that replaces only `type == "go"`
   entries and document `updatedAt`). One authorized integrator applies it. No
   other writer runs the apply step.
2. **Lock protocol.** If multiple writers must apply, they use a shared lock
   (e.g. an agreed lock file checked into `qfli_studio_core` root) so applies are
   serialized.

Explicitly rejected: "atomic rename + pre-read hash" as a substitute for a writer
protocol, because it cannot observe a concurrent writer's edit that lands between
read and rename, nor another writer's unknown Go changes. **Never last-writer-wins
over unknown Go edits.** The patch tool re-reads at apply time; if the non-Go
entries or unknown Go edits differ from what the patch expects, it aborts and
reports rather than overwrite.

Application is a permission boundary requiring user authorization for the
precise shared files (see C1). Content authoring does not wait on it.

## Tooling

- `assemble.py` — build the Go slice JSON from the durable content/samples.
- `verify.py` — compile/run every sample with the pinned SDK; for
  concurrent/benchmark samples use the pre-declared deterministic assertion;
  emit per-item evidence.
- `dedup.py` — substantive-duplication detection with a primitive whitelist;
  ignores identical trivial outputs and a lesson's own paired example code.
- `patch.py` — emit the reviewable Go-only patch and the guarded apply step.

## Compatibility and rollback

- Go entry ids stay in `go-tutorial-NNN` / `go-example-NNN`; new ids extend the
  range. No schema/locale change.
- Before integration, save the **exact previous Go slice** (the current Go
  entries of both shared files, byte-for-byte) under
  `qfli_go/tool/go_curriculum/baseline/`.
- Rollback is a Go-scoped restore, not "discard the patch": re-read the shared
  files at rollback time, replace **only** the Go entries with the saved exact
  Go slice, and leave every non-Go entry as it is at that moment (i.e. keep the
  latest non-Go content authored by other sessions). Never restore the whole file
  to an old snapshot, which would revert other languages' newer work.

## Trade-offs

- One lesson per chapter keeps the adapter/navigation contract and other
  language parity; grouping multiple lessons per chapter is out of scope.
- zh-CN only (existing Go contract); additional locales multiply authoring and
  verification cost.
- Keeping content/samples/tools under `tool/go_curriculum/` makes them
  maintainable and re-verifiable, at the cost of a small committed tool tree.
