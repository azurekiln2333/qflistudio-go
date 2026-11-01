# Independent native epoch source review

Date: 2026-10-23, Asia/Shanghai. Reviewer: `go_independent_check`.
Active task: `10-22-go-curriculum-ohos`; dependency: `10-22-go-offline-ide`.

This is a static review of ordinary Run/Invoke ownership, debugger preparation
and shutdown, asynchronous native callback panic containment, embedded T/F/B
accounting, and weak callable registry lifetime. It is not compilation, runtime,
race, rebuilt-library, corpus or device evidence. No native source was edited by
this reviewer. Shared core and sibling products were not changed.

The implementer's initial handoff is
`debug-epoch-native-method-source-handoff-20261023.md`, with review digest
`85d2fae6e988fb59cbd9975681791897fe6da4c1da2b9778cd74bd73a5ae1a82`.
A later Python-only `audit_native.native_source_hash()` observation returned
`d887402851a8e154c19cc20e3bf776000cabc05e1052a710dfe1e8892c82ccc1`.
The source owner/coordinator were notified of this change. These identify review
inputs, not a tested release freeze; later implementation/formatting requires a
new hash. The epoch finding below refers to unchanged lifecycle code at the
listed paths and lines.

## Findings (fixed)

None in this review. No concrete mechanical/local correction was necessary.
The remaining issue requires an explicit debugger provenance/data-model
decision and product bridge changes, so it was reported before implementation.

## Findings (not fixed)

### N1 — Opaque native callbacks reuse a lexical routine, including an exited one

Severity: high. Status: source-proven; reported to the coordinator and native
source owner, who independently confirmed the gap. No reproducer was executed.

Affected files are under `native/go_runtime/`:

- `vendor/github.com/traefik/yaegi/interp/interp.go:141-155`: `frame.clone`
  copies the captured frame's `debug` pointer.
- `vendor/github.com/traefik/yaegi/interp/run.go:2031-2050,2083`: `getFunc`
  captures that clone; native invocation of the registered function enters
  `invoke(..., nil)` and prepares its debugger routine using the captured frame.
  `genFunctionWrapper` has the corresponding nil-caller path at 1053-1069,1127.
- `vendor/github.com/traefik/yaegi/interp/qfli_callsite.go:231-244`: only direct
  function arguments are wrapped with invocation-specific caller context. A
  callback stored in a native object field, such as `sync.Pool.New`, is reached
  without such an argument wrapper.
- `vendor/github.com/traefik/yaegi/interp/qfli_execution.go:188-218`: a nil
  caller on a synchronous native dispatch stack is treated as synchronous, then
  lines 199-208 select the first lexical ancestor's `debug.g`. The marker proves
  synchronous native reentry, but does not identify its actual calling routine.
- `vendor/github.com/traefik/yaegi/interp/debugger.go:291-296,399-419`: a worker's
  exit removes its routine from `gLive`. A later callback breakpoint can wait on
  that exited routine's `resume` channel, while `Continue(id)` rejects the same
  ID with `ErrNotLive`. Stop can still cancel the debugger; normal continuation
  of this breakpoint is unavailable.

A small source scenario for a later real regression is:

```go
package main

import (
    "fmt"
    "sync"
)

var pool sync.Pool

func install() {
    pool.New = func() interface{} {
        value := 7 // callback breakpoint
        return value
    }
}

func worker(done chan struct{}) {
    install()
    close(done)
}

func main() {
    done := make(chan struct{})
    go worker(done)
    <-done
    fmt.Println("ready") // stop here until worker has left gLive
    fmt.Println(pool.Get())
}
```

The harness must hold main at the indicated breakpoint until the worker has
actually exited, then resume main and inspect the callback breakpoint. This
removes timing ambiguity from `close(done)` preceding the worker's final unwind.
The callback must have a live controllable execution ID. The current path
selects the exited worker's captured ID. The inverse main-created/worker-called
case also misattributes the callback while the lexical routine is still live.
Concurrent opaque callbacks from one captured frame share a resume channel and
cannot be controlled independently.

The same missing provenance affects source stacks:
`run.go:206-207` fills a nil source stack from `newCallContext(f.anc, callNode)`.
For this opaque entry, that ancestor is lexical capture rather than an actual
native caller. It can invent parent source frames across the native boundary.

Existing `TestDebugLocalDependencyInitializerCallbackSameEpoch`
(`debugger_test.go:334`) creates its Pool callback under initializer/main
ancestry. `TestDebugNativeCallbackKeepsSynchronousThread` (357) exercises direct
sort function arguments. Neither crosses creation and calling routines through
an opaque native object.

### Decision assessment requested by the coordinator

The coordinator's proposed explicit **native callback execution routine** is a
viable fallback when actual caller provenance is unavailable. It must be a
logical debugger execution unit, labeled as such; a new ID does not establish a
physical new goroutine. Known synchronous direct contexts should keep the
actual caller ID. No stack-token encoding, TLS, goroutine ID, shared mutable
current-call slot or native object mutation is necessary for this fallback.

Required implementation properties:

1. Allocate a fresh live debug routine for each unknown-provenance entry,
   including synchronous nil-caller entries. Never select a lexical routine as
   a substitute. Concurrent entries receive independent IDs and resume state.
2. Keep **debug routine ownership** separate from **asynchronous panic
   recovery**. An unknown synchronous callback can own a logical routine while
   still propagating panic through its actual native call to interpreted
   `recover`. Only an external/asynchronous entry should recover into the
   epoch's panic channel.
3. Preserve lexical `.anc` for execution and captured variable lookup. Give the
   debug/source stack an explicit opaque native boundary. Initialize the
   callback's source frame with its own function and nil caller parent before
   `runCfg`, preventing its lexical fallback. Nested interpreted calls inside
   the callback remain traceable.
4. Publish the routine in `gLive` before events/breakpoints, remove it exactly
   once on every exit, and retain epoch ownership until removal. The current
   `execution.enter` before callback registration and deferred leave before
   `workers.Done` are useful ordering constraints. Keep main ownership until
   epoch shutdown has joined all entered callbacks.
5. Break, step and Continue target the live callback execution ID. StepOut may
   reach the opaque boundary and finish that execution; it must not invent a
   caller frame or promise a stop in an unknown native caller.
6. Suppress uncertain parent/captured scopes across the boundary. Force an
   explicit locals-unavailable reason for unknown-provenance callback snapshots
   instead of inferring safety solely from live routine count. The current
   bridge's `len(dbg.GoRoutines()) == 1` check at `debugger.go:509` is
   conservatively false for a main routine plus a logical callback, but a kind
   based policy makes the contract stable.

Data model and bridge implications:

- Vendored `debugRoutine`/`DebugGoRoutine` and stopped events need immutable
  execution kind/boundary metadata exposed to the bridge. Preserve that metadata
  in event history after the live routine disappears.
- Native `debugThread` (`debugger.go:47-50`) currently has only `id`/`paused`;
  `debugEvent` (51-58) also lacks execution kind and opaque stack boundary.
  Additive metadata can preserve the existing command ID contract.
- `lib/go_debugger.dart:366-371` currently parses only ID/paused.
  `lib/go_studio_debugger.dart:330-336` names every entry `Goroutine N`, and
  `lib/go_debugger_page.dart:340` uses `Go routine N`. These product touch points
  must label logical native callback executions honestly and preserve boundary
  information. The existing shared `DebugThread.name` can carry the label; this
  does not by itself require changing shared-core interfaces.
- Update `.trellis/spec/backend/native-go-runtime.md:195-207,256-260` if this
  decision is accepted. Its current contract says events report actual threads
  and every synchronous reentry keeps its calling thread; distinguish proven
  direct caller identity from explicit opaque callback execution units.

Meaningful missing regressions, after the decision and another resource grant:

- Worker creates Pool.New, exits, and main later calls Get: breakpoint ID is
  live; step/Continue work; no exited lexical ID or fictional parent frames.
- Main creates Pool.New and a worker calls Get: correct explicit kind/boundary,
  safe locals behavior and no reuse of main's pause/resume state.
- Two simultaneously entered opaque callbacks sharing a lexical origin: two
  distinct controllable IDs, independent snapshots and resumes, real completion
  after both leave, and no stale paused entries.
- Nested source calls, direct/deferred sort callbacks, and nested native reentry:
  preserve proven direct caller identity; opaque stacks stop honestly at their
  boundary; stepOut has defined behavior.
- A synchronous opaque callback panic is recoverable by its interpreted caller;
  an asynchronous one fails the owning epoch without escaping the host.
- Blocked opaque callbacks keep Stop/Close pending until actual release;
  retained calls after epoch closure are rejected without new live routines.
- Run the race detector on the real concurrent controls and closure retention
  cases, rather than relying on static reasoning or thread-count assertions.

## Source paths reviewed without another independent finding

- `EvalPathWithContext` and `InvokeWithContext` use `executeWithContext`.
  `executionEpoch.enter` and `stop` serialize registration under one mutex;
  shutdown closes registration before waiting. `startGoroutine` reserves its
  worker token before scheduling. Entered callback wrappers release their
  ownership after recovery/debug cleanup. Closed epochs reject retained
  wrappers before interpreted execution.
- `executionEpoch.evaluate` waits for its main execution goroutine after a
  context cancellation or transferred native panic, then deferred `close` joins
  entered workers. Normal return starts shutdown rather than waiting for future
  unscheduled timers. A compiled blocking call can correctly delay completion.
- `DebugPath` attaches the debugger before imported-source initialization and
  preserves the same epoch through import preparation, entry barrier and entry
  execution. The new `Debugger.start` reset of `mainG.running` matches the
  initial barrier's stopped state.
- Vendored debugger completion waits for epoch close before removing main and
  waiting for all live debug routines. Product `closeGoDebug` waits for
  `session.done` before registry removal; `debugSession.run` defers real
  `Terminate`/`Wait`. It does not replace pending native cleanup with early
  synthetic closure.
- Asynchronous callback panic recovery records the epoch failure before
  returning the wrapper. T/F body and cleanup adapters inspect
  `ExecutionError` during unwind; benchmark guards do so for bodies, cleanups,
  subbenchmarks and RunParallel bodies. Final benchmark failure is inspected
  after native cleanup. The new body/cleanup/benchmark timer cases still need
  actual execution to establish accounting behavior.
- The callable registry stores hash buckets of weak binding pointers. The
  returned wrapper owns its binding strongly, and weak lookup promotes the
  binding while the input callable is kept alive. Periodic pruning removes
  dead entries; a registry key does not strongly retain an abandoned function.
  The existing two-wave finalizer/native-retention test is relevant evidence to
  obtain, not evidence supplied by this review.

These are source observations, not assertions that the unexecuted repairs pass
compilation or their behavioral tests. Promoted native method-expression work
is being reviewed/owned separately and is not closed by this epoch report.

## Verification

- Lint/formatting: **not run**. No Go or gofmt command is permitted in the
  current resource state. Scoped `git diff --check -- native/go_runtime` passed
  with only existing LF/CRLF conversion warnings; this is whitespace inspection,
  not Go lint.
- TypeCheck: **not run** after the handoff repairs.
- Tests: **not run** after the handoff repairs. Prior focused native process
  `85731` exited **1**, with four failing assertions preserved in
  `native-review-repair-focused-20261023.log`. Later source edits do not turn
  that failed checkpoint into a pass.
- Hash: Python-only `audit_native.native_source_hash()` was observed as above.
  It includes native tests and must be recomputed after any new edits/gofmt.
- Runtime, Linux race, rebuilt ABI/FFI, corpus, real package/signature and actual
  OHOS execution gates remain open. Full product/curriculum completion is not
  claimed.

### Planned commands — explicitly unexecuted

Go236 was released at global sequence 287. A later named resource grant is
required before running any of these commands. Follow
`native-final-validation-plan-20261023.md`; use process-local `GOMAXPROCS=2`,
`GOFLAGS=-p=1`, `GOMEMLIMIT=512MiB`, `GOGC=20`, `GOTOOLCHAIN=local`,
`GOWORK=off`, `GOENV=off`, `GOPROXY=off`, `GOSUMDB=off`, and the existing
compiler wrapper. Format only owned changed Go files first and record their
new digest. Then run serially from the repository root:

```powershell
& ./native/build/go-sdk-1.27.1/go/bin/go.exe -C native/go_runtime test -mod=vendor -count=1 -timeout=90s -v ./...
& ./native/build/go-sdk-1.27.1/go/bin/go.exe -C native/go_runtime vet -mod=vendor ./...
```

Do not substitute `^TestDebug` for full `./...`: ordinary callback panic
containment, Helper GC, T/F/B/cleanup accounting, benchmark skip and generic
native method regressions are part of acceptance. Preserve stdout/stderr,
terminal handle/PID, actual exit and elapsed time, and compare hashes before and
after execution. Inspect platform skips.

Under a separate later WSL grant, the already prepared distro/SDK can run the
real race gate (also full suite, with the same offline/memory limits):

```powershell
wsl.exe -d qfli-java-build --cd /mnt/d/MyNewProjects/qfli_go/native/go_runtime -- env GOROOT=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go GOMAXPROCS=2 GOFLAGS=-p=1 GOMEMLIMIT=512MiB GOGC=20 GOTOOLCHAIN=local GOWORK=off GOENV=off GOPROXY=off GOSUMDB=off CGO_ENABLED=1 /mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go/bin/go test -race -mod=vendor -count=1 -timeout=180s -v ./...
```

Never shut down another product's WSL distribution. After passing source checks,
recompute matching digests, rebuild the current DLL and all five Android/OHOS
libraries, and repeat actual FFI/corpus/archive/device gates. None was run here.
