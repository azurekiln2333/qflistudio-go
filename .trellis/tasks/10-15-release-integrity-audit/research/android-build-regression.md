# Android release generated-plugin regression

Workspace verified: `D:\MyNewProjects\qfli_go`. This follow-up inspected the
failed log, local generated metadata, project Gradle configuration and the
installed Flutter OHOS SDK sources. It did not run Flutter pub/build/test/clean,
modify generated metadata, edit frozen Dart/native sources or perform Git
operations. The only follow-up write is this report.

## Failure and cause

The logged `assembleRelease` failure is at `:app:compileReleaseJavaWithJavac`:

```text
GeneratedPluginRegistrant.java:24:
package dev.flutter.plugins.integration_test does not exist
```

`integration_test` is correctly declared under `dev_dependencies` in the product
pubspec. `.flutter-plugins-dependencies` correctly labels its Android plugin
`"dev_dependency": true`. The generated Java registrant nevertheless registers
`IntegrationTestPlugin`. Both metadata and Java file timestamps are from
2026-09-30, so the failing build reused previously generated tooling.

The installed SDK is `D:\ProgramFiles\flutter_ohos`, reported in
`android/local.properties`; its cached version is `3.27.5-ohos-1.0.1` with Dart
3.11.5. Inspection of its current sources proves the mismatch:

- `packages/flutter_tools/lib/src/runner/flutter_command.dart:1925` invokes
  `regeneratePlatformSpecificToolingIfApplicable` with the requested release
  mode. That helper at `:1962` returns early when `shouldRunPub` is false
  (`:1967`), as happens with `--no-pub`. Therefore this option also suppresses
  the mode-specific plugin regeneration.
- `packages/flutter_tools/lib/src/project.dart:383` passes that release flag
  into `ensureReadyForPlatformSpecificTooling`, which refreshes metadata and
  calls `injectPlugins` (`:443`).
- `packages/flutter_tools/lib/src/flutter_plugins.dart:1302` implements
  `injectPlugins`; at `:1321` release mode filters out `Plugin.isDevDependency`
  before writing the Android Java registrant (`:1333`).
- `packages/flutter_tools/gradle/src/main/kotlin/plugins/PluginHandler.kt:131`
  intentionally adds dev plugin dependencies only to nonrelease build types.
  The release classpath therefore correctly lacks `integration_test`, exposing
  the stale Java source instead of masking it.

## Coordinator repair command

Run from the Go root, preserving any intentional build flags and using the
normal product target:

```powershell
& 'D:/ProgramFiles/flutter_ohos/bin/flutter.bat' build apk --release --pub --target=lib/main.dart
```

The essential correction is to remove `--no-pub` (or explicitly use `--pub`) on
the release build. This allows Flutter to regenerate the registrant for release
mode before Gradle compiles it. It is not necessary to clean all outputs or
modify Android build configuration.

If a separate preparation step is preferred, the same SDK exposes
`build apk --release --pub --config-only --target=lib/main.dart`; a subsequent
matching release build may use `--no-pub` provided no intervening command
regenerates tooling in another mode. A direct build with `--pub` is simpler.

`flutter pub get` followed by `flutter build apk --release --no-pub` does not
establish this mode transition: pub-get tooling generation is explicitly
nonrelease in `commands/packages.dart:396`. Use the release build's own
regeneration path.

After regeneration, verify that the generated Android Java registrant no longer
references `integration_test`, then record the actual build exit status and APK
artifact. The plugin may remain in `.flutter-plugins-dependencies` with
`dev_dependency=true`; that metadata is shared by debug and release modes and
does not mean the plugin is packaged in the release app.

## Scope and status

No durable product/Gradle/script change is required for this failure. Keep the
test dependency as a dev dependency; keep the generated registrant ignored and
uncommitted. Main owns the serialized metadata regeneration and actual build.
Coordinator validation: `flutter build apk --release --pub` subsequently exited
0 and produced the current release APK. Package inspection verified all three
runtime ABIs byte-for-byte against the rebuilt libraries, including 16 KB ELF
LOAD alignment; `zipalign -c -P 16 4` also exited 0. A final product-entry rebuild
is recorded separately in the release validation report so integration-test
artifacts cannot be confused with the product APK.
