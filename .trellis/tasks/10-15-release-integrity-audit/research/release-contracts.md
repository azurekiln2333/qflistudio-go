# Release integrity contracts

## 1. Scope / trigger

These contracts cover the shared terminal hook, embedded Go build constraints,
offline product policy, and curriculum verification. They supplement the local
ignored `.trellis/spec/` documents and are committed with the release task.

## 2. Signatures

- `StudioProfile.terminalCommandDelegate(SandboxShellBackend, String)` is shared
  by the standalone terminal and editor TerminalPane.
- `GoToolchain.runTerminalCommand({required String workingDirectory,
  required List<String> arguments})` forwards a complete Go command to the SDK.
- `GoTerminalDelegate.handle(backend, command)` returns whether it claimed a line.
- Yaegi `buildConstraintsOk(*build.Context, []*ast.CommentGroup) (bool, error)`
  owns source constraint evaluation; do not add a second source filter.
- `verify.py [--go PATH] [--only IDS] [--race]` returns nonzero on any failure.

## 3. Contracts

- Only simple exact `go`/`go.exe` commands are claimed. Preserve quoted operands
  with the sandbox's `EscapePolicy.backslashLiteral`; compound lines stay with
  the shell. Desktop preserves cwd, actual output/status and process cancellation.
  Close child stdin, and drain stdout/stderr concurrently.
- Mobile supports only `go run <single file or directory>` through the same
  GoProgramRunner as editor Run. Resolve paths through the sandbox; a directory
  uses RunnerService entry selection. Unsupported commands report not-run, never
  an empty successful result. Learner programs are not an OS security sandbox.
- Native build directives come from raw line-comment AST nodes. A single modern
  `//go:build` expression takes precedence over legacy `// +build`; duplicate or
  malformed modern directives are errors. Block-comment text is documentation.
  Retain the existing tag predicate and vendored fixes after dependency refresh.
- Native stdout is buffered until completion. Device cancellation tests must
  wait for a project-local marker written inside main, then interrupt; waiting
  for live stdout deadlocks the test's own synchronization.
- `offlineOnly` hides account/Git/cloud/AI entrances and blocks Home/Profile
  refresh plus task-activity remote queue/sync. Local activity statistics persist;
  existing queued remote events remain available when an online product resumes.
  Online products retain their behavior. This is product policy, not a ban on
  network operations in learner-authored programs or the host shell.
- Explicit `--go` is resolved to an absolute existing executable before sample
  cwd changes; a missing explicit SDK is an error, never an implicit fallback.
  Explicit `--race` requires exact `RACE-OK` for each requested item. Gate errors,
  missing results, timeout and nonzero WSL exit fail the requested verification.

## 4. Validation and error matrix

| Condition | Required result |
| --- | --- |
| Desktop bare `go` | Real SDK help and status, including nonzero usage status |
| Mobile `go build/test/fmt/vet/mod` | Diagnostic and `kProgramNotRunExitCode` |
| Unsupported backend, bare/subcommand | No-runtime diagnostic and not-run status |
| Escaping mobile operand | Terminal diagnostic; no uncaught exception |
| Excluded selected source | Entry/build error; no sibling-main fallback |
| Duplicate/invalid modern constraint | Actual parse/duplicate diagnostic |
| Block-comment pseudo-directive | Ignore as a build constraint |
| Offline restored token | No background account/activity HTTP request |
| Missing explicit SDK/race result | Failed verification and nonzero CLI exit |

## 5. Good / base / bad cases

Good: both terminals run `go run main2.go` through their shared profile delegate,
with helpers preserved and only the selected main producing output.

Base: ordinary desktop package commands use the real SDK in the current terminal
directory; mobile single-file execution uses the embedded interpreter.

Bad: claiming mobile `go test` succeeded without a toolchain, evaluating stripped
CommentGroup.Text as build directives, or printing a green total beside RACE-FAIL.

## 6. Required tests

- Real-SDK delegate tests cover bare/help/run/build/test/vet/fmt, cwd, quoted and
  Unicode paths, compile errors, cancellation, and both terminal widgets.
- Native interpreter tests cover selected/helper/imported sources, modern enabled
  and disabled tags, legacy precedence, malformed/duplicate directives and block
  comments. Rebuild all five bundled libraries after native/vendor edits.
- Device integration covers FFI selected entries, panic/os.Exit, cancellation,
  terminal file/directory execution and honest unsupported-command refusal.
- Offline tests use restored tokens with an HTTP request counter, include online
  controls, check local statistics/pending retention and hidden Git shortcuts.
- Curriculum verifier tests assert nonzero exit for race FAIL/missing/gate error,
  ordinary mode unchanged, and relative SDK paths surviving sample cwd changes.

## 7. Wrong vs correct

Wrong: wait for a buffered `running` stdout line before cancelling native Go.
Correct: wait with a bounded deadline for a file written after main starts,
interrupt, await completion, and assert `^C` plus a cleared terminal exit status.

Wrong: inspect `race` only as report metadata.
Correct: accept only `RACE-OK`, include every failure in the overall failure count,
and propagate a nonzero process result.
