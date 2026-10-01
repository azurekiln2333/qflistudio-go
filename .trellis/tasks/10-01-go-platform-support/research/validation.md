# Platform Validation And Acceptance Audit

## Verified host evidence

- Flutter SDK: `D:/ProgramFiles/flutter_ohos`; bundled Dart/tool snapshot used
  after the shell launcher stalled. No SDK files or global environment changed.
- Windows official Go SDK: `native/build/go-sdk-1.27.1/go/bin/go.exe`,
  reporting `go1.27.1 windows/amd64`. It is not on the host PATH. Tests use
  `QFLI_GO_TEST_EXECUTABLE`; deployed desktop apps require Go on their PATH.
- Android: `emulator-5560`, `sdk_gphone16k_x86_64`, `emu64xa16k`.
- Linux: WSL distro `qfli-java-build`, x86_64, `/usr/bin/cc`, Python 3.12.3.
  Official Go 1.27.1 Linux archive downloaded with WSL after Windows TLS
  failures, then verified against official download metadata SHA256:
  `63d339f0da5ab53635a56f2490a7984dfe12dfcff22ad749f63edaf590168445`.
  SDK and caches remain under ignored `native/build/`.
- The default Ubuntu WSL registration is broken; it was not repaired.
- `hdc list targets` currently returns `[Empty]`. No OHOS device rerun.
- No macOS/Xcode/Apple target available. No Apple build or runtime tests.
  No Windows GUI build or Linux Flutter GUI test was attempted.

## Current check results

| Check | Result |
| --- | --- |
| Complete Flutter application suite, official Windows SDK enabled | 38 passed, none skipped |
| Flutter analysis | No issues |
| Windows official SDK regression | All 4 tests pass, including six actions, errors/prerequisites, module execution and cancellation closing pipes |
| Windows native Go module | All 8 top-level tests and vet pass; CGO_ENABLED=0 because no host C compiler is installed |
| Android real FFI integration | All 3 tests pass |
| Android package ABI check | arm64-v8a, armeabi-v7a and x86_64 libraries present |
| Android native ELF LOAD alignment | Every segment has 0x4000 (16 KB) alignment for all three ABIs |
| Linux SDK backend | run, build, compiled program output, test, fmt, vet, invalid source, mod tidy and module run pass |
| Linux native Go module | All 8 top-level tests and vet pass; CGO_ENABLED=1 |
| iOS build script static check | bash -n passes; SDKROOT/architectures/deployment/link configuration reviewed |
| iOS/macOS runtime or build execution | Skipped: Apple host/toolchain unavailable |

Linux backend diagnostics are generated in `native/build/linux-sdk-verification.json`.
They validate actual SDK/source behavior and do not imply Flutter Linux GUI tests.

## Regression harness fixes

Two content import/reopen cases stalled when `tester.runAsync(store.refresh)`
waited on registry writes queued in the fake-clock zone. `_refreshProjects` now
keeps pumping while real filesystem/isolate callbacks finish. Both cases and
all 17 content-import regressions pass; no shared-core production code changed.

## Requirement audit

1. Preserved Android/OHOS C ABI and libraries. Actual Android FFI tests pass.
2. iOS uses the embedded backend/process symbols, with an Xcode c-archive phase
   and retained exports for run/cancel/free across Debug/Release/Profile.
3. Desktop official SDK commands preserved; Windows app service and Linux
   backend/source checks pass within the available host boundaries.
4. Shared platform mapping fixes Android availability, marks desktop SDK
   prerequisites, and leaves unsupported targets explicit. Three mapping tests pass.
5. Available checks exercise real output, invalid code, panic/exit recovery,
   cancellation, SDK commands, and concurrent native output.
6. Recorded exact host/device evidence and all unexecuted Apple/GUI/OHOS checks.
7. Prior startup and content implementation remains intact; three startup
   regressions and the full application suite pass. No sibling repository edits.
   No commits, remote operations, or unrelated system configuration changes.

## Delivery Verification, 2026-10-02

The cross-product audit staged only the platform runtime changes. In
`lib/main.dart`, the foundation/platform imports and runtime metadata were
selected against HEAD; the separate native-startup work remains in the working
tree. The actual index was exported into qfli_web's ignored `go-staged` directory.
Only this verification copy used absolute shared-core dependency paths.

That source passed all 18 deliverable tests and full static analysis. The
official Windows SDK was enabled, so SDK operations and cancellation were
executed rather than skipped. The earlier 38-test working-tree result includes
startup/content changes outside this native platform commit.

The first export checks encountered Dart/Go compiler memory-allocation errors
on the Windows host. The successful retry used Flutter `--concurrency 1`,
`GOMAXPROCS=2`, and `GOFLAGS=-p=1` only in the verification process. The exported
entry and package compiled cleanly; no product concurrency settings were changed.
