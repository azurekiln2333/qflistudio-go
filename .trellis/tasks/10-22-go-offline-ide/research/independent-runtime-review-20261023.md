# Independent runtime and Dart review

Reviewed 2026-10-23 by the dispatched `trellis-check` agent. Active task:
`.trellis/tasks/10-22-go-curriculum-ohos`; implementation dependency:
`10-22-go-offline-ide`.

The original attachment, task PRDs/designs/implementation plans, check contexts,
native implementation handoff and current source files were read. The review
preserves the complete standalone-product goal. It does not accept a passing
host corpus as proof of OHOS execution or teaching fidelity.

## Scope and verification status

- Reviewed current native run/test/analysis/debugger/project-environment paths,
  relevant vendor frame/call/cancellation changes, Dart FFI/result decoders,
  Go runner/terminal, shared debugger adapter and profile registration.
- Native source was frozen at the handoff digest
  `7de8ef14fd57854cf1247d406ef76dc02bd39dbf6618832ec5f4959b85f8450b`.
  The checker made no native, Dart, shared-core, corpus or platform-config edit.
  Source/build digests must be recomputed after the implementation repairs below.
- `git diff --check` passed for the changed tracked runner/bridge/profile/terminal
  Dart files. The messages about future CRLF conversion are Git notices, not
  whitespace failures.
- Lint/type-check/tests were **not run in this review**. The coordinator explicitly
  reserved the host build/test queue and requested read-only/static review.
  The prior handoff's test results are historical evidence, not checker results.
- Findings below distinguish source-proven missing behavior from runtime shapes
  that still require the proposed focused regressions. No reproduction output is
  invented. Findings were sent to the coordinator before any native mutation.

## Findings (fixed)

None. Native source freeze and ownership were respected; the fixes need native
implementation decisions rather than a mechanical local Dart edit.

## Findings (not fixed)

### P1 — T106's central Helper behavior is absent

Files and evidence:

- `tool/go_curriculum/topics/T106.json:20–46` explicitly teaches `t.Helper`
  moving assertion failure attribution from the helper body to its caller.
  The title, summary, objective, pitfall and explanation all depend on this.
- `native/go_runtime/embedded_testing.go:77` implements `Helper()` as an empty
  method. `Logf` at line 81 only writes the test name and message; no interpreted
  source file/line is observed at all.
- `embedded_testing_test.go` covers original T080/T104/T105/T107/T108/T110/T119,
  but no negative-path Helper attribution case. T106's all-success example can
  pass its genuine assertions without ever exercising the lesson's main claim.
- The spec currently accurately documents the no-op. That documentation cannot
  substitute for the original lesson's required behavior.

Minimal regression:

```go
package helpercheck
import "testing"
func assertReady(t *testing.T) { // helper declaration
    t.Helper()
    t.Fatal("not ready") // must not be the attributed failure line
}
func TestCaller(t *testing.T) {
    assertReady(t) // expected failure attribution
}
```

Run both with and without `t.Helper`. Require a real nonzero result and actual
file/line attribution; with Helper it must point to `TestCaller`'s call, without
Helper to the failing helper-body call. Merely seeing `PASS`, test counts or the
word `TestCaller` does not prove it.

Recommended implementation: preserve interpreted function identity and call
position in frame metadata using `runCfg(funcNode, callNode, f)` and copy it
through frame/closure creation. At native method invocation, pass an immutable
interpreted source stack to a narrowly scoped per-interpreter receiver hook for
embedded T/F/B. Helper records the interpreted function identity; diagnostics
select the first unmarked caller. `runtime.Caller` sees reflect/host frames and
cannot supply this behavior. Avoid global current-call state or runtime goroutine
ID tricks: two independent tests/contexts must not exchange attribution.

Cover nested helpers, anonymous/subtest functions, method values, variadic calls,
deferred failures, multiple T instances and actual Unicode source filenames. The
existing DebugFrame source-position machinery is a reference, but enabling a
debugger merely to record test callers introduces unnecessary pause/lifecycle
state. This needs a native implementation and focused regressions, so the checker
did not silently change it under the source freeze.

### P1 — DebugPath ends the dependency initialization epoch before debugging

Files and source trace:

- Vendored `interp/debugger.go:818` wraps package compilation in
  `debugExecuteContext`; GTA/import resolution can execute local source package
  initialization through `importSrc`.
- Vendored `interp/src.go:154–170` actually executes imported roots, global
  initializers and init functions.
- `debugExecuteContext` calls `stop()` at `debugger.go:973`; `stop` increments the
  interpreter run ID and closes its context (`interp.go:658`).
- `DebugPath` then starts a second `debugExecuteContext` at `debugger.go:897` for
  entry execution. A closure created by a dependency initializer has captured its
  earlier frame/run ID (`run.go:2009,2014`). That frame was also created before
  the debugger attached, so its debug metadata may be nil when used later.
- The current multi-file debugger regression imports only compiled stdlib
  packages; it does not exercise a local dependency's initializer-created
  closure. This resembles the already-repaired test-engine epoch defect.

Minimal regression project:

```go
// src/localpkg/pool.go
package localpkg
import "sync"
var Pool = sync.Pool{New: func() any { return "ready" }}
```

```go
// src/main.go
package main
import ("fmt"; "qfli-project/src/localpkg")
func main() { fmt.Println(localpkg.Pool.Get()) }
```

Require both ordinary Run and actual Debug/Continue to print `ready` once and
terminate successfully. The static review proves the split and captured-frame
invalidation; the exact current failure shape (skipped callback or nil debug
metadata panic) must be captured by the regression, not assumed.

Recommended fix: give import preparation and subsequent debug execution one
continuous owned evaluation epoch. Preserve cancellation during compilation and
dependency init, preserve stop-on-entry semantics for the entry package, and
avoid blindly rebinding all captured frames to a new epoch. A context must not be
stopped between initialization and callbacks that belong to that execution.

### P1 — Compiled-library callbacks bypass debug worker ownership

Files and source trace:

- `interp/interp.go:568` tracks interpreted `go` launches with a token acquired
  before scheduling. This repairs the explicit `go` statement race.
- `interp/run.go:2012–2040` creates a reflected callback which enters `runCfg`
  directly; a compiled library invoking that callback from its own goroutine
  does not go through `startGoroutine`.
- `interp/debugger.go:289–318` gives it the captured frame's debugger routine and
  creates a distinct routine only when the AST call is directly under a
  `goStmt`. A timer or HTTP-library callback has no such AST parent.
- Consequently `activeWorkers` and `gLive` do not establish ownership of that
  callback. `native/go_runtime/debugger.go:509` also uses `len(GoRoutines())==1`
  as permission to read locals, which does not account for these callbacks.

Extend `TestDebugStopAndCloseWaitForBlockedNativeWorkers` with:

```go
time.AfterFunc(0, func() { http.Get(serverURL) })
select {}
```

As in the existing test, the host HTTP handler signals that the request entered
and holds it until a release channel closes. After entry and before release,
Stop/Close must remain pending, the session must remain owned, and terminal state
must not be fabricated. Only release the server after checking those assertions.
The existing regression covers direct main and interpreted `go func` HTTP calls,
not a native-library-created callback. This additional runtime case was not run
by the checker because of the resource reservation.

Recommended fix: use an epoch-owned callback-registration gate at external
native-to-interpreted callback entry. Registration and shutdown must synchronize:
shutdown closes registration before waiting, callbacks already entered retain
their tokens, and late callbacks from an obsolete epoch do not execute user code.
Just calling `WaitGroup.Add` on callback start leaves an Add-after-zero-Wait race.
Distinguish synchronous reentrant callbacks from genuinely concurrent execution
for thread identities/locals, while retaining actual active-callback ownership.

### P2 — The exported EvalSymlinks changes relative-return semantics

File: `native/go_runtime/project_environment.go:104`.

The wrapper always resolves a nonempty relative path to an absolute path before
calling `filepath.EvalSymlinks`, so even an existing ordinary `data/file.txt`
returns an absolute result. The pinned SDK's `path/filepath/path.go:143–149`
documents that a relative input stays relative unless an absolute symbolic-link
component makes the result absolute. This is behavior of an explicitly adapted
export, not a request for additional OS isolation.

Add an actual interpreted regression for a relative regular path, a relative
symlink and an absolute-target symlink (where the host can create them), from an
entry cwd different from host cwd. Preserve both correct lookup and the official
result shape. The current project-environment tests cover Abs/Glob/WalkDir but
not this export. The fix needs to preserve whether absolute symlinks were crossed;
unconditionally relativizing the final absolute result is also insufficient.

### P2 — Unix SDK cancellation only kills the go parent

File: `lib/go_runner.dart:302–320`.

Windows uses `taskkill /T /F`. Linux/macOS execute only `process.kill()` followed
by the go parent's exit future. That does not establish that the compiled child
of `go run` or a test binary has exited. The local pinned SDK's
`cmd/go/internal/base/signal_unix.go` handles SIGINT/SIGQUIT, not SIGTERM (Dart's
default kill signal). A child can retain stdout/stderr and keep running after
the go parent is gone.

The existing SDK cancellation regression correctly waits for both pipes, but
the handoff's Windows execution does not establish this Unix behavior. Reuse an
owned process-group/supervisor abstraction with a real Unix regression; do not
enumerate or kill unrelated system processes. This is a cross-module/process
ownership design choice, so it was reported rather than silently patched in a
read-only native review. It predates the current changes but remains contrary
to the entry-selection spec's process-tree cancellation contract.

## Paths checked without a new defect

- Analyze/Format use parser/AST/formatter packages against supplied source, not
  interpreter evaluation. Native `filePath` is not opened. Dart validates the
  schema, source identity, UTF-16 length/ranges and surfaces unavailable results.
- The selected `_test.go` path calls the embedded engine, which returns typed
  counts. Its initialization/discovery/test callbacks share one InvokeWithContext
  epoch. Fatal/Skip and assertions are not replaced by printing a pass string.
- Normal native result decoding is shared by the raw audit and ProgramRunResult
  adapter, with the same cancellation handle and C string release path.
- StudioProfile registers GoCodeAnalyzer and GoStudioDebugger. The debugger
  adapter rejects unsupported unsaved snapshots, validates physical project
  paths, rejects stale pause tokens, increments output revisions and waits for
  native close before completing done/dispose. Its correctness still depends
  on the missing native callback ownership and continuous epoch above.
- Project filesystem exports are finite adapters, not a sandbox. Compiled
  stdlib relative-file internals and native File.Chdir remain documented limits;
  no speculative general OS sandbox was requested by this review.

## Release consequences

Keep the native and OHOS gates open. Repair P1 findings, add the focused actual
regressions, repeat full native tests/vet and relevant Dart checks, then rebuild
all matching libraries before actual FFI/corpus/package/target acceptance.
T106 also requires negative-path semantic evidence beyond the existing
all-success corpus transcript. No host success, spec disclaimer or build artifact
alone closes those gates.
