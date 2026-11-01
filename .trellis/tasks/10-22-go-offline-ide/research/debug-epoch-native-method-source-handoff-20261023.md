# Debug epoch and native method source handoff

Date: 2026-10-23. Active task: `10-22-go-curriculum-ohos`; dependency:
`10-22-go-offline-ide`. Implementer: `go_debug_repair`.

This is a source handoff, not repaired-runtime evidence. The coordinator's first
combined focused run compiled but exited 1, retaining four failing assertions
in `native-review-repair-focused-20261023.log`: Debug local-import Pool.New
returned `running`; Helper method-value and method-expression cases failed
compilation; deferred method-value failed reflected assignment. That failed
report is unchanged. The Go236 resource slot was explicitly released at global
sequence 287; no test, build, vet, Flutter or WSL process was started by this
implementer after that release. No source digest or library is frozen here.

## Repaired source

- `vendor/github.com/traefik/yaegi/interp/debugger.go`: `Debugger.start` now resets
  `mainG.running=false` when arming the initial entry barrier. Import preparation
  already runs with the debugger attached in the same epoch; it can leave the
  main routine running even after its evaluation returns. Merely changing mode
  to DebugEntry made the bridge's initial Step fail with ErrRunning.
- `vendor/github.com/traefik/yaegi/interp/type.go`: `nativeSelectorType` models the
  actual callable value before inference and checking. Bound concrete methods
  omit the reflected receiver; concrete method expressions retain it; reflected
  interface methods already omit it, while their expressions add the explicit
  interface receiver. Normalized selector values no longer need the historical
  isBinMethod assignment shortcut or receiver-offset argument inference.
- `vendor/github.com/traefik/yaegi/interp/cfg.go`: native selectors use that same
  callable signature during CFG compilation. Native type selectors produce
  actual method-expression values. Bound selectors clear redundant receiver
  metadata because their runtime reflected Values are already bound. The prior
  source-method expression/cached-signature changes are preserved.
- `vendor/github.com/traefik/yaegi/interp/qfli_callsite.go`:
  `nativeMethodExpression` registers the explicit-receiver callable and binds its
  actual native receiver on invocation. It forwards immutable caller metadata
  through SourceMethodReceiver, including variadic methods and native interface
  expressions. The existing weak binding registry and per-invocation callback
  wrappers are retained. No mutable current-call or goroutine-ID mechanism was
  introduced.
- `embedded_testing.go`: the suite stores the current interpreter's immutable
  ExecutionError accessor. Every T/F body and cleanup checks it before publishing
  completion; every benchmark guard checks it during unwinding as well. This
  replaces the narrower top-level test/benchmark-only checks, so a callback panic
  interrupting cleanup cannot leave that case marked PASS. RunNativeCallback
  remains the synchronous host recovery marker; native timers stay asynchronous
  and join their creation epoch's panic boundary.
- `execution_lifecycle_test.go`: added asynchronous timer panic cases for an
  embedded cleanup and a benchmark to the isolated containment subprocess. The
  cleanup must report one failed and zero passed tests; the benchmark must report
  one real benchmark execution and no PASS output.
- `native_method_values_test.go` (new): general standard-library regression for
  pointer, value and interface method values, pointer/interface method
  expressions, deferred bound methods and incompatible function-signature
  rejection. These run through ordinary Run, without depending on testing.T's
  source-aware methods.

The previous direct-tools implementation in `qfli_execution.go`, `interp.go`,
`run.go` (getFunc/genFunctionWrapper), `qfli_test_context.go` and the native debug
bridge/tests was inspected and preserved. It installs a common epoch for
EvalPathWithContext, InvokeWithContext and DebugPath, reserves worker tokens
before scheduling, rejects callbacks after the registration gate closes, waits
for entered callbacks and transfers asynchronous panics into the owning
invocation. No shared-core, Dart, platform, curriculum, binary or sibling-product
files were changed by this implementer.

## Checks and next execution gate

Scoped `git diff --check` passed with only the repository's existing LF/CRLF
conversion warnings. The source is manually formatted; standalone gofmt and all
runtime execution are deferred under the coordinator's current no-Go-command
resource restriction. No repaired test pass is claimed.

The static source-review snapshot, computed using
`audit_native.native_source_hash()` after these changes, is
`85d2fae6e988fb59cbd9975681791897fe6da4c1da2b9778cd74bd73a5ae1a82`.
This identifies review input only; it is not a tested/release source freeze.
Formatting or further fixes require recomputing it.

Two further source-review findings remain open at this snapshot and were sent
to the coordinator before broadening the implementation:

- A native struct callback such as `sync.Pool.New`, created on a worker and
  synchronously invoked by main after that worker exits, has no argument-bound
  caller metadata. The current lexical fallback can select the exited routine.
  The existing native dispatch marker distinguishes sync/async but does not
  identify the actual current source dispatch frame through an opaque native
  object. The checker requests both worker-to-main and main-to-worker coverage.
- Promoted native method expressions on interpreted structs are not covered by
  the exact-native expression binder. `(*Wrapped).WriteString` for
  `type Wrapped struct{ *bytes.Buffer }` still reaches the generic bound-selector
  branch, and the early inferred concrete method signature names the embedded
  receiver instead of `*Wrapped`. A focused expression binder must preserve the
  explicit selected receiver and project its embedded native field. Bound
  promoted values and addressable auto-pointer calls appear consistent with
  existing generators but still need meaningful regressions.

These are source-proven design gaps, not newly observed runtime failures. The
coordinator was given implementation recommendations; this snapshot is not
release-ready or a claim that all native semantics are repaired.

The next granted slot should run the pinned SDK's full native suite and vet
sequentially, using process-local memory limits. Full `./...` is required; a
`^TestDebug` filter misses ordinary callback containment, Helper GC and benchmark
skip acceptance. Use `-count=1`, an actual bounded timeout, and preserve stdout,
stderr and the exact process handle/exit. Include `-v` when platform skip details
are needed. Run gofmt over the touched Go files before executing.

Required top-level regressions include:

- `TestDebugBreakpointFramesStepAndContinue`
- `TestDebugMultiFileScopesAndSelectedEntry`
- `TestDebugEntryInitializerDoesNotRunBeforeResume`
- `TestDebugPauseStopAndIDOwnership`
- `TestDebugErrorsAndPanicDoNotEscape` (includes a native timer panic)
- `TestDebugBuffersAndInvalidCommands`
- `TestDebugConcurrentPollCommandsAndClose`
- `TestDebugStopAndCloseWaitForBlockedNativeWorkers` (main, interpreted go,
  native timer literal and native timer named function)
- `TestDebugLocalDependencyInitializerCallbackSameEpoch`
- `TestDebugNativeCallbackKeepsSynchronousThread` (direct and deferred sort)
- `TestDebugClosedEpochRejectsLateNativeCallbacks` (32 concurrent late calls)
- `TestRunGoNativeCallbackPanicsStayInInvocation` (program literal/named,
  initializer, embedded body, embedded cleanup, benchmark; actual subprocess)
- `TestRunGoWaitsForEnteredNativeCallbacks` (main return and cancellation)
- `TestRunGoClosedEpochRejectsRetainedNativeCallbacks` (EvalPathWithContext and
  InvokeWithContext; GC followed by 32 concurrent late calls)
- `TestRunGoMainReturnStopsInterpretedWorkers`
- `TestRunGoNativeMethodValuesAndExpressions`
- `TestRunGoNativeMethodValueRejectsIncompatibleSignature`
- `TestEmbeddedHelperSourceAttribution` (especially method-value,
  method-expression, deferred-method-value; also Unicode, variadic, nested,
  deferred/ordinary anonymous, source interface and subtest cases)
- `TestEmbeddedHelperRegistrationIsPerTest`
- `TestEmbeddedHelperConcurrentCallers`
- `TestEmbeddedHelperTestingFamilies` (T/F/B and all eight diagnostics)
- `TestEmbeddedHelperOriginalT106Failure`
- `TestEmbeddedHelperClosureLifetimeAndNativeRetention` (two waves of 512
  finalizable captures, weak-registry pruning and a live native-retained callback)
- `TestEmbeddedTestingOriginalCurriculum` (all originals, including T106)
- `TestEmbeddedTestingFailuresFatalCleanupAndSubtests`
- `TestEmbeddedTestingPanicsAndNoExecutionCannotPass`
- `TestEmbeddedTestingSkippedBenchmarks` (skipped-only, healthy-plus-skipped,
  failure-then-skip)
- `TestEmbeddedTestingCancelsInitializersAndTests`
- `TestEmbeddedTestingEvidenceJSONAndPreCancellation`
- `TestProjectEnvironmentEvalSymlinksRelativePaths`
- `TestProjectEnvironmentEvalSymlinksLinkTargets`
- `TestProjectEvalSymlinksReferenceProcess` (reference subprocess helper)
- `TestSelectedEntryWorkingDirectoryAcrossExecutionModes`
- `TestRunGoForIterationVariables`

After Windows full native tests/vet pass, actual Linux race execution remains
required for the coauthored lifecycle/concurrency changes and symlink behavior.
Windows link skips are not Linux proof. The existing prepared WSL distro and
local Linux SDK may be used only in another explicitly granted resource slot;
never shut down another product's distribution. Recompute native digests, rebuild
the current DLL and all five Android/OHOS ABIs, then repeat real FFI, corpus,
archive/signature and actual target execution with matching hashes. None of
those later gates is closed by this source handoff.
