# Implementation plan

1. [x] Inspect Go dependency and the Java/shared-core changes. Start Pi in right Herdr pane w8:p2 and obtain focused audit.
2. [x] Run current shared terminal/editor tests from Go (22 passed), render five viewport/theme cases and visually inspect all five images.
3. [x] Finish Pi's disposable real-SDK overlay proof; record research/pi-audit.md. Review the final planning summary with the user before task.py start.
4. [x] After activation, assign Pi the Go entry selector, desktop overlay lifecycle, native filtered source view, concise titles and focused regression tests. Read trellis-before-dev and curated context before edits.
5. [x] Verify actual main / main2 / main output with both entries and helper present, plus comments/literals/method names, module imports, platform-excluded files, selected no-main failure and normal package execution.
6. [x] Run targeted Flutter tests and analysis, native Go tests and vet. Keep build/test/format/vet/tidy and cancellation tests.
7. [x] Rebuild all three Android and both OHOS runtime libraries with existing local SDKs. Inspect binary ABI/alignment and exercise native integration on available connected targets. Record unavailable platforms explicitly.
8. [x] Run the full Go app Flutter suite with official SDK checks enabled, review the exact changed files independently and fix findings.
9. [x] Update executable entry/terminal contracts, inspect narrow git scope and record final validation evidence.
10. [x] Finalize under the authorized 10-15 release-integrity-audit parent: native work committed as 4ace2f4, Dart/delegate as df2f46d, canonical formatting as 7502c08. Current full suite111/111, five native libraries and fresh Android/OHOS unsigned packages verified. Android API37/x86_64/16KB emulator integration5/5 and normal release restoration passed. Current OHOS signed install/FFI remains externally blocked; Android arm64 device execution is unverified. Parent research/release-validation.md is authoritative; archive/journal follow reviewed evidence commits. Earlier confirmation waits and historical device counts do not describe the current release state.

## Commands and resource limits

- Flutter: D:/ProgramFiles/flutter_ohos/bin/flutter.bat; tests use --no-pub and --concurrency 1. Product release builds use --pub so the Flutter OHOS SDK regenerates plugin registrations in release mode and excludes integration_test.
- Set QFLI_GO_TEST_EXECUTABLE to the absolute native/build/go-sdk-1.27.1/go/bin/go.exe for SDK tests.
- Use process-local GOMAXPROCS=2 and GOFLAGS=-p=1 on this busy Windows host.
- Windows native checks: CGO_ENABLED=0, go test -mod=vendor ./..., go vet -mod=vendor ./... inside native/go_runtime.
- Rebuild: tool/build_go_runtime.ps1 with the existing Windows Go SDK, pinned OHOS Go SDK, Android NDK and OpenHarmony SDK paths.
- flutter test --no-pub --concurrency 1 ../qfli_studio_core/test/terminal_pane_test.dart ../qfli_studio_core/test/editor_run_test.dart
- flutter test --no-pub --concurrency 1 .trellis/tasks/10-09-terminal-flow-pi/research/terminal_visual_test.dart
- flutter analyze --no-pub; flutter test --no-pub --concurrency 1

## Ownership and safety

Pi may edit lib/go_runner.dart, a focused Go entry-selector helper, lib/native_go_bridge_ffi.dart, lib/native_go_bridge_stub.dart, native/go_runtime/runtime.go, its tests, Go runner/selector/widget tests and integration_test/go_native_test.dart. Generated mobile libraries are refreshed from those sources after code review. Codex owns task artifacts/specs/review.

Do not write sibling repositories or change shared APIs. No broad cleanup, hard resets, source rewrites or global environment changes. Scratch work belongs in .artifacts/terminal-flow-pi. Verify the resolved absolute path stays in that directory before any recursive deletion.
