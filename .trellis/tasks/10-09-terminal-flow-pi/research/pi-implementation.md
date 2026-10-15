# Pi implementation — selected-entry Go execution

Status: implementation complete for source + focused tests. No binaries rebuilt.
Owner: pi-go-terminal (right Herdr pane w8:p2), directed by Codex.
Task: `.trellis/tasks/10-09-terminal-flow-pi`.

## What changed

Selected-entry execution now honors `entryFile` on both backends by removing
only the competing top-level `func main` files from the build view. Ordinary
packages and all helper files, subpackages, modules, embed assets and build
constraints are unchanged.

### Desktop (`lib/go_runner.dart` + new `lib/go_entry_selector.dart`)

- The run action removes competing package-`main` siblings via a per-run Go
  `-overlay` JSON file (`{"Replace":{<abs path>:"", ...}}`), keeping the
  existing `go run .` command and all non-entry sources.
- Ordinary single-entry packages keep the original `['run', '.']` command with
  no overlay.
- The selected source is not pre-validated for `main`; the real compiler
  diagnoses it after other mains are excluded. A helper/non-main selected source
  therefore produces a genuine nonzero compile result, never a silent fallback.
- Build constraints, `//go:embed`, module context and platform-excluded files
  are left to the compiler (verified on the real SDK).
- Overlay serialization uses `dart:convert` `jsonEncode`.
- Directory/read failures surface as real diagnostics; `competingMainSiblings`
  throws instead of silently running unfiltered.
- `build`/`test`/`fmt`/`vet`/`modTidy` semantics are untouched; they never read
  or validate the entry.
- `lib/go_entry_selector.dart` owns the comment/string/rune/raw-aware lexer.
  It reports the package clause and receiver-free top-level `func main`, so a
  `main` in another package is not treated as an entry. Method receivers, nested
  function literals, and names inside comments/literals never count.
- Overlay lifecycle has one owner: the exit future releases the temp directory
  after success or cancellation; `Process.start` failure and the outer error
  path also release it. Cancellation was restored to its original form.

### Native (`native/go_runtime/runtime.go`)

- Entry validation uses `go/parser`; a parse error in the selected source is
  returned first (exit 1), before the no-main diagnostic, so malformed code is
  not masked.
- Non-package-`main` or no-main entries return
  `no main function in <file>; cannot use it as the Go entry.` (exit 1) and never
  run another file's `main`.
- Competing siblings are detected with `go/parser` (package main + receiver-free
  top-level `func main`). A sibling that fails to parse is left in the
  interpreter view so normal diagnostics apply. A directory read error is
  surfaced.
- `projectSourceFS` grows a `ReadDir` method (satisfies `fs.ReadDirFS`, which
  `io/fs.ReadDir` prefers) that hides only the excluded competing mains in the
  selected entry directory. Imported subpackage listings are untouched. No
  vendored Yaegi API changes.

### Titles

- Native (`native_go_bridge_ffi.dart`, `native_go_bridge_stub.dart`) and desktop
  runs show a short `go run <basename(entryFile)>`. No runtime-implementation
  suffix, no Chinese run banner, no overlay path in the UI.
- Error-only `_unavailable` keeps the `Go 工具链` label.

## Files

| File | Role |
| --- | --- |
| `lib/go_runner.dart` | run overlay selection + lifecycle + titles |
| `lib/go_entry_selector.dart` | lexer, competing-sibling scan, overlay writer |
| `lib/native_go_bridge_ffi.dart` | `go run <basename>` title |
| `lib/native_go_bridge_stub.dart` | `go run <basename>` title |
| `native/go_runtime/runtime.go` | parser-based entry + filtered source view |
| `test/go_entry_selector_test.dart` | lexer + sibling + overlay unit tests |
| `test/go_toolchain_test.dart` | real-SDK coexistence integration test |
| `test/go_app_test.dart` | runner takeover / no-fallback wiring |
| `integration_test/go_native_test.dart` | mobile interpreter entry selection |
| `native/go_runtime/runtime_test.go` | native entry, no-main, parse-error, diagnostics |

Not touched: shared core, sibling apps, `lib/main.dart`, startup/config, vendored
Yaegi, `go_platform.dart`, binary libraries.

## Acceptance evidence

Desktop (`test/go_toolchain_test.dart`, real SDK go1.27.1):
- `main.go` + `main2.go` (both `func main`) + `helper.go` in one directory.
  Selecting `main.go` -> `main helper pkg asset`; `main2.go` ->
  `main2 helper pkg asset`; `main.go` again -> `main helper pkg asset` (tap /
  long-press / tap).
- `localpkg` import, `//go:embed asset.txt`, and platform-excluded `only_linux.go`
  all survive the overlay.
- Helper-as-entry: nonzero exit, no output, real compiler diagnostic.
- Malformed selected source: nonzero exit, non-empty diagnostic on stderr.
- Broken symbol: `undefined: missingSymbol` stays visible.
- Existing six-tool test and cancellation test remain green.

Native (`native/go_runtime/runtime_test.go`):
- `TestRunGoSelectsEntryWithSiblingMain`: `main.go` -> `main helper pkg`,
  `main2.go` -> `main2 helper pkg`, `main.go` again -> `main helper pkg`.
- `TestRunGoRejectsEntryWithoutMain`, `TestRunGoRejectsNonMainPackageEntry`,
  `TestRunGoSurfacesParseErrorBeforeNoMain`, `TestRunGoKeepsCompilerDiagnostics`.
- Existing multi-file, panic, os.Exit, cancellation, concurrency tests pass.

Title contract asserted inside the real integration run cases
(`integration_test/go_native_test.dart`), not a standalone FFI-load test.

## Commands and results

- Native: `go test -mod=vendor ./...` ok, `go vet -mod=vendor ./...` clean
  (`GOMAXPROCS=2`, `GOFLAGS=-p=1`, `CGO_ENABLED=0`).
- `flutter analyze --no-pub`: no issues.
- Focused Flutter suite with `QFLI_GO_TEST_EXECUTABLE` =
  `native/build/go-sdk-1.27.1/go/bin/go.exe`: 39 tests passed
  (`go_entry_selector_test`, `go_toolchain_test`, `go_app_test`,
  `go_platform_test`).
- Overlay temp directories: zero leaked after all runs.

## Review corrections applied

1. Replaced the hand-written overlay JSON encoder with `jsonEncode`.
2. Removed the `kProgramNotRunExitCode` no-main short-circuit; the compiler now
   diagnoses selected source, and native returns the real `go/parser` error
   before any no-main message.
3. Directory/read failures surface instead of silently falling back to an
   unfiltered run; malformed siblings stay in the compiler view.
4. Detection now requires package `main` plus a receiver-free top-level
   `func main`; cross-package/method/malformed regressions added.
5. Removed the brittle title-only `go_native_title_test.dart`; the concise title
   is asserted in the real integration cases.
6. Overlay cleanup has a single owner (exit future); `_cancel` is back to its
   original shape.

## Limitations / not done here

- No Android/OHOS/iOS binary rebuild or device run; Codex owns builds and device
  verification. The iOS phase consumes this source.
- No commit; review owns that.
