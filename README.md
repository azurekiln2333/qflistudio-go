# qfli_go

This Flutter app is an independent Git repository. Check out `qfli_studio_core` next to it before resolving dependencies.

```text
checkout-parent/
  qfli_studio_core/
  qfli_go/
```

Run `flutter pub get` here, then `flutter run` for the target device. The shared editor patch is provided by `../qfli_studio_core/vendor/re_editor`.

## Go Runtime

Desktop execution uses the official Go SDK from `PATH`. Android and OpenHarmony
use a bundled Yaegi interpreter through Flutter FFI. Mobile execution does not
provide the official SDK's build, test, vet, or module-management commands.

See [the native runtime notes](native/go_runtime/README.md) for dependency
patches, library builds, and device integration tests.
