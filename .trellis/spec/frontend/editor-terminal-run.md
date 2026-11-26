# Editor Terminal and Run Gestures

Execution policy: apply `AGENTS.md` and [Cloud-Only Execution](../backend/cloud-only-execution.md).
All development verification commands below run only in GitHub-hosted Actions.
Descriptions of user-facing Run/terminal behavior are not local agent execution
permission. The canonical sibling is `../qflistudio-core`; historical
`../qfli_studio_core` examples describe the previous layout. Shared-core edits or
inspection require their owner's assignment through the coordinator.

## 1. Scope / Trigger

The Go app imports the editor and TerminalPane from ../qfli_studio_core. Read that working tree before changing layout or gestures: multiple language apps consume it, and another session may already own a shared change.

## 2. Signatures

    EditorPage._runProject({String? entryOverride})
    EditorPage._runActiveFile()
    RunnerService.runProject({required String projectPath,
                              required String entryFile})
    TerminalPaneState.attachOutput(
      title: ..., stdout: ..., stderr: ..., exitCode: ..., cancel: ...)

Keep the existing ProgramRunner handoff. Go-specific entry execution is documented in ../backend/go-entry-selection.md.

## 3. Contracts

- Tap the Run button to resolve the project entry. Long press captures the active file and runs it once. A following tap still resolves the configured entry.
- Validate missing/deleted/unsupported/out-of-project selections before saving or dispatching. Do not silently fall back to the default entry.
- Save edited sources through the existing editor flow before running; do not change configured entry metadata.
- Commands, stdout, stderr and the following prompt are one top-aligned scrollback. The prompt is the last scrollback row, not a fixed bottom form.
- Preserve long-output scrolling, short viewports, large/long paths, session switching, command history, Enter submission and cancellation.
- Suppress preparation chatter and successful completion/exit-code-zero banners. Preserve program-authored text, including Chinese stdout. Nonzero status and actual errors remain visible.
- Use short terminal labels and commands; do not add runtime implementation suffixes such as (JDK) or expose internal temporary paths.
- In-flight output and completion belong to the originating terminal session.

## 4. Validation & Error Matrix

| Interaction/state | Expected result |
| --- | --- |
| main2 active, main configured; tap / hold / tap | main / main2 / main, each once |
| Dirty valid active source | Saved before runner sees it |
| Missing or invalid active source | Clear error, no default fallback |
| Successful run | Preserved output followed immediately by prompt |
| Failed run | Real diagnostic and nonzero status |
| Long output / small viewport | Output and prompt scroll together |
| Session switch during a run | Output remains in source session |
| Running button activated again | Disabled/no duplicate launch |

## 5. Good / Base / Bad Cases

Good: the last output line is immediately followed by the next prompt at the same line rhythm.

Base: an empty terminal starts at the top; successive runs append into the existing transcript.

Bad: a fixed input strip below a divider, a separate run-output card, a mandatory success banner, or a long press that also triggers a normal click.

## 6. Tests Required

Run the current shared terminal/editor tests from the Go app:

    flutter test --no-pub --concurrency 1 ../qfli_studio_core/test/terminal_pane_test.dart ../qfli_studio_core/test/editor_run_test.dart

Pair shared gesture tests with real Go runner/native entry-selection tests. Do not claim actual selected-file execution from a mock-path assertion alone.

Inspect real TerminalPane renders for desktop, phone dark/light, a short viewport and long project paths. Fixtures belong in test/research artifacts, never in product data.

## 7. Wrong vs Correct

Wrong: pin an input TextField beneath the output list.

Correct: place the prompt after the output lines in the same naturally scrolling content. Keep its width within the pane and its height consistent with the terminal text.

## Go terminal delegate (2026-10-15)

Both terminal surfaces consume `goProfile.terminalCommandDelegate`. It claims
simple exact go/go.exe commands using backslashLiteral tokenization. Desktop
forwards real SDK commands in backend.cwd, preserving output/status/cancel and
closing stdin, with the product's offline child environment. Mobile accepts
go run and the supported simple go test package/file forms through
GoProgramRunner's embedded engine; unsupported flags, build, dependency download,
coverage, race and mutation fuzz commands report not-run. Directory selection uses
RunnerService.findEntry. Non-Go/compound lines return to the shared shell.
Tests must cover both actual widgets, SDK commands and mobile refusal/path rules.
See release audit `research/release-contracts.md` for the error matrix.

The selected `_test.go` Run action executes actual package tests, benchmark
loops and registered fuzz seeds. Preserve its typed NativeGoResult evidence;
do not report complete SDK equivalence. The ordinary Run action remains separate
from StudioProfile.debugger; explicit Debug consumes GoStudioDebugger and the
shared controller's capabilities. Disk-only debug must save sources before
launch and never discard dirty buffers implicitly.
