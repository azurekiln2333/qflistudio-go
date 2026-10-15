# Final independent source review

## Scope and workspace

Reviewer verified both the current directory and Git top-level as
`D:/MyNewProjects/qfli_go`. The only shared dependency inspected was
`D:/MyNewProjects/qfli_studio_core`. No sibling language project was read or
modified. Source/build ownership was frozen by the coordinator; this review
changed only the integration test after explicit coordinator authorization and
this report. No Git, pub, build, clean, device, or asset-generation operation was
performed by this reviewer.

Read the task check context, PRD, design, execution plan, native runtime/import
specs, and release contracts before review.

## Findings (fixed)

### Device integration target omitted the real Go profile

File: `integration_test/go_native_test.dart`.

The integration target defines its own `main()` and previously never installed
`StudioProfile.current`. Its directory-terminal regression creates `main.go` at
the project root and calls `go run .`. The actual delegate calls
`RunnerService.findEntry`, whose generic candidates contain `src/main.go` but
not root `main.go`; root `main.go` is supplied by `goProfile.entryFileNames`.
Consequently this test would report not-run on a mobile device even though
normal product startup installs the correct profile.

Fix: import only `goProfile` from the product entry module. Per-test setup saves
the previous profile and installs the real Go profile; teardown restores the
previous value. The existing real directory-execution/output assertions are the
behavioral regression. This leaves the marker-based interrupt synchronization,
all five integration cases, product code, and native libraries unchanged.

## Findings (not fixed)

No additional actionable source defect was found in this bounded final review.
Packaging, signing, device execution, and full-suite outcomes remain separate
coordinator-owned gates and are not inferred from this source review.

## Source paths and contracts verified

- Both terminal surfaces read the same product hook:
  `pages/terminax_terminal_page.dart` installs it on `TerminalManager` initially
  and when creating sessions; `editor/terminal_pane.dart` passes it to the
  shared sandbox factory. `goProfile` registers `goTerminalCommandDelegate`.
- `GoTerminalDelegate` accepts exact `go`/`go.exe` command basenames and leaves
  compound/invalid shell syntax to the shared backend. Desktop invocation uses
  actual SDK arguments/cwd/output/status/cancellation and closes child stdin.
  Bare `go` reaches the SDK. Mobile only accepts one local `go run` operand,
  resolves it through the sandbox, uses the same runner/entry selection as the
  editor, and reports unsupported commands with a not-run exit code. The
  unsupported-platform and native-load fallback paths produce diagnostics.
- Selected-entry execution keeps helpers, imported sources and build rules in
  the normal compiler/interpreter paths while removing competing main files.
  Native modern directives are read from raw leading line-comment AST nodes;
  duplicate/invalid directives fail, block-comment documentation is ignored.
  The prior independent native/race review and fixes are preserved.
- The interrupt integration test waits for a bounded project-local marker after
  main begins, then calls the real backend interrupt and awaits execution. It
  does not wait for native stdout, which is buffered until completion.
- Core `offlineOnly` guards hide account/cloud/Git/AI entry points and editor
  online-terminal controls. Home/Profile refresh and task-event queue/sync
  guards preserve local statistics and existing pending events. Expanded
  shortcuts hide network presets and Git; Go receives only the shared offline
  tools. Startup `auth.load` reads local storage rather than refreshing HTTP.
  Learner-written code and manual host-shell commands retain their documented
  capability boundary.
- Go offline regressions mount real shared widgets and the real Go profile.
  Background-request assertions use residual trusted tokens, real-I/O drains
  and online controls; the shared shortcut tests cover offline/online behavior.
- Core commit `a838c25` validates and returns the exact non-Java filename before
  filesystem/project creation. Java normalization remains on its separate path.
  Regression tests cover ASCII/control/Unicode surrounding whitespace across
  resolve/open/import/new-project operations, absence of writes, and valid
  mixed-case filenames with internal spaces and exact code bytes.
- The generic ToolsGrid text-scaling change remains owned by Web/core; its
  shared extent calculation and 320px/2x regression are present. No Web-specific
  content was moved into Go by this reviewer.

## Verification

- Lint/type check: `flutter analyze --no-pub
  integration_test/go_native_test.dart` exited 0, `No issues found!` (1.7s),
  after the profile setup fix.
- Tests: source assertions reviewed; no duplicate Flutter/native suite or device
  run was started because the coordinator owns those serialized release checks.
  The corrected integration file is ready for its coordinator-owned device run.
- Final reviewer source freeze: `integration_test/go_native_test.dart` and this
  report are handed back to the coordinator for verification and commit.

## Canonical formatting follow-up

Coordinator authorized only canonical formatting of
`lib/go_terminal_delegate.dart`, `test/go_curriculum_content_test.dart`,
`test/go_offline_profile_test.dart`, `test/go_terminal_delegate_test.dart`, and
`integration_test/go_native_test.dart`. Applied the pinned Dart 3.11.5 formatter
at `D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/bin/dart.exe` and inspected
the complete before/after unified diff. Changes are line wrapping, indentation,
and formatter-managed trailing commas; no expression, assertion, string literal,
fixture source code, or runtime behavior changed.

- Whole-tree format gate: `dart format --output=none --set-exit-if-changed lib
  test integration_test` exited 0: `Formatted 17 files (0 changed)`.
- `flutter analyze --no-pub` with those five explicit paths exited 0:
  `No issues found!` (2.0s).
- No tests were added or rerun for formatting. No pub, build, device, or Git
  operation was performed. All five files and this report are frozen again.
