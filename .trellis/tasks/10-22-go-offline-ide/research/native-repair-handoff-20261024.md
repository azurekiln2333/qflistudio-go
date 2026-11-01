# Native callback and promoted-method source repair handoff

Date: 2026-10-24, Asia/Shanghai. Owner: `native_finish_1024`.

This is a source handoff for independent review. No Go, gofmt, test, vet, SDK,
Dart, Flutter, WSL, build or device command was started in this turn. There is no
live native/SDK handle or host reservation owned by this worker.

## Source identity

`audit_native.native_source_hash()` was called through a Python import only:

`5fed89f7c6ed1fe44e40b1701b4760d0cf6bdb38a52da0894a8860e9b38b79d6`

This digest includes all native source and test files using the audit's existing
inventory. It identifies uncompiled source, not successful execution. Recompute
after any review edit or later gofmt operation.

Files changed by this continuation:

| File | Change |
| --- | --- |
| `native/go_runtime/vendor/github.com/traefik/yaegi/interp/debugger.go` | Actual synchronous debug caller links independent of lexical capture; opaque stack boundary walking; guarded routine removal; nil-safe event accessors; complete kind/boundary accessors already started in the worktree |
| `native/go_runtime/vendor/github.com/traefik/yaegi/interp/qfli_execution.go` | Complete callback preparation with actual debug caller links while preserving the fresh opaque-owner/panic-recovery separation already started |
| `native/go_runtime/debugger.go` | Preserve thread/event/frame metadata and explicit opaque locals limits; clear stopped owners when actual exit events arrive |
| `native/go_runtime/debugger_test.go` | Nine substantive opaque callback regressions; strengthen existing direct/deferred synchronous metadata assertions |
| `native/go_runtime/native_method_values_test.go` | Nested pointer, interface and deferred promoted expressions; reject another by-value pointer-method expression |
| `.trellis/spec/backend/native-go-runtime.md` | Logical owner, provenance, boundary, locals, panic, cleanup and method-expression contracts |
| This handoff | Review snapshot and pending gates |

Previously started source changes were preserved and reviewed, including
`vendor/github.com/traefik/yaegi/interp/qfli_callsite.go`, `cfg.go`, `type.go`,
`run.go` and the execution epoch changes. Those remain part of this digest.
Unrelated native, product, shared-core and sibling-product edits were not
reverted. No Dart/shared-core files were edited by this worker.

## Callback design and metadata

- Unknown-provenance entries (`caller == nil`, such as native `sync.Pool.New`
  fields) receive a fresh live logical `nativeCallback` owner. A lexical creator
  may already have exited, or two callers may enter the same closure concurrently.
  Neither case reuses the captured frame's command ID or resume channel.
- Debug ownership is independent of asynchronous panic handling. The dispatch
  stack marker classifies synchronous versus external entry only. A synchronous
  opaque panic propagates through the native stack to interpreted `recover`;
  an external callback panic fails its execution epoch.
- Lexical `.anc` remains available for captured storage. Proven synchronous
  contexts have a separate debug caller link. Opaque entries start a source
  frame with no parent before `runCfg` can perform lexical fallback, and their
  displayed stack stops at an explicit boundary. Nested interpreted calls and
  nested direct native callbacks remain inside that boundary.
- Registration precedes entry events/breakpoints. Callback cleanup removes the
  debug owner before releasing the epoch worker token. Main ownership remains
  until shutdown joins entered callbacks. Actual exit notifications remove any
  stale bridge pause entries. StepOut from the opaque entry may finish that
  logical owner without inventing a stop in an unknown native caller.
- Additive JSON: threads/events `kind` is `goroutine` or `nativeCallback`;
  opaque events set `opaqueNativeBoundary: true`; the final source frame sets
  the same flag. Paused event snapshots retain these fields after owner exit.
- Opaque snapshots do not read locals, regardless of current live-owner count.
  Exact reason: `Opaque native callback may capture values outside this stack;
  locals were not read` (one line in the actual JSON).
- Interpreter accessors: `DebugGoRoutine.Kind()`, `DebugEvent.GoRoutineKind()`,
  `DebugEvent.OpaqueNativeBoundary()`, `DebugFrame.OpaqueNativeBoundary()`.

`callback_finish_1024` confirmed the matching strict optional Dart decoder,
legacy defaults, honest native callback labels, history retention, boundary
display and native reason preservation. Its handoff is
`callback-product-source-handoff-20261024.md`.

## Promoted method expression review

The existing partial binder is retained: `nativeSelectorType` distinguishes a
bound value from an explicit receiver expression. `matchSelectorMethod` passes
the selected outer receiver type and copied embedding indices to
`nativeMethodExpression`. Invocation projects the embedded receiver, takes its
address only where valid, binds source-aware native methods and uses the common
provenance-aware dispatcher. `nativeProjectionAddressable` rejects expressions
that would implicitly address a by-value embedded value; pointer embeddings
still supply valid addressability. Interface methods have no reflected
`Method.Func`, and the callable signature/binder preserve that distinction.

Existing direct native value/pointer/interface expressions, method values,
automatic addressing, deferred values, promoted pointer/value/address forms and
incompatible-signature assertions were preserved. Added cases exercise multiple
embedding levels, a pointer inside a by-value outer expression, native interface
embedding, deferred projected expressions and a nested invalid value expression.
These are source assertions awaiting execution.

## Added debugger regressions (not executed)

| Test | Evidence required when run |
| --- | --- |
| `TestDebugOpaqueCallbackOutlivesItsCreatingWorker` | Stop creator before its signal, wait at a main barrier until the creator really leaves the live list, then break/step/continue a distinct live callback and preserve metadata after exit |
| `TestDebugOpaqueCallbackCreatedByMainCalledByWorker` | A callback created by main and called by a worker gets its own kind/boundary and control ID |
| `TestDebugConcurrentOpaqueCallbacksHaveIndependentControls` | Two live callback IDs share a lexical origin, pause independently, step/continue separately, StepOut reaches and finishes the boundary, and owners/stopped entries drain after both leave |
| `TestDebugSynchronousOpaqueCallbackPanicRecoversInCaller` | Owning a logical ID does not swallow a panic recoverable by the interpreted caller |
| `TestDebugStopAndCloseWaitForHeldOpaqueCallback` | A private HTTP gate keeps an entered callback held; Stop/Close remain pending until actual fixture release and registry cleanup follows |
| `TestDebugClosedEpochRejectsRetainedOpaqueCallbacks` | A native Pool field retained beyond Wait cannot execute or create even a transient debug owner; 32 late calls remain rejected |
| `TestDebugNestedNativeReentryKeepsOpaqueOwnerAndActualCaller` | A main-created comparison closure called by sort from an opaque entry keeps the live opaque ID and follows the actual callback caller instead of lexical main |
| `TestDebugAsynchronousOpaqueCallbackPanicStaysInEpoch` | A native goroutine invokes the raw stored Pool callback, its panic fails the epoch, and exactly one enter/exit pair drains |
| `TestDebugOpaqueCallbackSourceStackEndsBeforeLexicalCreator` | A source-aware native recorder sees only inner/callback source frames, excluding installation and creator ancestry |

Existing initializer, direct/deferred sort, blocked native worker, late callback,
Run/Invoke lifecycle, Helper attribution/weak-GC, benchmark-skip and symlink
regressions remain intact. The private held HTTP fixture releases through a
defer before registered debugger cleanup can block.

## Checks and pending validation

- Scoped `git diff --check -- native/go_runtime
  .trellis/spec/backend/native-go-runtime.md`: exit 0. Git emitted its existing
  LF/CRLF conversion notices; no whitespace errors were reported.
- Python whitespace inspection of every file edited here, including untracked
  native bridge/tests: zero trailing-whitespace or final-newline issues.
- Python source hash: recorded above. No compile/test/gofmt/vet/race result is
  claimed, and no library was rebuilt.

Historical failed native handle **85731 exit 1** remains authoritative for that
attempt. SDK **21711 exit 0** and final **70405 / shell PID 64664 exit 0** cover
only the previously recorded Windows SDK regressions/scoped analysis. Go236 was
released at global seq287; no new heavy command is authorized by this handoff.

After independent source review and a later named resource grant:

1. Run gofmt only on owned changed native files, then record a new digest.
2. Run the complete native module serially with the pinned offline SDK:
   `go test -mod=vendor -count=1 -timeout=90s -v ./...`.
3. If that passes within the grant, run `go vet -mod=vendor ./...`. Record exact
   handles/PIDs where available, terminal exits and log paths; release promptly.
4. Obtain a separate real Linux race window for concurrent callback controls,
   lifecycle/retention and symlink comparisons. Source review is not race proof.
5. Later rebuild the current DLL and all five Android/OHOS libraries, run real
   Dart FFI tests, inspect exact packaged artifacts and perform target acceptance.

`native-final-validation-plan-20261023.md` retains the offline memory settings,
full inventory and separate platform gates. No final native acceptance, host
reservation, source freeze across future reviewer edits, device acceptance or
commit is implied here.
