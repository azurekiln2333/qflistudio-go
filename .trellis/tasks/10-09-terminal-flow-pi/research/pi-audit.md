# Pi audit — selected-entry coexistence in the Go terminal flow

Status: **planning research only. No production or test code changed.**
Owner: pi-go-terminal (right pane w8:p2), directed by Codex.
Task: `.trellis/tasks/10-09-terminal-flow-pi`.

## 1. Verified defect

Both execution backends ignore the selected `entryFile` and compile the whole
entry directory:

- Desktop `lib/go_runner.dart` -> `go run .` in the entry directory.
- Embedded `native/go_runtime/runtime.go` -> Yaegi `EvalPathWithContext` on the
  entry's package directory (Yaegi `importSrc` parses *every* `.go` file).

Consequences with the acceptance fixture (`main.go` + `main2.go`, both
`func main`, plus `helper.go`):

- `go run .` fails: `main redeclared in this block`.
- Selecting `main2.go` (long-press "run current file") cannot take effect.

Correction accepted from Codex: `go run main2.go` compiles **only** the named
file (cwd does not add siblings); helpers normally carry `package main`, so
"drop other package-main files" would drop helpers. Therefore the fix must
remove **only competing top-level `func main` files**, never helpers.

## 2. Empirical proof (SDK `native/build/go-sdk-1.27.1/go/bin/go.exe`, go1.27.1)

Fixture `src/`: `go.mod` (`example.com/fx`), `main.go` and `main2.go` each with
their own top-level `func main` and `//go:embed asset.txt`, `helper.go`
(`package main`), `localpkg/` local import, `asset.txt`, and a
platform-excluded `only_linux.go`. Run with `GOMAXPROCS=2`, `GOFLAGS=-p=1`,
`GOTOOLCHAIN=local`.

| Command | Result | Exit |
| --- | --- | --- |
| `go run .` | `main redeclared in this block` (and `asset redeclared`) | 1 |
| `go run -overlay ov_main.json .` where overlay deletes `main2.go` | `MAIN helper=HELPER pkg=LOCALPKG asset=EMBEDDED-ASSET` | 0 |
| `go run -overlay ov_main2.json .` where overlay deletes `main.go` | `MAIN2 helper=HELPER pkg=LOCALPKG asset=EMBEDDED-ASSET` | 0 |
| broken `helper.go`, overlay selects `main.go` | genuine `undefined: missingSymbol` diagnostic passes through | 1 |
| `GO111MODULE=off` (no go.mod), overlay deletes `main2.go` | `M1 HELPER` | 0 |
| `go build -overlay ov_main.json .` | succeeds; `only_linux.go` stays excluded | 0 |
| `go run main2.go` (reference) | `undefined: helper` — named file compiles alone | 1 |
| `go run main2.go helper.go` (reference) | `MAIN2 HELPER` — siblings must be named | 0 |

Proven properties of the overlay approach:

- `-overlay` Replace `{absolutePath: ""}` makes the source **not exist** for the
  build while leaving it on disk untouched.
- Helpers, local package imports, `//go:embed` assets, module context, and
  platform/build-constraint filtering are all preserved — the Go compiler still
  computes the real build view; only the named competing file disappears.
- Overlay temp JSON path never needs to appear in product output; only the
  compiler's own diagnostics are surfaced.
- Works identically for the OHOS compiler
  `native/build/ohos-go-f2cb44316b789bc12d0b5fd562d853f6fec3ab28/bin/go.exe`
  (`go1.27.1-ohos`, same overlay semantics).

Overlay is strictly safer than named-file lists (no reimplementation of build
tags / GOOS / GOARCH / embed), and does not require reproducing `go list`.

## 3. Why `go run .` stays the default

- Ordinary packages with a single top-level `main`: run `go run .` **without any
  overlay** — byte-identical to today, zero risk.
- A competing `main` is only declared when the directory has >1 top-level
  `func main`. Only then build the overlay JSON.
- If the selected file has no top-level `func main`: report
  `no main function in <filename>` and exit non-zero. Never fall back to another
  file's `main`.

## 4. Detection contract

- **Dart:** comment/string-aware tokenizer for **top-level** `func main`. Must
  correctly ignore `//`, `/* */`, `"..."`, raw `` `...` ``, and rune literals;
  count only `func main` at top level (not methods `func (r X) main()` and not
  indented closures). No regex-only heuristic.
- **Native:** real `go/parser` / `go/ast` (`parser.ParseFile` +
  `parser.SkipObjectResolution`) for the same contract.

## 5. Native design (no vendored Yaegi edits)

Yaegi touches the FS only via `fs.ReadDir` and `fs.ReadFile`/`Open`. Filter at
the FS boundary instead of changing Yaegi APIs:

1. In `runGoWithContext`, parse the entry directory with `go/parser` to find
   sibling `.go` files declaring a top-level `func main`.
2. Pass the selected entry basename into the FS wrapper.
3. Add `ReadDir(name string) ([]fs.DirEntry, error)` to `projectSourceFS`
   (satisfies `fs.ReadDirFS`, which `io/fs.ReadDir` prefers) that hides
   competing top-level-`main` siblings **only for the entry directory**; every
   other listing (helpers, imported subpackages) is untouched. `Open` for direct
   file reads stays as-is.
4. If the entry has no top-level `func main`, return exit 1 with
   `no main function in <filename>`.
5. Do not change `bridge.go` (C ABI), cancellation maps, `outputBuffer`, or
   `Args`. No vendored Yaegi edits; `-mod=vendor` fixes remain intact.

## 6. Desktop design (`lib/go_runner.dart`)

For `GoToolAction.run` only:

1. Keep `workingDirectory = entryDirectory`.
2. Token-scan the directory's `.go` files for top-level `func main`.
3. If the selected entry declares `func main` and no sibling does: keep
   `['run', '.']`.
4. If the selected entry declares `func main` and siblings do: write an overlay
   JSON (temp file outside the project source tree, cleaned after the run) that
   maps each competing sibling's absolute path to `""`, and pass
   `['run', '-overlay', overlayPath, '.']`.
5. If the selected entry lacks `func main`: return a non-run result with
   `no main function in <filename>` and a non-zero exit; never run another main.
6. Surface genuine compiler/parse diagnostics unchanged (verified above).
7. `build`/`test`/`fmt`/`vet`/`modTidy`, `_findModule`, `_binaryPath`,
   `_cancel`, stream/exit plumbing: **unchanged**.

## 7. Titles

- Native success title (`native_go_bridge_ffi.dart`, `native_go_bridge_stub.dart`):
  `go run <basename(entryFile)>` (e.g. `go run main2.go`). No "Go 运行时" /
  "embedded runtime" wording.
- Desktop success title already derives `go <args>`; with the overlay it should
  present the selected file, i.e. `go run <basename>`, not the overlay temp path.
- Error-only `_unavailable` label stays `Go 工具链`.

## 8. Bounded file ownership (edits deferred until reviewed go-ahead)

| File | Change |
| --- | --- |
| `lib/go_runner.dart` | run-action overlay selection + top-level-`main` tokenizer + reject-no-main; other actions untouched |
| `lib/native_go_bridge_ffi.dart` | success title -> `go run <basename>` |
| `lib/native_go_bridge_stub.dart` | success title -> `go run <basename>` |
| `native/go_runtime/runtime.go` | `go/parser`-based sibling detection + filtered `projectSourceFS.ReadDir`; no vendored edits |
| `.trellis/spec/backend/native-go-runtime.md` | document alternate-entry case + contract (after code lands) |

Not touched: `bridge.go`, `main.go`, vendored Yaegi, `go_platform.dart`,
`build/test/fmt/vet/tidy` paths, core or sibling apps.

## 9. Test plan

Desktop `test/go_toolchain_test.dart` (SDK-gated), fixture with 3 files
(`main.go` + `main2.go` both `func main`, `helper.go`):
- tap → `entryFile=main.go` -> stdout `main`; long-press → `main2.go` -> `main2`;
  tap → `main.go` -> `main`.
- `entryFile=helper.go` -> non-zero + `no main function`.
- helper symbol resolves in both mains (helpers retained).
- Add `localpkg` import + `//go:embed` asset + `only_linux.go` to prove module,
  embed, and constraint handling survive the overlay.
- Genuine compile error still produces its diagnostic.
- `build/test/fmt/vet/tidy` outputs unchanged.
- Unit tests for the tokenizer: `//`, `/* */`, `"..."`, raw string, rune,
  method `func (r X) main()`, indented closure, real top-level.

Native `native/go_runtime/runtime_test.go`:
- `TestRunGoSelectsEntryWithSiblingMain`: `main.go` -> `main`,
  `main2.go` -> `main2`, both using `helper` and a subpackage import.
- `TestRunGoRejectsEntryWithoutMain`: `helper.go` entry -> non-zero + diagnostic.
- Existing multi-file test stays green.
- Constraint/`_test`/subpackage guards remain green.

Integration `integration_test/go_native_test.dart`:
- Extend the multi-file case to the 3-file fixture on Android/OHOS/iOS and
  assert entry selection.

## 10. Baseline evidence (unchanged repo)

- `go test -mod=vendor ./...` in `native/go_runtime`: ok.
- `go vet -mod=vendor ./...`: clean.
- Codex: shared terminal/editor suite 22 pass; 5 current visual renders pass.

## 11. Scratch / safety

- All scratch under `.artifacts/terminal-flow-pi/`; the disposable fixtures
  `fx_overlay` and `fx_nomod` were removed after proving, with the absolute
  target verified inside that directory before recursive delete. No global
  environment was changed (process-scoped `GOFLAGS`/`GOMAXPROCS`/`GOTOOLCHAIN`
  only).
