# Design

## Change boundary

The real gap is native iOS execution and archive packaging, plus inaccurate
platform metadata. The existing mobile interpreter and desktop official SDK
remain their respective backends.

- Shared Go-platform selection: one small Dart module identifies mobile native,
  desktop SDK, or unsupported execution. Runner, profile, and integration skip
  conditions consume that same decision.
- FFI bridge: select DynamicLibrary.process() on iOS; retain the existing .so
  loader on Android/OHOS. Run and cancel resolve the same library consistently.
- Apple build: an iOS build script uses the macOS Go SDK and Xcode SDK/architecture
  settings to create a c-archive; an early Xcode phase builds it, and linker flags
  retain and export all three ABI entry points for Dart lookup.
- Existing runtime source and desktop SDK commands are changed only when real
  platform validation exposes a defect.

## Compatibility

The C ABI remains QfliGoRun, QfliGoCancel, and QfliGoFree. Do not add a second
interpreter or route desktop users away from the official Go compiler.
The iOS interpreter executes code within the process; it does not spawn Go SDK
commands. Desktop operation still requires an installed/discoverable official
SDK. Browser execution does not have native FFI or local SDK processes.

## Verification ownership

The main session owns Dart selection/profile/bridge, platform validation, docs,
and the final audit. After the Apple worker could not start because of an account
concurrency limit, the main session also implemented the iOS build script,
Xcode build/link settings, and Apple review note. All other edits are
preserved. Apple execution is not attempted without Apple tools/device access.
