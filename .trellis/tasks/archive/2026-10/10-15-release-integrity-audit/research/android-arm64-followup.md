# Android ARM64 follow-up — 2026-10-15

## Coordination and safe installation result

Rust coordinator's authoritative global `qfli-core-release-sync` seq58 released
OPD2413 (`192.168.68.236:35991`) to Go. Go accepted in seq60. Read-only checks
confirmed `device`, `arm64-v8a`, Android API36 and 4096-byte pages. Existing Go
production package `com.azurekiln.qfli.goshift` has firstInstallTime
`2026-10-09 13:26:27` and version1.0.0.

The explicit safe `adb install -r` of the retained production-ID integration
APK **failed** with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`: the installed Go
package has a different signing identity. No uninstall, data clear, fallback
installation or shared ADB restart was performed. Production app/data were not
replaced. This attempt is not a passing ARM64 integration run or current normal
release installation.

Go immediately explicitly released the device to Dart coordinator w7:p1 in
seq61, clarified that release in seq63, and queued after Dart. Python's
coordinator confirmed no earlier reservation (relayed by Dart seq62). Dart
coordinator accepted exclusive ownership in seq64. No later Go device commands
are permitted until Dart's explicit coordinator release.

## Isolated host build prepared

To test current native code without replacing the installed production package,
Go built an isolated integration APK on the host only:

- Package: `com.azurekiln.qfli.goshift.integrationtest`.
- Activity: `com.azurekiln.qfli.goshift.MainActivity` (original namespace).
- Command: `flutter build apk --debug --pub --target
  integration_test/go_native_test.dart --target-platform android-arm64`.
- Result: exit0; Gradle assembleDebug24.1s.
- Artifact: `.artifacts/release-integrity/packages/qfli-go-arm64-isolated-integration.apk`.
- SHA256: `d39c8ff9ace5679ec967e43a8fce0698cce8a0154f19a7f7ca2a8a0f9d661887`.

The applicationId override was a temporary build operation. The original
`android/app/build.gradle.kts` was backed up and restored byte-for-byte in a
finally block; `git diff --exit-code` confirms restoration. No product source
change or new signing identity was committed. APK badging confirms the isolated
package and correct launch Activity. The ARM64 runtime hash exactly matches
the already verified original integration runtime:
`fe8c2ea519e18d7480f368087f8345708c0dcf31adb633acbfed071db0241148`.

## Next device gate

ARM64 integration execution is **pending Dart coordinator handoff**, not passed.
The prepared runner manually installs only the isolated package with
`adb install -r`; it then starts that package paused, forwards a dynamically
allocated VM Service port and connects `flutter drive --use-existing-app
--keep-app-running`. This path was reviewed in the local Flutter SDK and avoids
automatic install/uninstall fallback. It stops only the isolated app and removes
only its own forward afterwards.

Raw host scripts and logs are under `.artifacts/release-integrity/`:
`android-arm64-before.txt`, `android-arm64-install.log`,
`android-arm64-isolated-build.log`, `build-arm64-isolated.ps1`, and
`run-arm64-isolated.ps1`. Future results must be recorded as actual outcomes,
without overwriting the separate passing x86_64/16KB evidence.
