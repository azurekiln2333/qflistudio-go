# qfli_go

This Flutter app is an independent Git repository. Check out `qfli_studio_core` next to it before resolving dependencies.

```text
checkout-parent/
  qfli_studio_core/
  qfli_go/
```

Run `flutter pub get` here, then `flutter run` for the target device. The shared editor patch is provided by `../qfli_studio_core/vendor/re_editor`.

## Go Runtime

| Platform | Execution backend | Prerequisite |
| --- | --- | --- |
| Android / OpenHarmony | Bundled Yaegi interpreter through C ABI and Flutter FFI | Native libraries are included |
| iOS | The same interpreter, built as a static archive and loaded from the app process | Xcode and a Go SDK on the build Mac |
| Windows / Linux / macOS | Official Go SDK | `go` available on the application's `PATH` |
| Web / other targets | Unavailable | Native execution is not supplied |

The interpreter is implemented in Go and exposed through C ABI. Mobile execution
supports interpreted Go programs; desktop execution provides the official SDK's
run, build, test, fmt, vet, and module-management commands.

Windows SDK execution and cancellation, Android x86_64 FFI execution, and Linux
SDK/native-source behavior have been verified. Linux Flutter GUI and Apple
build/device execution have not been tested on this Windows host.

See [the native runtime notes](native/go_runtime/README.md) for dependency
patches, library builds, platform evidence, and device integration tests.
