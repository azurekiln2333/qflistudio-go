# QFLIGoShift

[简体中文](README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md)

QFLIGoShift is a Flutter app for learning and editing Go.
This independent repository uses the sibling `qfli_studio_core` package through a local path dependency.

## Core features

- An editor with syntax highlighting and file navigation.
- Tutorials and examples with code copying and project import.
- Desktop program execution through the official Go SDK.
- Desktop build, test, formatting, and module commands.
- Mobile program execution through the bundled Yaegi interpreter.
- An in-app terminal that selects the backend for the platform.
- Mobile terminal support limited to program execution in the form `go run`.

## Features in development

The development worktree contains the following unpublished changes.
These changes may be incorrect.

- Syntax diagnostics and editor squiggles.
- Formatting, imports, symbols, and local module tools.
- JSON-to-Go-struct conversion.
- Breakpoints, stepping, call stacks, and variable inspection.
- Named workspaces and restoration of multiple project roots.

These features have not passed complete validation of the current version.
Their presence in source does not prove that a packaged app contains them.

## Platforms and execution backends

This table separates the backend design from historical checks.
Historical results apply only to the sources and packages checked at that time.

| Platform | Execution backend | Prerequisite | Historical checks and limits |
| --- | --- | --- | --- |
| Android | Yaegi through C ABI and Flutter FFI | Native library for the selected ABI | Earlier x86_64 pass; ARM devices unverified |
| OpenHarmony | Yaegi through C ABI and Flutter FFI | Native library built with the OHOS Go port | Earlier x86_64 evidence; arm64 unverified |
| iOS | Yaegi through a static archive and process symbols | Mac, Xcode, and Go SDK | Apple builds and device execution unverified |
| Windows | Official Go SDK | `go` available on the application's `PATH` | Earlier toolchain evidence; GUI packaging unverified |
| Linux | Official Go SDK | `go` available on the application's `PATH` | Earlier backend evidence; Flutter GUI unverified |
| macOS | Official Go SDK | `go` available on the application's `PATH` | Unverified on a macOS host |
| Web / other | Unavailable | None | No native Go execution |

`lib/go_platform.dart` defines the mapping.
Mobile targets report `embedded-go-runtime`.
Desktop targets report `official-go-sdk`.

## Offline boundary

The standalone app's features target offline use.
The built-in curriculum does not require Go package downloads.
The mobile interpreter is not a complete Go SDK.
It does not provide the official SDK's build or module-download commands.
The app does not provide a general network sandbox.
User-written Go programs may access the network or host files.
Fetching Flutter dependencies during development may require a connection.
Prepare all dependencies and toolchains before working offline.

## Development prerequisites

- A Flutter SDK satisfying the Dart constraint `>=3.11.5 <4.0.0`.
- An installed Go SDK for desktop execution.
- A sibling checkout of the shared core repository.
- An OHOS-enabled Flutter SDK for OpenHarmony builds.

The shared editor comes from `../qfli_studio_core/vendor/re_editor`.
Use this directory layout:

```text
checkout-parent/
  qfli_studio_core/
  qfli_go/
```

## Development commands

Run these commands from `qfli_go`.
They are development instructions, not checks performed for this documentation change.

Resolve dependencies:

```powershell
flutter pub get
```

Run the app:

```powershell
flutter run
```

Analyze Dart source:

```powershell
flutter analyze --no-pub
```

Replace the SDK path with your installed executable.
Run the tests:

```powershell
$env:QFLI_GO_TEST_EXECUTABLE = "C:\path\to\go.exe"
flutter test --no-pub --concurrency 1
```

The curriculum tools use sources under `tool/go_curriculum/`.
Host checks do not replace device checks.

```powershell
python tool/go_curriculum/assemble.py
python tool/go_curriculum/verify.py --go "C:\path\to\go.exe"
python tool/go_curriculum/dedup.py
```

## Native libraries and packages

Android builds require the Android NDK.
OpenHarmony builds require the OHOS SDK and the pinned OHOS Go port.
See the [native runtime notes](native/go_runtime/README.md) for the port version and source details.

First build the OHOS Go host toolchain:

```powershell
./tool/build_ohos_go_toolchain.ps1 -BootstrapGoExecutable "C:\path\to\go.exe"
```

Use the OHOS Go executable path printed by that script.
Build the five Android / OpenHarmony native libraries:

```powershell
./tool/build_go_runtime.ps1 `
  -GoExecutable "C:\path\to\go.exe" `
  -OhosGoExecutable "C:\path\to\ohos-go.exe" `
  -AndroidNdk "C:\path\to\ndk" `
  -OhosSdk "C:\path\to\ohos-sdk"
```

The script covers three Android ABIs and two OpenHarmony ABIs.
The iOS Xcode build phase invokes `tool/build_ios_go_runtime.sh`.
After native source changes, rebuild the libraries used by the corresponding app package.
An old library does not acquire source fixes automatically.

Use an OHOS-enabled Flutter SDK to build a debug HAP:

```powershell
flutter build hap --debug --no-pub
```

Building a package does not prove execution on a device.

## Curriculum and verification status

- The existing curriculum has 120 Go topics.
- Each topic has one tutorial and one example.
- The shared core supplies the current curriculum UI.
- The development worktree has another 160 draft topics.
- Those drafts are not in the production curriculum.
- Historical host check results exist.
- Exhaustive OHOS execution of the original examples is incomplete.
- The current native changes have not passed complete validation.
- The current UI changes remain unverified.

This repository does not claim that the current version has passed exhaustive OHOS checks.
Device evidence must match the actual source and app package.

## Further documentation

- [Native runtime, builds, and platform evidence](native/go_runtime/README.md)
- [Curriculum tooling](tool/go_curriculum/README.md)
- [Learner guide](tool/go_curriculum/GUIDE.md)
- [Curriculum schema](tool/go_curriculum/schema.md)
- [Host probe notes](tool/go_curriculum/mobile_check/README.md)

## Third-party notices

- [Go standard library notice](assets/licenses/go.txt)
- [Yaegi notice](assets/licenses/yaegi.txt)
