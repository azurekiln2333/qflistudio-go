# Apple Integration Review

## Implemented boundary

- The main session implemented Apple files after the delegated worker could
  not start because of an account concurrency limit; no worker edits existed.
- Runner routing selects the embedded backend for iOS. Both FFI run and cancel
  resolve the process library, preserving the three C ABI signatures.
- Runner invokes the archive build phase before Sources/Frameworks.
- The script selects the active Xcode SDK, deployment target, and architecture;
  device arm64 and simulator arm64/x86_64 are explicit cases. It uses vendor
  mode and disables Go toolchain auto-download and surrounding Go workspaces.
- Go SDK lookup covers official installer/Homebrew paths and a build override.
- Derived output owns per-platform/per-architecture archives and Go caches;
  lipo merges current slices. CC includes all target arguments in its cache key.
- Debug/Release configs link the archive and retain the three ABI symbols;
  Profile uses Release. The new script has an LF checkout rule.

## Source basis

The installed official Go 1.27.1 SDK's `misc/ios/clangwrap.sh` specifies Xcode
clang, SDK sysroot, architecture and iOS/simulator minimum-version flags.
`go tool dist list` and the SDK's c-archive platform definitions include
ios/arm64 and ios/amd64. Existing bridge exports define the ABI.

## Verification limit

`bash -n tool/build_ios_go_runtime.sh` passes in WSL. No macOS host, Xcode,
iOS SDK, or Apple device is connected. Compilation, archive linking, signing,
and device/simulator FFI execution were explicitly skipped.
