# Independent Go release review

Review workspace: `D:\MyNewProjects\qfli_go`; both `Get-Location` and
`git rev-parse --show-toplevel` matched this path. Initial ownership was report
only. After the runtime worker froze its patch, the coordinator transferred
bounded ownership of `native/go_runtime/vendor/github.com/traefik/yaegi/interp/build.go`
and `native/go_runtime/runtime_test.go` for the two mechanical issues below.
This reviewer stages/commits nothing and does not mutate shared-core or sibling
language repositories. Review began against branch `fix/go-release-integrity`.

## Scope and positive findings

- Read the parent check manifest, PRD, design, execution plan, native-runtime,
  selected-entry, content-import, curriculum-tooling and editor-terminal specs.
- `lib/go_entry_selector.dart` and the run branch of `lib/go_runner.dart` retain
  package compilation through a temporary Go overlay. Helpers, local imports,
  embedded assets and normal build filtering remain in the compiler context.
  Source files and entry metadata are not rewritten. Files without a selected
  runnable main are not replaced with another known main.
- `native/go_runtime/runtime.go` filters only the selected entry directory, uses
  Go AST facts, preserves parser/helper diagnostics, and verifies that the actual
  interpreter package has a main. The cached-package lookup does not call main
  again. Existing output synchronization and vendored panic/cancellation paths
  remain intact.
- Re-read the frozen terminal delegate after the worker's fixes. The profile is
  wired once; shared standalone and editor terminals consume that same field.
  Desktop commands use the real SDK in the backend cwd, preserve quoted operands,
  expose real status/diagnostics, and close stdin because there is no interactive
  stdin flow. Bare Go, missing SDK, unavailable targets and mobile unsupported
  subcommands receive explicit results. Mobile file/directory resolution uses the
  sandbox boundary and the existing runner. No additional concrete defect was
  found in these updated delegate paths.
- Shared content integration and the 120-topic compiler/semantic audit were
  reviewed through the coordinator/worker evidence; this reviewer did not rerun
  the complete curriculum or mutate aggregate assets.

## Findings and resolution

### P1: Modern build constraints are ignored by the embedded interpreter

Files: `native/go_runtime/vendor/github.com/traefik/yaegi/interp/build.go:15`
and `:36`; `native/go_runtime/runtime.go:253`; coverage gap in
`native/go_runtime/runtime_test.go:28`.

The vendored build filter recognizes legacy `// +build` lines only. A selected
file using a modern, false `//go:build` expression is compiled and executed, so
the post-evaluation main lookup reports success for a source excluded by the
official Go build rules. Retained helper/imported sources can likewise be
included incorrectly. Existing ignored-entry coverage exercises the legacy form.

Verified without modifying repository tests: a temporary Go compiler overlay
replaced the test input with the following case, then ran the pinned SDK with
`go test -mod=vendor -overlay <temporary-json> -count=1 -v ./...`:

```go
// selected.go
//go:build qfli_never_enabled

package main
func main() { println("SELECTED") }
```

The same directory contained `other.go` with a different main. Calling
`runGo(project, selected)` returned `{Stdout:SELECTED\n Stderr: ExitCode:0}`.
The probe's assertion that an excluded selected source must fail returned test
exit 1. The temporary overlay and probe files were then deleted.

Recommendation sent to main: fix modern-expression support in Yaegi's existing
build filter, cover selected/retained-source behavior and invalid expressions,
preserve legacy filtering, and rebuild all bundled native libraries afterward.
Main assigned this to the existing runtime worker; coordinator owns rebuilding.

Resolution: the runtime worker added `go/build/constraint` expression evaluation
from raw AST comment text and actual interpreter tests for selected sources,
helpers, imported sources, enabled/invalid expressions and legacy compatibility.
Review of this patch found two additional mechanical discrepancies:

- Duplicate modern directives were evaluated as AND. Actual pinned SDK execution
  rejects them with `multiple //go:build comments`; the first native patch ran
  the program with exit 0 when both expressions were enabled.
- A `//go:build` line written inside a `/* ... */` documentation comment was
  interpreted as a real directive. Actual pinned SDK execution includes that
  file; the first native patch incorrectly excluded it.

After the owner froze its files, this reviewer fixed both in the existing filter:
only actual line-comment nodes can contribute directives, and a second modern
directive returns an error before tag evaluation. Interpreter regressions cover
enabled/disabled first directives and block-comment text with/without a genuine
enabled directive. `gofmt`, full native tests and vet pass. Final native source
was explicitly frozen and handed to main for the five-library rebuild; rebuilding
and device execution are still separate coordinator gates.

### P2: Explicit race verification can report a failing gate as success

File: `tool/go_curriculum/verify.py:362` (original reviewed revision), plus
`run_race_gate` at `:306`.

`--race` stores the gate result in the record but never rejects `RACE-FAIL` or
the missing-result fallback `RACE-SKIP`. `run_race_gate` also does not check the
WSL process exit status. Consequently this explicit verification mode can return
0 after its race gate fails.

A controlled probe imported the real module, directed `EVIDENCE_DIR` to a
temporary directory, replaced compiler verification with a successful record,
and replaced the race callback with `{T001: RACE-FAIL}`. The actual
`main(['--only', 'T001', '--race'])` printed:

```text
OK   T001 stdout-exact variant=mock-probe race=RACE-FAIL
VERIFY: 1 passed, 0 failed
REVIEW_RACE_MAIN_EXIT 0
```

Expected: explicit `--race` requires an actual `RACE-OK`; failure, absent result
or a failed WSL command produces a failed item and nonzero overall status. Main
assigned the tooling fix to the existing curriculum worker. This does not
invalidate the 120 ordinary compiler checks, which did not claim race coverage.

Resolution: the curriculum owner now requires `RACE-OK`, reports missing/error
results as failures, counts only successful records as passed, and rejects a
nonzero WSL status, timeout or unavailable WSL executable. This reviewer ran the
owner's five regression tests successfully and separately drove the real
`run_race_gate` through mocked nonzero/timeout/missing-executable subprocess
results; all three raised `VerificationError` as required. No real race execution
is claimed from these controlled tests.

## Verification performed by this reviewer

Pinned SDK: `D:\MyNewProjects\qfli_go\native\build\go-sdk-1.27.1\go\bin\go.exe`.
Verification-only environment: `GOMAXPROCS=2`, `GOFLAGS=-p=1`,
`GOTOOLCHAIN=local`.

- Dart analyzer over `lib/go_entry_selector.dart`, `lib/go_runner.dart`,
  `lib/go_terminal_delegate.dart`, and their three focused test files: exit 0,
  `No issues found!`.
- Focused native tests for selected sibling mains, ignored entries, helper
  diagnostics, pre-cancellation, worker panics and concurrent output: exit 0;
  six top-level tests plus their subcases passed.
- Modern-build-expression regression probe: failed as expected before the fix,
  establishing the P1 reproduction above.
- Race-status control-flow probe: established the P2 false-green result above;
  real race execution was not claimed by this probe.
- Native `go vet -mod=vendor ./...`: exit 0.
- After the final filter fixes, full native `go test -mod=vendor -count=1 ./...`:
  exit 0 (`ok qfli_go/native/go_runtime 1.789s`), followed by native vet: exit 0.
- `python -m unittest tool/go_curriculum/test_verify_race.py -v`: all five
  regressions passed. Additional subprocess-failure control-flow probes passed
  for nonzero exit even with an apparent success marker, timeout and missing
  executable.

Full Flutter/shared regression execution, native artifact rebuilding,
Android/OHOS builds and device tests remain coordinator-owned. These were not
claimed as passed from source review. Both concrete review findings are resolved
in source and tests; no additional unresolved finding remains within this
reviewer's scope. Final release readiness still depends on coordinator-owned
packaging and device evidence.
