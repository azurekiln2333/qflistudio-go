# Debugger lifecycle review repair

Follow-up to the independent runtime review, 2026-10-23. Active task:
`10-22-go-curriculum-ohos`; implementation dependency: `10-22-go-offline-ide`.
The old native handoff digest predates these changes. No bundled-library or
device evidence is attributed to the current source until it is rebuilt.

## Change boundary

Two missing ownership boundaries caused the P1 findings: DebugPath stopped the
interpreter after dependency initialization, and compiled libraries could enter
interpreted callbacks without joining the debugger's owned workers or live
threads. The repair lives at evaluation and native-to-source invocation entry.
It preserves the selected project, entry-package pause, imported initialization
semantics, native blocking IO behavior and existing debugger protocol.

### Expanded ordinary Run/test boundary

The coordinator explicitly included the same callback ownership defect in
ordinary Run and embedded tests after static review showed that their
EvalPathWithContext/InvokeWithContext paths did not install an epoch. A timer
callback panic therefore had no owned recovery boundary. The shared epoch owner
will also cover these two context methods, retaining one epoch for test package
initialization and all test callbacks. Normal main return still initiates
shutdown immediately: it does not wait for future timers or keep interpreted
workers running. Shutdown closes entry, cancels interpreted execution, and waits
only for actual entered work to leave. Already entered blocking compiled calls
can delay completion until they return; future/retained callbacks are rejected.

This requires the epoch owner and callback panic classification to work without
an attached debugger. It changes no exported ABI, selected-entry policy,
curriculum source or test discovery. New ordinary regressions will use an
isolated test subprocess for panic containment, an actual retained native
callback for late-entry rejection, and a held HTTP callback for cancellation
and normal-main-return cleanup. The coordinator retains ownership of product
FFI and target rebuild acceptance.

## Implementation

- `interp/qfli_execution.go` owns a continuous execution epoch. Entry and
  shutdown share a mutex-protected registration gate; shutdown closes that gate
  before Wait. Tokens cover callbacks already executing and workers reserved
  before scheduling. Closed-epoch callbacks return zero values without entering
  user code. Panics from external callbacks reach the epoch's panic channel.
- `interp/debugger.go` attaches root debug ancestry before source imports.
  Dependency preparation, the entry pause and entry execution share that epoch.
  Actual evaluation and callback completion precede the terminal event and Wait.
  Dependency preparation runs without entry stops; entry globals/init/main stay
  deferred until the debugger resumes. Missing program metadata is tolerated by
  DebugFrame.Program when imported frames have no entry Program association.
- `interp/interp.go` reserves an epoch token before an interpreted goroutine is
  launched. Its worker defer always releases the token. EvalPathWithContext and
  InvokeWithContext share that epoch owner, reset the root cancellation frame,
  close registration before waiting and report external callback panics.
- `interp/qfli_test_context.go` provides the marker-only RunNativeCallback
  boundary used by embedded T and B adapters. Synchronous test-body/cleanup and
  benchmark panics continue into the adapter's existing per-test recovery rather
  than being swallowed by the asynchronous callback panic channel. Native
  timers launched by those bodies have no synchronous dispatch marker and still
  report through the epoch.
- `interp/run.go` getFunc and genFunctionWrapper register callbacks with the
  source-call bridge, retain their creation epoch, acquire callback tokens and
  initialize source/debug frames before runCfg. Existing closure bindings,
  receivers, variadic inputs and return-slot behavior remain intact.
- Explicit callback invocation metadata comes from the native-analysis owner's
  `qfli_callsite.go` bridge. Synchronous native reentry keeps its actual calling
  debug thread; an external callback or interpreted go function-value call gets
  a live thread of its own. A noinline native dispatch function is identified by
  its function entry PC on the current host stack. No goroutine ID or mutable
  global current-call slot is used. Native structs which hold a source function
  without an argument wrapper use captured ancestry for synchronous reentry.
- `.trellis/spec/backend/native-go-runtime.md` records the epoch, registration,
  thread and regression contracts.

The native-analysis owner separately owns runCfg/call/callBin/native methods,
source-frame fields, Helper diagnostics, symlink behavior and weak function
registry leases. Shared edits must be kept together. Static review identified
that callBin defers also need the bridge, so a deferred sort.Slice regression
checks this boundary alongside the direct form.

## Meaningful regressions

`native/go_runtime/debugger_test.go` now includes:

- Real module dependency `sync.Pool.New` created by initialization: ordinary Run
  and Debug/Continue must both print `ready` once; no entry output before resume.
- A held HTTP call entered by main, interpreted go, time.AfterFunc literal and
  time.AfterFunc named function: asynchronous workers must appear in live
  threads; Stop/Close remains pending and registered until the server releases.
- Direct and deferred sort.Slice callbacks with a real breakpoint: exactly one
  live thread, with the original main thread ID and correct final sorted output.
- A native library retaining a source callback: after actual Debugger.Wait,
  invoke it concurrently 32 times and require zero user callback side effects
  and no resurrected live threads.
- A timer callback panic: return a real failed debug result without escaping
  into the host process.

## Validation status

Source formatting and focused `git diff --check` passed. Go compilation,
focused regressions, full native tests/vet and Linux race checks are pending the
coordinator's explicit host resource slot. No passing execution result is
claimed here yet.

Focused command in `native/go_runtime`, with the pinned Windows SDK and local
process settings `CGO_ENABLED=0`, `GOTOOLCHAIN=local`, `GOMAXPROCS=2`, `GOFLAGS=-p=1`:

```powershell
& ../build/go-sdk-1.27.1/go/bin/go.exe test -mod=vendor -count=1 -timeout=90s -run '^TestDebug' .
```

The real race command uses the already prepared Linux SDK and existing WSL
distribution. It must share the same coordinator resource queue and never
shutdown another product's distribution:

```powershell
wsl.exe -d qfli-java-build --cd /mnt/d/MyNewProjects/qfli_go/native/go_runtime -- env GOROOT=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go GOMAXPROCS=2 GOFLAGS=-p=1 GOTOOLCHAIN=local CGO_ENABLED=1 /mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go/bin/go test -race -mod=vendor -count=1 -timeout=90s -run '^TestDebug' .
```

After source checks pass, recompute native digests and rebuild the corresponding
host and all five Android/OHOS libraries. Run actual Dart FFI, corpus, package
inspection and OHOS target gates with the new hashes. Those steps are owned by
the coordinator, and are not replaced by source review or host Go tests.
