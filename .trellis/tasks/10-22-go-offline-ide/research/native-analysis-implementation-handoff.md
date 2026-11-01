# Native analysis, embedded testing and execution handoff

Recorded on 2026-10-23 by the Go native analysis implementer. Native sources are
stable for the root coordinator's final rebuild. No commit, library rebuild or
device claim was made by this subagent.

The independent review subsequently reopened the native freeze. See
`helper-symlink-review-repair-20261023.md` for the Helper/EvalSymlinks repair and
fresh validation status. The digest below describes the earlier freeze only.

## Implemented behavior and files

- Pure syntax analysis/formatting and AST summaries: `native/go_runtime/code_analysis.go`,
  `code_analysis_test.go`, `ide_bridge.go`; `lib/go_code_analyzer.dart`,
  `native_go_analysis_ffi.dart`, `native_go_analysis_stub.dart`; and
  `test/go_code_analyzer_test.dart`. Analysis takes exact unsaved source, never
  evaluates it, maps UTF-8 byte positions to UTF-16 offsets, and validates the
  single typed JSON boundary. The shared editor owns debounce/stale rejection.
- Actual embedded package tests, benchmarks and explicit fuzz seeds:
  `native/go_runtime/embedded_testing.go`, `embedded_testing_test.go`, the
  `_test.go` dispatch in `runtime.go`, and vendored `interp/qfli_test_context.go`.
  Compilation, package initialization and the entire suite share one evaluation
  context so initializer-created closures retain valid frames. Benchmarks use
  real `testing.Benchmark`/`testing.PB`; results include native execution proof.
  Parallel tests, mutation fuzzing, race/coverage and process-global test
  environment changes remain explicitly unsupported.
- Raw native results/cancellation: `lib/native_go_result.dart`,
  `native_go_bridge_ffi.dart`, `native_go_bridge_stub.dart`, and
  `test/native_go_result_test.dart`. The editor's result and raw proof share the
  same native execution and cancellation handle. The library loader is shared
  with analysis and handles platform-specific bundled paths.
- Selected test entries and local mobile `go test`: `lib/go_runner.dart`,
  `go_terminal_delegate.dart`, `test/go_toolchain_test.dart`, and
  `go_terminal_delegate_test.dart`. Desktop invokes the actual SDK package test
  command. Mobile accepts only implemented flags; unsupported commands fail
  visibly. SDK child dependency resolution is offline and telemetry uploader
  startup is suppressed without changing global user configuration.
- Surgical coauthored vendor changes: `interp/interp.go` tracks debug workers
  with a session-owned wait group; `interp/run.go` releases the parent frame
  mutex while invoking deferred functions, avoiding a real HTTP callback/
  `httptest.Server.Close` deadlock. Preserve the debugger owner's complementary
  `debugger.go` changes and other agents' compatibility fixes.
- Correct iteration variables: vendored `interp/ast.go`, `cfg.go`, `run.go` and
  `native/go_runtime/loop_variables_test.go`. The condition, body and post share
  the current iteration cell. The next cell is copied at body completion or
  continue, before post. Initializers with `defineStmt` and `defineXStmt` work;
  assignment to an existing variable retains shared-cell semantics. Empty body,
  labeled continue and loops without condition/post also retain control flow.
- Selected entry directory: `project_environment.go`, its existing test helper,
  `runtime.go`, `embedded_testing.go`, `debugger.go`, and new
  `entry_environment_test.go`. The helper now takes explicit project and initial
  directory arguments. All three actual execution modes start in the selected
  entry's directory; their temp base remains `<project>/.qfli/tmp`.

## Regression evidence

All native commands used the pinned local SDK and these process-local resource
limits: `GOMEMLIMIT=512MiB`, `GOGC=20`, `GOMAXPROCS=2`, `GOFLAGS=-p=1`.

1. Working-directory regression was first run against the old callers. Program,
   embedded test and debugger each actually read the root fixture and failed
   with `wrong initial working directory: wrong-root`. The new fixture places
   different `fixture.txt` bytes in project root and `src/`, and selects the
   source/test in `src/`.
2. After the caller/helper repair, all three modes pass. The same test verifies
   `Getwd`, an entry-relative generated file, a temp file under the project temp
   base, absence of the generated file in project root, and unchanged host cwd.
   The embedded test additionally requires one actual passing test in proof.
3. The original loop defect was reproduced as native stdout `01234` for
   `for i:=0;i<5;i++ {fmt.Print(i);if i==1{i++}}`, whose expected output is
   `0134`. Fifteen focused cases now pass, covering mutation, continue, body/
   condition/post closures, multiple variables, tuple/blank tuple initializers,
   empty body, omitted condition/post and assigned external variables.
4. Focused final native command:
   `go test -mod=vendor -run '^(TestSelectedEntryWorkingDirectoryAcrossExecutionModes|TestRunGoForIterationVariables)$' -count=1 .`
   passed in **1.139s**.
5. Final native module `go test -mod=vendor -count=1 ./...` passed in **7.590s**;
   `go vet -mod=vendor ./...` passed. This includes existing original curriculum
   embedded tests, worker panic/cancellation and debugger cleanup regressions.
6. The four owned Dart suites (`go_code_analyzer_test`, `native_go_result_test`,
   `go_toolchain_test`, `go_terminal_delegate_test`) passed **49 tests**, with
   **3 conditional native-library tests skipped** because the fresh final DLL
   was not yet available. `QFLI_GO_TEST_EXECUTABLE` pointed at the actual pinned
   SDK; selected tests, real SDK offline environment, terminal behavior and
   cancellation were executed. The run completed in about 40 seconds.
7. Focused `dart analyze` over all 12 owned Dart source/test files reported
   **No issues found**. `git diff --check` for the edited tracked files passed.
8. The debugger owner separately reported a real WSL `-race` run of all
   `TestDebug` tests passing in **1.186s**, after its final cleanup repair and
   before the subsequent cwd/tuple changes. The earlier Windows attempt failed
   to link with missing `-lgcc_eh`; it is not race evidence. The final full native
   suite includes the new cwd debug case; no final full race run is claimed here.

`GOTELEMETRY=off` was found ineffective: the SDK reads the mode from its stored
configuration, and `go env GOTELEMETRY` returned `local`. The runner now sets
`GO_TELEMETRY_CHILD=2`, which makes telemetry startup skip the uploader process.
Its real-SDK regression verifies the five dependency/toolchain settings through
`go env` and verifies that an executed program inherits the child marker.
The root coordinator owns matching build-script environment changes.

## Final source attribution

The native source digest captured after the final suite/vet and source freeze is:

`7de8ef14fd57854cf1247d406ef76dc02bd39dbf6618832ec5f4959b85f8450b`

Use the same implementation as the corpus auditor, from repository root:

```powershell
python -c "import sys; sys.path.insert(0,'tool/go_curriculum'); import audit_native; print(audit_native.native_source_hash())"
```

`native_source_hash()` recursively sorts native-module files whose suffix is
`.go`, `.c`, `.h`, `.s`, `.S` or `.syso`, plus files named `go.mod`, `go.sum` or
`modules.txt`. Each entry is its POSIX relative path and the SHA-256 of its exact
bytes. The final digest hashes that list's UTF-8 JSON using `ensure_ascii=False`,
`sort_keys=True` and compact separators. This includes vendor and test sources;
it excludes external build scripts/flags, catalogs and produced libraries.
Hash the final DLL/SO and packaged HAP separately. Recompute before attributing a
rebuild/audit; do not reuse this value after additional native edits.

## Review boundaries and remaining integration gates

The project environment is a finite adaptation of exported `os`, `io/ioutil`
and `filepath` operations. It avoids changing host cwd/TMPDIR for those wrapped
calls; it is neither a complete virtual OS nor a security sandbox. Compiled
stdlib helpers that open relative files internally (for example
`template.ParseFiles` or `zip.OpenReader`) do not route through those exports;
native `*os.File` methods such as `Chdir` also retain their host behavior.
Do not generalize the tested operations to complete filesystem/cwd isolation.

The requested independent read-only review found no other blocking issue in
the macOS architecture/SDK/lipo/rpath/copy/signing flow, audit profile byte
restoration, or HAP asset/runtime/ELF/export comparison. Build scripts needed
the same telemetry child marker; that finding was handed to the root owner.

The root coordinator must rebuild the final DLL and all five bundled Android/
OHOS ABIs from the final sources, run the three skipped actual-FFI cases and
other adapter tests against that DLL, refresh corpus/runtime hashes, build and
inspect the audit HAP, and execute on an actual OHOS target when available.
Earlier DLL/ABI batches are intermediate artifacts. A host pass or archive
inspection is not device evidence; no full-product or OHOS completion is claimed.
The verifier was explicitly told to map displayed-import data to the selected
package directory and preserve expectations, rather than hide cwd failures.
