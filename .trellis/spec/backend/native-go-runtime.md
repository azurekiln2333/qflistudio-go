# Native Go Runtime

Execution policy: apply `AGENTS.md` and [Cloud-Only Execution](cloud-only-execution.md).
All test/vet/analyze/build, helper verification, SDK setup and artifact checks below
run only in GitHub-hosted Actions. Historical local evidence does not authorize
local reruns or binary artifact downloads.

## Scope

Android, OpenHarmony, and iOS call `native/go_runtime` through Flutter FFI.
Desktop execution uses the official Go SDK in `lib/go_runner.dart`. The mobile library
is a Yaegi interpreter; it does not provide the Go SDK, native `go build`, or
module downloads. Selected `_test.go` entries use the bounded embedded test
engine described below. Create a fresh interpreter for each run.

## Signatures

```c
char *QfliGoRun(unsigned long long id, char *projectPath, char *entryFile);
void QfliGoCancel(unsigned long long id);
void QfliGoFree(char *result);
char *QfliGoAnalyze(char *requestJson);
char *QfliGoFormat(char *requestJson);
char *QfliGoDebugStart(unsigned long long id, char *requestJson);
char *QfliGoDebugPoll(unsigned long long id, unsigned long long afterSequence);
char *QfliGoDebugCommand(unsigned long long id, char *requestJson);
char *QfliGoDebugClose(unsigned long long id);
```

`tool/build_go_runtime.ps1 -GoExecutable <go.exe> -OhosGoExecutable <ohos-go.exe> -AndroidNdk <ndk> -OhosSdk <sdk>`
builds three Android ABIs and OpenHarmony arm64-v8a/x86_64.
`tool/build_ios_go_runtime.sh` runs in the iOS Runner build phase and produces
a c-archive for the active Xcode SDK and architectures.

## Contracts

- Run IDs are uint64; Dart allocates one for each invocation.
- Paths are UTF-8 absolute strings. The entry must exist inside the project.
- The result is an allocated UTF-8 JSON string with `stdout` and `stderr`
  strings, and integer `exitCode`. Dart frees it through `QfliGoFree`.
- A run is invoked in `Isolate.run`. Output is buffered until completion.
- Cancellation before native registration is remembered by the bridge.
- The source filesystem maps `qfli-project` into the selected project.
  This is source lookup, not an operating-system sandbox.
- Builds must use `-mod=vendor`: Yaegi's path evaluation and goroutine launch
  functions carry local fixes. `go mod vendor` overwrites these fixes.
- Native source requires Go 1.24 or newer for public weak pointers and reflected
  value hashing. Release builds currently pin official Go 1.27.1 and the matching
  OHOS port. Build entry points set GOTOOLCHAIN=local: an older SDK reports the
  go.mod minimum-version error instead of downloading another toolchain.
- OpenHarmony must use `GOOS=openharmony` with the pinned OHOS Go port, not
  upstream `GOOS=linux`: the latter's initial-exec TLS fails at `dlopen`.
  `tool/build_ohos_go_toolchain.ps1` builds release `v1.27.1-ohos` at commit
  `f2cb44316b789bc12d0b5fd562d853f6fec3ab28`. Use its isolated cache and
  `GOTOOLCHAIN=local` to keep upstream relocation types out of OHOS builds.

## Platform Selection And Apple Integration

- `lib/go_platform.dart` owns the backend mapping. Runner dispatch, profile
  metadata, and native integration eligibility consume that same mapping.
- Android/OHOS/iOS: `embedded-go-runtime` and `available`; desktop:
  `official-go-sdk` and `requires-sdk`; unsupported targets: `unavailable`.
- Desktop metadata records the SDK prerequisite. Actual execution reports
  not-run when `go` cannot be launched from the application environment.
- iOS uses `DynamicLibrary.process()` for both run and cancel. Android/OHOS
  retain `DynamicLibrary.open('libqfli_go_runtime.so')`.
- Build iOS with `GOOS=ios`, cgo, vendor mode, and `-buildmode=c-archive`.
  Device architecture is arm64; simulator architectures are arm64/x86_64.
  Match clang to the active Xcode SDK and deployment target. Include target
  arguments in `CC` so changes participate in Go's build cache identity.
- Keep the archive, headers, and caches in `DERIVED_FILE_DIR`; preserve LF
  line endings in the Xcode shell script. `QFLI_GO_EXECUTABLE` can override
  the Go SDK executable on the build Mac.
- Debug and Release include `NativeGoRuntime.xcconfig`; Profile uses Release.
  Link the generated archive and retain/export all nine public C ABI symbols
  so release dead stripping cannot remove functions used only through FFI.
- A source review or `bash -n` is not an iOS build/device test. Record Apple
  execution as untested until Xcode and an Apple target are available.

## Validation And Errors

| Condition | Result |
| --- | --- |
| Completed main function | Exit code 0 and captured output |
| Missing or outside entry | Exit code 127 and path error |
| Parse, type, or execution error | Exit code 1 and diagnostic stderr |
| Unrecovered main or worker panic | Exit code 1 and panic diagnostic |
| Restricted Yaegi `os.Exit(n)` | Exit code 1 with `os.Exit(n)` diagnostic |
| Cancelled context | Exit code 1 and context error |
| FFI load or decoding failure | Dart not-run exit code and load diagnostic |

## Cases

- Good: main and helper files in the same package print `ready`.
- Base: a compile error returns stderr and leaves the application running.
- Bad: an unhandled interpreted `go` call panic escapes into the host runtime.
- Bad: reading `bytes.Buffer` while a cancelled worker is still writing.

Use the synchronized `outputBuffer` for interpreter stdout/stderr. The patched
`EvalPathWithContext` transfers results through a channel, reports worker and
native-callback panics, and stops interpreted frames when the task ends.
Cancellation waits for entered workers/callbacks and compiled blocking calls
to return; do not assume it interrupts native IO.

## Required Checks

- `go test -mod=vendor ./...` and `go vet -mod=vendor ./...` in the native module.
- Cover multi-file execution, invalid code, pre-cancellation, running-program
  cancellation, main panic, worker panic, restricted `os.Exit`, and concurrent
  output without losing lines.
- `flutter analyze` and `flutter test`; set `QFLI_GO_TEST_EXECUTABLE` to an
  installed SDK to run the official toolchain test rather than skip it.
- If Windows reports compiler memory-allocation failures, constrain the
  verification process with Flutter `--concurrency 1`, `GOMAXPROCS=2`, and
  `GOFLAGS=-p=1`. Keep these settings local to verification; rerun the actual
  SDK assertions and do not convert an allocation error into a successful test.
- Rebuild shared libraries after changing the runtime or vendored dependency.
- Android library LOAD alignment must be at least 16 KB; verify all three ABIs
  are in the APK. Verify the OpenHarmony library is in the unsigned HAP.
- Run `integration_test/go_native_test.dart` on Android/OpenHarmony/iOS to verify
  FFI execution, panic handling, and cancellation. Build success alone does
  not establish device execution support.

## Wrong And Correct

Wrong: wrap `EvalPathWithContext` with a caller-side `recover` and assume it
catches panics from the interpreter's goroutines.

Correct: recover inside each evaluation/worker goroutine, transfer the error
to its current task, and report it through the established JSON result.

## Build constraints and device cancellation (2026-10-15)

Use the vendored `buildConstraintsOk` on raw AST line comments: one modern
`//go:build` wins over legacy lines, malformed/duplicate modern directives return
errors, and directives written inside block comments are ignored. Evaluate with
the existing tag predicate; test selected, helper and imported sources. Rebuild
all five bundled libraries after changing this filter.

Native stdout is buffered. Device cancellation synchronization must use a bounded
project-local marker written inside main; do not wait for live stdout first.
The complete matrix and required assertions are preserved in the release audit's
`research/release-contracts.md`.

## Scenario: offline IDE and embedded package execution (2026-10-23)

### 1. Scope / Trigger

The product now ships pure syntax analysis/formatting, a real debugger and an
embedded test subset. Treat these as separate capabilities. Analysis must never
compile imports, execute initializers or modify the supplied source file.

### 2. Signatures

The nine exported symbols above share C-string ownership: every non-null JSON
result is released once through QfliGoFree. Dart startNativeGo returns
NativeGoExecution(result: Future<NativeGoResult>, cancel: ...); runNativeGo
adapts this single decoder to ProgramRunResult. Do not parse proof fields in UI.

`useProjectEnvironment(interpreter, project, initialDirectory)` receives the
physical project and selected entry directory. Ordinary runs, tests and debug
all use the selected package directory as their initial cwd. Temp files remain
under project/.qfli/tmp; no process-wide Chdir/TMPDIR change is permitted.

### 3. Contracts

- Analyze/Format request: `{filePath: string, source: string}`. filePath is an
  identity, not a file to open. Source limit is 4 MiB UTF-8. Schema1 response
  contains filePath, utf16Length, packageName, diagnostics, imports and symbols;
  optional formattedSource/error. Ranges are original-source UTF-16 offsets,
  including CRLF and supplementary Unicode. This is syntax analysis, not type
  checking. Malformed requests and oversized buffers fail visibly.
- Run adds optional testExecution with engine `qfli-embedded-testing-v1`,
  testsRun/testsPassed/testsFailed/testsSkipped/benchmarksRun/fuzzSeedsRun.
  Ordinary programs omit it. Assertions, synchronous subtests, Fatal/Skip,
  cleanups, TempDir and registered fuzz seeds are supported. Benchmarks use
  actual testing.Benchmark/PB. Parallel, Setenv, Chdir, TestMain, mutation fuzz,
  coverage and race are unsupported by this in-process test engine. Helper uses
  interpreted function identities registered on the individual T/F/B. Logging,
  Error/Fatal and Skip diagnostics report the first unmarked source caller,
  including method values, variadic calls, deferred calls and Unicode filenames.
  Source stacks travel as immutable invocation metadata; never infer them from
  host runtime.Caller or a shared current-call slot.
  Reflected callback lookup uses weak registry entries; live wrappers own their
  source binding so native-retained callbacks survive GC without retaining all
  abandoned closures. A retained callback's source lease identifies its own
  function, not a registration-time caller after that call returned. Helper
  attribution stops at an opaque callback boundary and may fall back to that
  callback's actual diagnostic line; ordinary in-call T/F/B caller attribution
  remains unchanged. Skipped benchmarks report SKIP, and skipped-only suites
  cannot claim successful execution.
- Package loading, discovery and all test callbacks must stay inside ONE
  InvokeWithContext epoch. Stopping after EvalTest invalidates Pool.New,
  handlers and captured goroutines. Do not expose success from printed PASS
  without checking actual execution metadata.
- EvalPathWithContext and InvokeWithContext own the same callback registration
  and shutdown boundaries as debug. Normal main return starts shutdown without
  waiting for future timers; entered workers/callbacks must actually leave
  before returning a result. Native callback panics become invocation failures.
  Test-body and benchmark adapters use RunNativeCallback around synchronous
  host bodies so their existing panic/Goexit handlers retain test attribution.
- DebugStart request contains projectPath, entryFile and relative-file ->
  one-based-line-list breakpoints. Poll uses an event sequence cursor. Command
  contains command and goroutineId. Native events/output are bounded; preserve
  truncation/unavailable fields. Execution IDs are live debugger command owners.
  Optional threads/events `kind` is `goroutine` or `nativeCallback`; the latter
  labels a logical opaque native callback, without claiming a physical new
  goroutine. Events retain this metadata after the owner exits. Imported-package
  initialization retains interpreter semantics.
- Debug import preparation, the entry pause and entry execution share one
  continuous evaluation epoch. Attach the debugger before dependency
  initialization so initializer-created callbacks keep valid frames and run IDs.
- Native Close retains ownership until worker and callback cleanup really
  finishes. Acquire the epoch token before spawning an interpreted worker and
  when entering a compiled-library callback. Close registration under the same
  lock before waiting; reject callbacks retained from a closed epoch. Waiting
  only for a later enterGoRoutine registration races main completion.
  Proven direct synchronous native reentry keeps its actual calling execution
  ID. Only the exact native function value and signature at callback argument
  index 1 for sort.Slice, sort.SliceStable and sort.Search prove synchronous,
  non-retaining dispatch. Their pinned implementations call the callback inline;
  names or matching signatures do not establish that contract. Generic native
  callback arguments are opaque even when the original registration remains
  active: another interpreted dispatch can invoke a retained argument while the
  registrar blocks. A bare go call of a compiled native function also cannot
  reuse its launching frame as the current caller; its callbacks stay opaque.
  A generic native stack marker classifies panic propagation
  only, not caller identity. Every unknown-provenance entry (for example a
  retained argument or a sync.Pool.New field) gets a fresh live `nativeCallback`
  owner, even on a synchronous dispatch stack.
  Known external callbacks get a new goroutine owner. Native dispatch-stack
  identity may distinguish synchronous panic propagation from external recovery;
  it cannot identify an unknown caller. Keep debug ownership separate from panic
  recovery: a synchronous opaque panic remains recoverable in its interpreted
  caller, while an external panic fails the epoch. Register before entry events
  and remove the owner once before releasing its epoch worker token.
  Events set `opaqueNativeBoundary: true` for opaque owners, and the final source
  frame sets the same flag. Keep lexical `.anc` for captures, use proven actual
  caller links for displayed synchronous reentry, and stop both debug/source
  stacks at opaque entries. StepOut can finish an opaque owner without promising
  a pause in an unknown native caller. Opaque snapshots never inspect locals and
  report `Opaque native callback may capture values outside this stack; locals
  were not read`. Do not infer safety only from the current live owner count.
  Stopped scalar reads use DebugEvent.WithStoppedValues: the live-owner and
  owned-worker eligibility check, scalar snapshot, new-owner registration and
  resume are serialized by the debugger registry/routine locks. startGoroutine
  reserves an owned-worker count before scheduling, including compiled go calls
  without interpreted frames. No arbitrary methods/Stringer calls, native
  pointer dereferences or aggregate expansion may run under the snapshot guard.
  Compiled APIs can retain mutable aliases after returning: the shipped
  net/rpc.Client.Go stores reply and its native input worker writes through it.
  Before native dispatch, conservatively mark pointer, map, slice, channel,
  unsafe.Pointer, interface-underlying and struct/array alias types, including
  bound native receivers. Mark source callback result aliases before returning
  them to compiled code. Inspect types and interface contents only; never walk
  pointer targets, aggregate field values or the native heap. Function wrappers
  remain distinct because their interpreted entry and result escape are guarded.
  A possible mutable escape disables scalar snapshots for the whole debugger
  session, even after the native call/worker completes, and reports `Native code
  may retain mutable values; locals are unavailable for this session`. There is
  no evidence-based general release point for an unknown native alias.
  Pure scalar arguments/results remain readable. Exact sort.Slice/SliceStable
  argument 0 is a documented synchronous/non-retaining slice borrow; match the
  same exact native Type+Pointer contract, and retain owned-worker exclusion for
  bare go dispatches. Do not grant exceptions by package/name/signature alone.
  The guarantee covers tracked interpreter storage used through safe Go; native
  aggregate expansion and arbitrary unsafe-memory introspection are unsupported.
  Never use goroutine IDs, TLS or a shared current-call variable for provenance.
  Blocking compiled stdlib calls may delay Stop; do not return a synthetic
  terminal state early.
- GoStudioDebugger consumes the shared immutable FULL-snapshot API. Breakpoints
  are launchOnly; snapshots are unsupported and disk sources must be saved.
  Pause tokens bind session plus generation; any resume invalidates the old
  token even if another goroutine remains paused. Output-only changes increase
  revision and replace complete rolling buffers. done/stop/dispose wait for
  actual native termination AND registry cleanup. No expression evaluation.
- Per-interpreter filesystem exports are limited path adapters, not an OS
  sandbox. Absolute paths retain application permissions. Compiled stdlib
  internals (for example template.ParseFiles) and native File.Chdir do not
  automatically pass through os export wrappers. Extend only with actual
  reproduced contracts; never use global cwd to make an audit pass.
  EvalSymlinks walks components from the interpreter cwd without first cleaning
  link/..; its logical result stays relative until an absolute symlink target
  is crossed. Absolute paths retain application permissions.
- All build scripts set local/vendor/offline dependency resolution and
  GO_TELEMETRY_CHILD=2. The pinned Go SDK reads telemetry mode from a config
  file: setting GOTELEMETRY=off alone does not disable its uploader startup.
  Preserve and restore PowerShell process environment values.

### 4. Validation & Error Matrix

| Condition | Expected behavior |
| --- | --- |
| Malformed source/Unicode error | Real syntax diagnostics in original UTF-16 source |
| Formatting invalid source | Error/diagnostics, no invented formatted result |
| Ordinary program | No fabricated testExecution |
| Test assertion/Fatal or unsupported operation | Nonzero result, real failure evidence |
| Cancelled test package | Same invocation cancelled, context error; no main fallback |
| root and src contain same filename | Selected src entry reads/writes src; host cwd unchanged |
| Debug stale token, wrong session or source escape | Reject without sending a native command |
| Debug blocked stdlib worker | Stop/Close remains pending until actual worker exit |
| Missing library/export | Explicit unavailable capability, no SDK fallback |

### 5. Good/Base/Bad Cases

Good: an unsaved syntax error shows the correct range without writing a marker;
explicit debug pauses before a source side effect, reads value42, resumes and
releases its registry ID. Base: an ordinary program still returns the original
stdout/stderr/exitCode shape. Bad: a test import silently runs another main, or
Stop completes while an HTTP child still owns the interpreter.

### 6. Tests Required

- Native full test/vet plus regressions for test callbacks/HTTP timeout defers,
  program/test/debug cwd parity, project temp, concurrent project files and
  loop body/condition/post closures, continue, tuple and blank-tuple variables.
- Debug local dependency initialization with sync.Pool.New must match ordinary
  Run after Continue. Held HTTP calls from time.AfterFunc must keep Stop/Close
  pending and appear as live threads. Check synchronous sort.Slice callback
  thread identity, callback panic handling and rejection of retained callbacks
  after debugger Wait. Also cover an exited callback creator, main-created/
  worker-called opaque entries, independently paused concurrent entries, nested
  source/native reentry, boundary StepOut, synchronous recover and external panic,
  held opaque callback Stop/Close, unavailable locals, retained history metadata
  and closed-epoch rejection before any new debug owner. Run the real Linux race
  detector for these regressions.
  Also cover retained direct arguments after registrar exit and while their
  registrar remains blocked, including concurrent invokers, source-stack cutoff,
  synchronous recovery and external panic transfer. Exact sort type/signature
  lookalikes must remain opaque. A deterministic stopped-main snapshot test
  holds the value guard until an actual callback contender blocks in owner
  registration, reads the pre-entry scalar, then permits its mutation. Compiled
  go workers with no source frame or mutable arguments must suppress locals and
  release that exclusion when they actually leave. Actual rpc.Client.Go reply
  mutation and deferred native mutation through a source callback's pointer
  result must keep locals unavailable after the apparent native work completes.
  Pure scalar callback/native fmt calls must preserve ordinary scalar locals.
- Native method selectors must preserve bound signatures and explicit outer
  receiver types for method expressions. Promoted expressions project embedded
  fields at invocation, including nested pointer and native interface embeddings;
  by-value expressions cannot implicitly take the address of an embedded value.
  Keep source-aware receivers and variadic/deferred dispatch on the same bridge.
- Exercise T106's negative assertion path and source attribution with nested
  helpers, distinct test objects, subtests/anonymous functions, method values,
  variadic/deferred/concurrent calls and all T/F/B diagnostic families. Compare
  short-lived closure GC with native-retained callbacks, including a second
  registration wave that triggers weak registry pruning. Compare
  interpreted EvalSymlinks with official filepath in a separate cwd-owned
  process for relative/absolute link targets, link/.. and error cases.
- Actual rebuilt-library tests: go_code_analyzer_test.dart,
  go_debugger_test.dart, go_studio_debugger_test.dart and
  native_go_result_test.dart with QFLI_GO_RUNTIME_LIBRARY set. Mock-only or
  skipped tests do not prove native ABI integration.
- Repeat exhaustive original/expanded official/native audits with exact
  source/catalog hashes. Then run packaged FFI on OHOS. Do not set
  Directory.current or os.Chdir to the fixture in either harness.
- Rebuild all five Android/OHOS libraries after any vendor/native source change.
  Windows/Linux CMake bundles the dynamic runtime; macOS Runner invokes
  build_macos_go_runtime.sh and signs its Frameworks dylib. A Windows syntax
  check does not prove an Xcode build.
- build_go_catalog_audit.ps1 must restore original entry-profile bytes even on
  failure and reject concurrent edits instead of overwriting them.
  inspect_go_catalog_hap.py checks exact assets/runtime bytes, ELF ABI and nine
  exports. Signature validation and actual device execution remain separate.

### 7. Wrong vs Correct

Wrong: EvalTestWithContext -> stop -> InvokeWithContext(test callbacks), or
test stdout containing PASS is treated as proof. Correct: one continuous
context for package initialization/discovery/execution and typed nonzero test
counts. Wrong: change the host cwd before running imports. Correct: pass the
entry directory to per-interpreter path exports and prove host cwd is unchanged.

## Scenario: GitHub native library artifacts (2026-11-17)

### 1. Scope / Trigger

`.github/workflows/native-runtime.yml` builds Android, OpenHarmony, macOS and
both iOS target families. Linux source tests produce no distributable library.
Windows/Linux program execution uses the official SDK, but diagnostics and
source debugging still require this project's own dynamic library.

### 2. Signatures

- `tool/build_go_runtime.ps1 -Platform all|android|ohos` defaults to `all`.
- `tool/ci/install_ohos_sdk.ps1 -Url <https> -Sha256 <64 hex> -Destination <new dir>`.
- `python tool/ci/collect_native.py snapshot <json>` before building.
- `python tool/ci/collect_native.py stage --platform <target> --snapshot <json> --output <empty directory>` after building; add `--readelf` for ELF or `--build` for Apple.

### 3. Contracts

- Preserve the default five-library provenance filename and schema. Selected
  platforms write distinct `bundled-go-runtime-build-<platform>.json` files.
- A selected platform must not require the other platform's SDK or compiler.
- Use official Go 1.27.1, vendored sources and local/offline build flags.
- Default OHOS provisioning uses the official release archive and fixed SHA-256.
  URL/digest overrides must be a complete pair from the same configuration source.
- Android and OHOS are independent jobs. Apple matrix failure does not cancel
  another Apple target. Only successful collection uploads a native artifact.
- Collect exact expected ABI inventories, headers, project/Go/Yaegi licenses,
  file hashes, source/build hashes, commit and run identity. Do not upload SDKs.
- Android ELF LOAD alignment is at least 16384. All libraries export the nine
  C ABI symbols; each Apple slice must pass its own symbol inspection.
- Separate iOS device and simulator archives. macOS uses a universal dylib.
- CI explicitly targets macOS 13.0 and iOS 13.0 before source capture. Record
  the configured deployment target in the manifest build section. Go 1.27
  requires macOS 13; the existing app's 10.15 Xcode setting is a separate
  compatibility mismatch and does not establish older-system support.
- Artifact names include target and commit. Retention is 14 days.

### 4. Validation & Error Matrix

| Condition | Result |
| --- | --- |
| Incomplete SDK URL/digest pair | Fail before SDK download |
| SDK checksum or expected layout differs | Fail provisioning |
| Native/build input changed during build | Reject collection |
| Provenance predates snapshot or mismatches source/file | Reject collection |
| Wrong ABI, missing export or bad Android alignment | Reject artifact |
| Apple target lacks an expected architecture | Reject artifact |
| No files available for upload | Fail upload |

### 5. Good/Base/Bad Cases

Good: a clean checkout builds each requested target and uploads matching hashes.
Base: omitting `-Platform` retains the existing Android/OHOS local build.
Bad: collecting the checked-in Android SO files after a failed compiler step.

### 6. Tests Required

Run actionlint, PowerShell parser checks, Bash syntax checks, and the artifact
collector's rejection tests. The remote source job runs vendor-mode Go test/vet.
Observe an actual Actions run before claiming cross-platform build success.
Download artifacts and validate the listed hashes and expected inventory.
A native-only CI change does not require a new Flutter UI test run.

### 7. Wrong vs Correct

Wrong: report a green YAML check as a successful Apple build or device test.
Correct: report each remote job and its actual artifacts; device execution is a
separate gate. Cloud builds do not remove local files. Existing Apple build
phases still compile from source and do not automatically consume downloads.
The first hosted source test run exposed existing debugger failures. Build jobs
now run after source checks even when those checks fail, while the source job
and overall workflow remain failed. Every artifact records
`sourceChecksConclusion` and `sourceChecksRunURL`; a failed/unknown status is
shown as compilation-only evidence. Never hide failures with continue-on-error.
