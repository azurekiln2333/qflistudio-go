# Pi w8:p5 — Go terminal/runtime audit (pi-terminal)

Owner: Herdr pane `w8:p5`, cwd `D:\MyNewProjects\qfli_go`.
Parent task: `10-15-release-integrity-audit`.
Related: `10-09-terminal-flow-pi` (Go entry/runtime fixes, retained and re-verified).

## Scope

Trace the real shell delegate flow for the standalone terminal page and the
editor `TerminalPane`; check `lib/main.dart`'s `goProfile` for a missing
`terminalCommandDelegate`; verify Go run/build/test/fmt/vet/mod, version, help,
failure diagnostics, cancellation and project paths. Fix missing routing and
incomplete methods; promise only what the embedded interpreter really supports on
mobile; reuse `GoToolchain` on desktop. No empty implementations.

## Findings

### F1 — `goProfile` was missing `terminalCommandDelegate` (real defect)

Both terminal surfaces read `StudioProfile.current?.terminalCommandDelegate`:

- `../qfli_studio_core/lib/editor/terminal_pane.dart:440`
- `../qfli_studio_core/lib/pages/terminax_terminal_page.dart:42,109`

`goProfile` never set it, so every `go ...` line typed in either terminal fell
through `SandboxShellBackend.runExternal` to the "内置终端不支持该命令" branch,
even though the Go toolchain and the mobile interpreter were already wired for
the Run button. Java (`qfli_java/lib/main.dart`) already installs a delegate;
Go had no equivalent.

### F2 — no Go terminal command routing existed

There was no `GoToolchain` method to run a raw `go <args...>` command in the
shared sandbox cwd, and no delegate factory. `GoToolchain.execute` is
action-based (it rewrites package selection for `run`), which is right for the
Run button and wrong for a faithful terminal prompt.

## Fixes

- `lib/go_runner.dart`: added `GoToolchain.runTerminalCommand({workingDirectory,
  arguments})`. Streams a raw `go <args...>` in the given cwd with the real SDK.
  Returns `null` when the platform has no official SDK so the caller reports an
  honest boundary. Reuses `_lines`/`_cancel`. `execute()` unchanged.
- `lib/go_terminal_delegate.dart` (new): `goTerminalCommandDelegate` +
  `GoTerminalDelegate`. Classifies/tokenizes with `CommandParser`
  (`EscapePolicy.backslashLiteral`, matching the sandbox) so quoted operands
  survive and compound lines (pipe/redirect/chain/glob) fall back to the sandbox
  instead of being misread as Go arguments.
  - Desktop (`officialSdk`): forwards the whole line to the SDK in `backend.cwd`.
  - Mobile (`embeddedInterpreter`): claims only `go run <single file|dir>` via the
    same `GoProgramRunner` the Run button uses. Refuses `go build/test/fmt/vet/
    mod`, bare `go` and `go run` with flags/patterns with an honest message and
    `kProgramNotRunExitCode` — never an empty success.
  - `unavailable`: honest "no Go runtime" refusal.
- `lib/main.dart`: one import + `terminalCommandDelegate: goTerminalCommandDelegate`
  on `goProfile` (only the allowed profile field).
- `test/go_terminal_delegate_test.dart` (new): profile wiring; desktop
  version/help/run single+multi-file/real compile error/test; cd-aware cwd;
  running-program cancellation; non-go + compound non-claim; mobile capability
  refusals; and both terminal contexts (`TerminaxTerminalPage` + `TerminalPane`).

## Verification

Commands (all from `D:\MyNewProjects\qfli_go`):

- `QFLI_GO_TEST_EXECUTABLE=D:\MyNewProjects\qfli_go\native\build\go-sdk-1.27.1\go\bin\go.exe`
- `flutter analyze --no-pub lib/go_runner.dart lib/go_terminal_delegate.dart lib/main.dart test/go_terminal_delegate_test.dart` → No issues found.
- Existing focused Go suite (10-09 work retained): `go_entry_selector_test.dart` +
  `go_app_test.dart` + `go_toolchain_test.dart` → **45 passed**, exit 0.
- `native/go_runtime`: `go test -mod=vendor -count=1 ./...` → ok, exit 0;
  `go vet -mod=vendor ./...` → exit 0.
- `GOMAXPROCS=2 GOFLAGS=-p=1 GOTOOLCHAIN=local` with the pinned Windows SDK and
  `GOCACHE=native/build/go-cache-windows`.

## External blocker (not my file)

`../qfli_studio_core/lib/editor/editor_page.dart:1605` had a syntax error
(missing comma after the Git `PopupMenuItem(...)` before
`if (widget.project.isCloud && ...)`) while it was being edited by the
offline-editor-gates owner. That broke compilation of every Dart test importing
`editor_page.dart`, including the new delegate test. Shared core is out of my
write scope; reported to the coordinator (`w8:p1`) and left untouched.

Also reported: `test/go_offline_profile_test.dart` (Pi3-owned) has 2 analyzer
errors (`ProfileTab` undefined; non-nullable body completion) and 3
`depend_on_referenced_packages` infos.

## Reported to coordinator

Sent to `w8:p1` at the time of the first fix. Suggested commit:

    fix(go): install Go terminal command delegate for both terminals
    files: lib/go_runner.dart lib/go_terminal_delegate.dart lib/main.dart test/go_terminal_delegate_test.dart

## Coordinator review round (all 5 items addressed)

1. **Bare `go` on desktop** — `runTerminalCommand` no longer rejects an empty
   rest; a bare `go` is forwarded to the real SDK (help on stderr, exit 2, status
   preserved). Regression added.
2. **Bare `go` on unavailable targets** — restructured so the delegate switches
   on the backend first; `unavailable` reports "没有可用的 Go 运行时" for bare
   `go` and subcommands alike instead of returning false.
3. **Mobile operand path** — uses `backend.resolveSandboxPath(operand)` so the
   sandbox boundary rules apply; an escape is reported via
   `SandboxEscapeException` as a terminal error, never an uncaught exception.
   `projectPath` is now `backend.sandboxRoot` (the interpreter's confining root),
   and a directory operand resolves through `RunnerService.findEntry`, matching
   the editor Run button (configured entry, then profile entry names).
4. **Real-FFI integration coverage** — added to `integration_test/go_native_test.dart`:
   `SandboxShellBackend(delegate: goTerminalCommandDelegate)` driven with
   `go run <file>`, `go run <dir>`, a helper-as-entry compile error, an
   unsupported subcommand refusal, and a running-program interrupt. Uses the
   real embedded interpreter through FFI; gated on the embedded backend so it
   only runs on Android/OHOS/iOS.
5. **Command name matching** — replaced `basenameWithoutExtension == 'go'` with
   an exact `go` / `go.exe` match, so `go.txt` / `go-land` are no longer claimed.
   Regression added.

Additional real defect found while adding coverage: the test capture backend
originally drained stdout fully before stderr, which deadlocked a process that
fills the stderr pipe (bare `go`). The **shared** `SandboxShellBackend.runStreams`
already drains concurrently, so the product was safe; the test harness was fixed
to drain both pipes concurrently.

### Verification after review round

- `flutter analyze --no-pub lib/ test/go_terminal_delegate_test.dart integration_test/` → No issues found.
- `test/go_terminal_delegate_test.dart` → **25 passed** (0 skipped with the SDK).
- Go suite (`go_terminal_delegate_test` + `go_entry_selector_test` +
  `go_app_test` + `go_toolchain_test`) → **70 passed**.
- Shared terminal/editor: `terminal_pane_test.dart` + `editor_run_test.dart` →
  **41 passed**; `terminal_manager_delegate_test.dart` + `sandbox_terminal_test.dart`
  → **26 passed**.
- `native/go_runtime`: `go test -mod=vendor -count=1 ./...` → ok; `go vet -mod=vendor ./...` → clean.

### main.dart unchanged beyond the delegate

`git diff -- lib/main.dart` confirms the only additions are
`import 'go_terminal_delegate.dart';` and
`terminalCommandDelegate: goTerminalCommandDelegate`. The `flutter/services.dart`
import and the whole startup refactor are pre-existing 10-09 work, not mine.

## Native Yaegi build-constraint fix (reviewer finding)

### Defect (real mobile compatibility)

`native/go_runtime/vendor/github.com/traefik/yaegi/interp/build.go` `buildLineOk`
only recognized the legacy `// +build` syntax (`line[:7] == "+build "`). A
selected `selected.go` gated by the modern `//go:build qfli_never_enabled` was
therefore silently included; with another `other.go` main present, the mobile
`runGo` wrongly executed SELECTED with exit 0. Official Go excludes the file.

### Fix (in the owning vendor filter, no second source-filter layer)

- `interp/build.go`: `buildOk` now calls `buildConstraintsOk`, which reads the
  raw `ast.Comment` lines (retaining the `//` marker) and evaluates via
  `go/build/constraint`:
  - `//go:build` expressions (`constraint.IsGoBuild` + `Parse` + `Expr.Eval`),
    taking precedence when both syntaxes are present. The final independent
    review additionally made duplicate modern directives an explicit error and
    ignored directive-like text inside block comments (see independent-review.md).
  - legacy `// +build` lines through `buildPlusLineOk`, preserving the original
    OR-of-space-options / AND-of-comma-tags semantics and the `go1.x` release-tag
    comparison (`buildOptionOk`/`buildTagOk`/`goMinorVersion` unchanged).
  - an unparsable expression is returned as an error (diagnostic), not silently
    included or excluded.
  - `yaegi:tags` handling unchanged.
- Removed the now-dead `buildLineOk`; `buildPlusLineOk` is the single legacy path.
- `native/go_runtime/README.md` documents the vendor patch for the next
  `go mod vendor` refresh.

### Regression tests (native, real interpreter)

`native/go_runtime/runtime_test.go` additions:

- `TestRunGoRejectsModernBuildTaggedEntry` (3 subtests) — the exact reported
  case: modern-tagged selected file + sibling main must not execute SELECTED or
  OTHER and must fail with a diagnostic.
- `TestRunGoExcludesModernTaggedHelper` — a modern-tagged helper stays out of
  the package view; the selected main surfaces the undefined-symbol diagnostic.
- `TestRunGoExcludesModernTaggedImportedSource` — a modern-tagged source inside
  an imported subpackage stays out (covers the reviewer's retained/imported note).
- `TestRunGoAcceptsEnabledModernBuildTag` — a satisfied `//go:build` includes
  the file (no over-exclusion).
- `TestRunGoAcceptsLegacyPlusBuildTag` — legacy OR/AND semantics preserved.
- `TestRunGoPrefersModernBuildExpression` — both syntaxes present, consistent pair.
- `TestRunGoReportsInvalidBuildExpression` — invalid expression yields a real
  `unexpected token` diagnostic, no SELECTED output.

### Verification

- `go test -mod=vendor -count=1 ./...` in `native/go_runtime` → **26 passed,
  0 failed, 0 skipped** (GOMAXPROCS=2, GOFLAGS=-p=1, GOTOOLCHAIN=local,
  GOCACHE=native/build/go-cache-windows, GOROOT unset, pinned SDK 1.27.1).
- `go vet -mod=vendor ./...` → clean; `go fmt -mod=vendor ./...` → no changes.

### Files (this fix)

- `native/go_runtime/vendor/github.com/traefik/yaegi/interp/build.go`
- `native/go_runtime/runtime_test.go`
- `native/go_runtime/README.md`

`native/go_runtime/runtime.go` was NOT touched in this round; its diff is the
pre-existing 10-09 work. Main owns the five-library rebuild.

### Independent review alignment

The reviewer's P1 (`research/independent-review.md`) required: read the modern
instruction from the raw `ast.Comment.Text` because `CommentGroup.Text()`
strips `//go:build`; reuse `go/build/constraint.Parse` + `Eval` with the existing
`buildTagOk`; keep the modern expression authoritative over legacy `// +build`.
The fix implements exactly that. The reviewer confirmed the terminal Dart code
has no other substantive defect.

## Integration interrupt test fix (device-buffering defect)

`integration_test/go_native_test.dart`, only the
`terminal delegate interrupts a running go run program` case, was rewritten:
the native bridge buffers stdout until completion, so waiting for a `running`
line before interrupting a 30s-sleep program could only time out. The program
now writes an absolute-path marker file after entering `main` and then loops;
Dart polls the marker with an explicit 30s deadline, calls `backend.interrupt()`,
awaits `backend.execute`, and asserts the `^C` line and `lastExitCode == null`.
The marker path is embedded with `jsonEncode` as a Go interpreted-string literal
so device paths with separators/non-ASCII survive. A throwaway host probe ran the
same source through the SDK and confirmed marker-write, interrupt, `^C`, and a
null status; it was deleted afterward. No other integration test waits on
streaming stdout (they await `exitCode`/`execute` completion first). This file is
frozen for the coordinator's device run.
