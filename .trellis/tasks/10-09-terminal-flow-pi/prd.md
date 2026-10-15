# Continuous terminal and current-file Go execution

## Goal

Verify that the Java terminal changes apply to Go and make Run execute the intended Go entry. Codex directs Pi in the right Herdr pane and verifies its work.

## Confirmed background

- The user approved task creation and explicitly requested a right-hand Pi worker. Pi is running in w8:p2 as pi-go-terminal.
- pubspec.yaml consumes ../qfli_studio_core. Java already changed the shared terminal and editor, including the inline prompt and long-press active-file selection.
- GoToolchain.execute in lib/go_runner.dart still invokes go run .; the selected entry determines only the directory. Selecting another main in the same directory does not select that source.
- Go, Java and shared core contain pre-existing uncommitted work. Other language sessions are active. Shared-core source is read-only for this worker unless a needed change is explicitly coordinated.

## Requirements

- R1: Confirm which Java changes landed in shared core and apply to Go. Reuse the working terminal implementation.
- R2: Commands, stdout, stderr and the next prompt form one top-aligned scrollback. Preserve long-output scrolling; no split input/output regions or run cards.
- R3: A successful run emits no completion sentence or exit-code-zero line. Use concise terminal labels; preserve application output, including Chinese text, and real failure diagnostics.
- R4: Tap Run executes the configured main entry. Long press executes the file active when the gesture fires exactly once. A subsequent tap still runs main. Do not rewrite project entry metadata.
- R5: Keep the existing save/run flow, helper files, standard multi-file Go projects, module context, cancellation, and build/test/format/vet/tidy actions.
- R6: Cover official desktop execution and the bundled mobile interpreter. Invalid current-file selections must remain rejected without falling back to the main entry.
- R7: Pi owns the bounded Go implementation and focused tests; Codex owns planning, shared UI verification and final review. Preserve unrelated work.

## Acceptance criteria

- AC1 (R1-R3): Current shared terminal/editor tests pass from Go; visual inspection confirms top alignment, an inline prompt, long-output scrolling and no split run surface.
- AC2 (R4): With main2.go active and main.go configured, tap / long press / tap run main / main2 / main exactly once without changing entry metadata.
- AC3 (R5): Sibling helper declarations and project-local module imports continue to work. Existing tool actions retain their semantics.
- AC4 (R4-R6): Desktop and interpreter tests assert actual selected-entry output and diagnostics, rather than only mock arguments. Cancellation remains covered.
- AC5 (R3): User stdout remains intact; successful runs are quiet and nonzero statuses stay visible.
- AC6 (R7): Review the delta from this session and record relevant Flutter/Go checks, actual platform coverage and limitations.

## Out of scope

New PTY transport, Java runtime changes, navigation/startup redesign, SDK reinstallations, default-entry metadata changes and unrelated shared-core/sibling-app edits.

## Approval

The user approved the final design on 2026-10-09: implement the Go entry-selection fix, concise titles, regression tests and rebuilt mobile runtime libraries. The task is in_progress. Pi owns implementation in the right Herdr pane; Codex verifies and coordinates.
