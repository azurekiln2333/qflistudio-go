# Helper attribution and EvalSymlinks review repair

Follow-up on the independent runtime review, 2026-10-23. This reopens the
previous native source freeze; the old handoff digest is historical. No library
rebuild, commit, packaged execution or device acceptance is owned by this agent.

## Change boundary

The missing behavior is interpreted testing caller attribution, plus the
relative logical result of the explicitly adapted filepath.EvalSymlinks export.
Source metadata belongs at interpreter invocation boundaries rather than a
mutable slot on testing.T. Filesystem lookup belongs to the existing private cwd
adapter rather than process-wide Chdir. This repair adds no general OS sandbox,
test scheduling feature or curriculum workaround.

## Implementation

- `embedded_testing.go`: a mutex-protected helper-function set per T/F/B.
  Source-aware Helper records the current interpreted function identity;
  Log/Logf/Error/Errorf/Fatal/Fatalf/Skip/Skipf choose the first unmarked source
  caller, preserving existing failure, Goexit and skip behavior. Native-only
  internal calls keep their fallback diagnostics without invented source lines.
- `interp/qfli_callsite.go`: immutable interpreted source frame chains and a
  narrow SourceMethodReceiver boundary. A per-interpreter reflected-function
  binding registry carries provenance for method values and callbacks. Bound
  method Values are materialized before being copied into source variables;
  closure identity is normalized with reflect.ValueOf(value.Interface()), not
  code-pointer identity. Method expressions match their actual native method.
  Native callbacks receive a per-invocation wrapper; no global current-call
  slot, runtime.Caller attribution or goroutine ID is used.
- The binding registry stores only public weak pointers, indexed with
  maphash.Comparable and checked again by canonical reflected-function identity.
  A live wrapper owns its binding lease, so callbacks retained by native code
  remain callable while abandoned closures and captured objects can be collected.
  Dead registry buckets are pruned periodically. Native source now declares
  Go 1.24 in go.mod; GOTOOLCHAIN=local supplies the official minimum-version
  error with an older SDK. Release SDK pinning remains Go 1.27.1.
- `interp/interp.go`, `interp/run.go`: frames retain/clone source ancestry.
  Source/native calls, method selection and defers pass explicit invocation
  metadata. Deferred arguments are shallow snapshots taken when scheduled;
  variadic CallSlice retains normal slice semantics. Existing frame mutex release
  around native deferred calls remains intact.
- The direct-tools owner coauthored the callback bodies in getFunc and
  genFunctionWrapper, registering an invocation alias and setting actual source
  caller metadata. Its separate debug-epoch gate owns callback lifecycle and
  uses the explicit native dispatch marker only to distinguish native reentry.
- Embedded test/benchmark bodies and cleanups enter through RunNativeCallback
  so their existing recovery owns synchronous failures. A skipped benchmark
  reports SKIP without treating its zero iterations as a failed measurement;
  a suite containing only skipped work still cannot claim successful execution.
- `project_environment.go`, `project_symlinks.go`: Go's symlink component walker
  adapted to private cwd lookup. Logical relative paths remain relative;
  absolute link targets remain absolute, including targets outside the project.
  The input is not cleaned before resolving link/.. . Windows filename casing
  is normalized through the actual OS implementation. The inherited Go BSD
  notice is retained in `LICENSE.go-standard-library`.
- `.trellis/spec/backend/native-go-runtime.md`: removed the historical Helper
  no-op promise and recorded the repaired source and symlink contracts.

## Regression coverage and validation status

New `embedded_helper_test.go` exercises unmarked and nested helpers, method
values/expressions, variadic calls, deferred native/anonymous calls, actual
Unicode filenames, anonymous callbacks, subtests, source interfaces, distinct
test objects and simultaneous callers. T/F/B each exercise all eight diagnostic
families. The original T106 success sample joins the existing curriculum test;
an intentionally changed expected value requires a real failure at the source
assertion's caller line. Curriculum teaching text and expected behavior are
preserved.

New `embedded_helper_lifetime_test.go` registers two waves of 512 temporary
closures capturing finalizable native objects, requires those objects to be
collected, and invokes a native-retained callback after GC and registry pruning.
The retained callback must still fail at the original interpreted caller line.
The benchmark skip regression covers a skipped-only suite, a healthy test plus
a skipped benchmark, and failure followed by Skip.

New `project_symlinks_test.go` compares actual interpreted output with the
official filepath implementation running in a separate process whose cwd is the
selected src directory. The host test process never changes cwd. Coverage
includes ordinary relative paths, parent components, empty paths, absolute
paths, relative/absolute/outside-project/chained links, link/.., missing paths,
non-directory components and link loops. Link cases skip only if the actual host
refuses symlink creation.

Formatting and `git diff --check -- native/go_runtime
.trellis/spec/backend/native-go-runtime.md` passed. Runtime tests and vet are
pending the coordinator's explicit resource slot; no new runtime pass or source
freeze is claimed at this point. The initial planned focused command uses the
pinned SDK and GOMEMLIMIT=512MiB, GOGC=20, GOMAXPROCS=2, GOFLAGS=-p=1:

`go test -mod=vendor -count=1 -run 'TestEmbeddedHelper|TestProjectEnvironmentEvalSymlinks|TestEmbeddedTestingOriginalCurriculum/T106|TestEmbeddedTestingSkippedBenchmarks' .`

After the coauthored native regressions and full suite/vet pass, recompute the
corpus auditor's native source digest and rebuild all matching libraries before
attributing actual FFI/corpus/HAP/device evidence.
