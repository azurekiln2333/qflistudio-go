# Design: application package CI

## Boundary

New files:

- `.github/workflows/app-packages.yml` — workflow `App packages`.
- `tool/ci/app_build.py` — build, inspect and stage helper.
- `tool/ci/test_app_build.py` — unit tests for the helper.
- `docs/app-packages-ci.md` — Chinese user guide.

Changed files: `README.md`, `README.en.md`, `README.zh-TW.md` (section
"原生库与安装包" and its translations), `native/go_runtime/CI.md` (one pointer).

Untouched: `native-runtime.yml`, all application sources, tracked native
libraries, `ohos/build-profile.json5`.

The helper is adapted from the proven `qfli_lua/tools/ci_app_build.py`.

## Pinned inputs

| Input | Value |
| --- | --- |
| Shared core | `azurekiln2333/qflistudio-core@573d1b6eecf1c2b392ad753264a5a09f62f8335e`, checked out as sibling `qfli_studio_core/` |
| Flutter-OH | `https://gitcode.com/CPF-Flutter/flutter_flutter.git`, tag `3.41.9+ohos-1.0.2`, commit `62357a93d653bf844f730bb1f4b7cc9e2139d14e`, Dart 3.11.5 |
| Go | 1.27.1 (`actions/setup-go`) |
| OHOS SDK | API 26 command-line tools `26.0.0.821` from the `ErBWs/ohos-sdk` mirror, two parts with SHA-256 |
| Java | Temurin 17 (Android, OHOS) |
| Windows cgo compiler | MSYS2 UCRT64 `mingw-w64-ucrt-x86_64-gcc` |

## Job matrix

| Platform | Arch | Runner | Package |
| --- | --- | --- | --- |
| android | universal | ubuntu-24.04 | `qfligoshift-android-<abi>.apk` × 3 (debug key) |
| ios | arm64 | macos-15-intel | `qfligoshift-ios-arm64-unsigned.ipa` |
| ohos | arm64-v8a | ubuntu-24.04 | `qfligoshift-ohos-arm64-v8a-unsigned.hap` |
| linux | x86_64 | ubuntu-24.04 | `qfligoshift-linux-x86_64.tar.gz` |
| windows | x86_64 | windows-2025 | `qfligoshift-windows-x86_64.zip` |
| macos | arm64 | macos-26 | `qfligoshift-macos-arm64.tar.gz` |
| macos | x86_64 | macos-15-intel | `qfligoshift-macos-x86_64.tar.gz` |

Artifact name: `app-<platform>-<arch>`, retention 14 days. Layout:

```
packages/        only after every inspection passed
reports/         command logs, package-inspection.json, failure traces
licenses/
manifest.json
SHA256SUMS
```

## Triggers

`workflow_dispatch`, and `push` with a path filter and no branch filter:
workflow file, `tool/ci/app_build.py`, `tool/ci/test_app_build.py`,
`tool/inspect_go_catalog_hap.py`, `tool/go_curriculum/audit_native.py`,
`tool/build_ios_go_runtime.sh`, `tool/build_macos_go_runtime.sh`, `lib/**`,
`assets/**`, `native/go_runtime/**`, platform directories, `pubspec.*`.

Side effect: `native-runtime.yml` already triggers on `tool/ci/**`. The first
push therefore also starts the native workflow. Its source-check job discovers
`tool/ci/test_*.py`, so the new tests must pass on Linux Python 3.12 without
`json5`.

## Helper commands

`python tool/ci/app_build.py <command>`; platform and arch come from
`QFLI_PLATFORM` / `QFLI_ARCH`.

1. `init` — create the output directory and a pending manifest. Refuse to
   reuse a directory that already holds packages.
2. `setup-native` (windows, linux, macos, ios) — require `go version` to report
   `go1.27.1`; publish `QFLI_GO_EXECUTABLE`. Windows: take gcc from
   `$MSYS2_LOCATION/ucrt64/bin`, publish `QFLI_GO_CC` and `CGO_LDFLAGS=-static`.
   `build` prepends the gcc directory to `PATH` for the Flutter command only.
   Linux: publish the system gcc.
3. `setup-ohos` (ohos) — download, verify and unpack the SDK; publish
   `HOS_SDK_HOME`, `DEVECO_SDK_HOME`, `DEVECO_NODE_HOME`.
4. `setup-flutter` — fetch the pinned tag, verify commit and engine identity,
   write the flutter_tools dependency overrides, enable only the job platform,
   precache. The tag fetch, the first Flutter command (it downloads the Dart
   SDK) and precache each run up to three times, one log per attempt.
5. `build` — verify core and Flutter commits, sanitize the OHOS profile (OHOS
   only), `flutter pub get`, verify the core path binding, run
   `flutter build`, inspect, then stage packages.
6. `finalize` (always) — on any failure remove `packages/` and mark the
   manifest failed; copy licenses; write the step summary and `SHA256SUMS`.

## Platform specifics

- Windows and Linux: `native/go_runtime/desktop.cmake` compiles the runtime
  during `flutter build`. It reads `QFLI_GO_EXECUTABLE` and `QFLI_GO_CC`.
- macOS and iOS: the Xcode build phases compile the runtime. The build passes
  `QFLI_GO_EXECUTABLE` both as an environment variable and as the build setting
  `FLUTTER_XCODE_QFLI_GO_EXECUTABLE`, because the scripts prepend Homebrew
  directories to `PATH`.
- macOS: `FLUTTER_XCODE_ARCHS=<arch>`, `ONLY_ACTIVE_ARCH=YES`, ad hoc signing
  (`CODE_SIGN_IDENTITY=-`, manual style), `MACOSX_DEPLOYMENT_TARGET=13.0`.
- iOS: `flutter build ios --release --no-codesign`; the helper zips
  `Payload/Runner.app` into an unsigned IPA with `zip -qry`.
- Android: `flutter build apk --release --split-per-abi`, without `--no-pub`.
  `flutter pub get` writes a plugin registrant that includes the dev-only
  `integration_test` plugin. Release Gradle omits dev-only plugins, so a
  `--no-pub` build fails in `javac`. Without `--no-pub` the build regenerates
  the registrant in release mode. Gradle signs release with the debug key
  (existing project setting). The job uses the tracked `jniLibs` runtime.
- OHOS: `flutter build hap --release --no-codesign --target-platform
  ohos-arm64`. The helper empties `signingConfigs` and removes `signingConfig`
  and `compileSdkVersion` in the disposable checkout only. It refuses to run
  outside GitHub Actions or on a modified profile.

## Inspection before staging

All checks run before any file enters `packages/`.

| Platform | Checks |
| --- | --- |
| android | ABI set equals the requested ABI; `libflutter.so`, `libapp.so`, `libqfli_go_runtime.so` present; ELF class and machine; LOAD alignment ≥ 16 KiB on 64-bit ABIs; nine C ABI exports; `AndroidManifest.xml`; `zipalign -c -P 16`; `apksigner verify` |
| ohos | same library set under `libs/arm64-v8a/`; ELF checks; exports; `module.json` |
| linux | `qfli_go`, `lib/libflutter_linux_gtk.so`, `lib/libapp.so`, `lib/libqfli_go_runtime.so`, `data/icudtl.dat`; ELF checks; exports |
| windows | `qfli_go.exe`, `flutter_windows.dll`, `qfli_go_runtime.dll`, `data/app.so`, `data/icudtl.dat`; x64 PE; export table has the nine symbols; every imported `lib*.dll` ships in the bundle |
| macos | `QFLIGoShift.app`; executable arch equals the job arch; frameworks and `Contents/Frameworks/libqfli_go_runtime.dylib` contain the arch; `nm -gU` exports on the dylib; `codesign --verify --deep --strict` |
| ios | `Runner.app`; executable arch `arm64`; frameworks; `nm -gU` exports on the statically linked executable |

Every platform also compares the packaged Flutter assets declared in
`pubspec.yaml` with the source bytes.

The nine exports come from `tool/inspect_go_catalog_hap.py::SYMBOLS`. ELF and
PE parsing is pure Python so the same code runs on every runner.

## Manifest honesty

Keys use camelCase like `collect_native.py`. Fixed statements:

- `signing`: android `debug_key_for_testing_not_store_release`; ios and ohos
  `unsigned_requires_signing_before_device_installation`; macos
  `ad_hoc_not_notarized`; windows `unsigned_executable`; linux
  `not_applicable`.
- `goRuntime`: android and ohos `tracked_prebuilt_library_not_rebuilt_in_this_job`;
  others `compiled_from_source_in_this_job`.
- `deviceTests` and `runtimeTests`: `not_run`.
- Android and OHOS reports record the tracked and packaged runtime digests and
  whether they are byte-identical (packaging tools may strip the library).

## Failure handling

`run()` keeps complete logs under `reports/` and emits one bounded, redacted
`::error::` annotation. Any exception invalidates `packages/` and
`SHA256SUMS`. Upload uses `if: always()` so reports survive.

## Rollback

Delete the four new files and revert the documentation edits. No application
or build file changes exist to revert.
