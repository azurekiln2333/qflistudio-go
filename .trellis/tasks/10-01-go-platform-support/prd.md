# Go Platform Support

## Goal

Audit the Go compiler/interpreter execution paths outside OHOS, implement missing
native-platform integration, and verify platforms that this host can run. Skip
runtime tests for platforms without a working local toolchain or device.

## Existing evidence

- Android/OHOS have bundled Go/Yaegi libraries exposed through a C ABI.
- Windows/Linux/macOS already invoke the official Go SDK for run/build/test,
  formatting, vet, and module tidy.
- iOS currently falls through to an unavailable process toolchain and has no
  native archive build/link setup.
- Runtime metadata marks only OHOS as available despite Android integration.
- A connected Android x86_64 emulator is available. The Windows Go SDK is cached
  in native/build/go-sdk-1.27.1. WSL distributions need availability checks.
- macOS/iOS toolchains and devices are unavailable on this Windows host.

## Requirements and acceptance

1. Preserve working OHOS and Android C ABI signatures and execution behavior.
2. iOS must select the embedded interpreter, load its statically linked symbols,
   and have an Xcode-driven archive build/link setup for device and simulator.
3. Desktop platforms must retain the official Go SDK backend and its commands.
4. Report runtime implementation and SDK prerequisites accurately; Android must
   not be classified as missing, and unsupported targets must remain explicit.
5. On available platforms, verify real execution, error handling, cancellation,
   and toolchain commands; fix any concrete defects uncovered.
6. Record the exact host/device evidence and distinguish inspected integration
   from actual execution. Do not attempt Apple runtime tests on Windows.
7. Preserve prior startup/content changes, unrecognized edits, and existing
   project navigation. No unrelated repository or system configuration changes.

## Validation

Windows: official SDK command tests and native runtime source tests where the
host compiler configuration permits. Android: Flutter FFI integration on the
connected emulator and package ABI evidence. Linux: run tests only if a WSL
instance starts and required tools exist. Apple: source/config review, with the
absence of device execution clearly recorded. Flutter analysis and relevant
application regressions apply on this host.
