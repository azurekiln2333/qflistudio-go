# Design: cross-platform native runtime workflow

## Scope boundary

The workflow builds only bundled native runtime libraries. It does not package or sign the Flutter applications.

- `windows-2022`: Android ABIs and OpenHarmony ABIs. The existing PowerShell scripts require Windows NDK/SDK paths.
- `macos-15`: macOS universal dylib, iOS device archive, and iOS simulator archive. The existing shell scripts use the installed Xcode SDK and Go SDK.
- Linux and Windows desktop application execution continue to use the official Go SDK already expected by the app. They do not receive a new GitHub native artifact job.

## Jobs and contracts

### Independent Android and OpenHarmony jobs

1. Checkout the repository.
2. Install official Go 1.27.1.
3. Install Android NDK with the runner's Android SDK tools.
4. Download the default official OpenHarmony SDK archive and verify its published SHA-256. Permit a URL/digest override pair. Reject incomplete overrides.
5. Run `tool/build_ohos_go_toolchain.ps1` to build the pinned OHOS Go host toolchain.
6. Run `tool/build_go_runtime.ps1` with official Go, OHOS Go, Android NDK and OHOS SDK paths.
7. Collect Android libraries, OpenHarmony libraries and `native/build/bundled-go-runtime-build.json`.
8. Generate a file list with byte sizes and SHA-256 digests.
9. Upload platform-specific artifacts with immutable unique names.

### macOS job

1. Checkout and install Go 1.27.1.
2. Invoke `tool/build_macos_go_runtime.sh` with Xcode environment variables for arm64 and x86_64.
3. Upload the universal dylib and a checksum manifest.

### iOS job

1. Checkout and install Go 1.27.1.
2. Invoke `tool/build_ios_go_runtime.sh` once for `iphoneos/arm64`.
3. Invoke it again for `iphonesimulator/arm64 x86_64`.
4. Upload separate device and simulator archives, each with the generated header and checksum manifest.

## OHOS SDK input

The workflow defaults to the official 5.0.0 release SDK and published digest. Repository variables `OHOS_SDK_URL` and `OHOS_SDK_SHA256`, or a complete manual dispatch input pair, override the default. The archive is extracted to a temporary runner directory. The workflow never commits or caches the SDK.

## Artifact naming

Use names containing the platform, ABI or slice, and commit SHA. Examples:

- `native-android-<sha>`
- `native-ohos-<sha>`
- `native-macos-universal-<sha>`
- `native-ios-device-<sha>`
- `native-ios-simulator-<sha>`
Each artifact contains its manifest and SHA256SUMS.

Binary artifacts use zero compression where practical. Missing files fail the upload step.

## Verification and limits

- Validate shell scripts with `bash -n` on the macOS job.
- Run `go test -mod=vendor ./...` and `go vet -mod=vendor ./...` in a native source job before platform builds, or record an environment limitation if the full matrix cannot run.
- Use `file`, `lipo -info`, and SHA-256 checks on Apple outputs.
- Use existing provenance JSON for Android/OHOS. Apple outputs get a separate manifest because the PowerShell provenance script does not cover them.
- No Apple signing identity, provisioning profile, device install, or Flutter packaging is required.
