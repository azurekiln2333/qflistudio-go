# Go release validation — 2026-10-15

## Workspace and ownership

Application repository: `D:/MyNewProjects/qfli_go`, branch
`fix/go-release-integrity`. Shared dependency: the separate
`D:/MyNewProjects/qfli_studio_core` repository. Existing restarted Pi panes
`w8:p5`, `w8:p6`, `w8:p7` were verified in the Go repository before assignment;
all three completed their disjoint terminal/runtime, curriculum, and offline
scopes. Main owns staging, commits, builds, device coordination and integration.
No sibling language project was modified by this Go team.

Shared core commits integrated by Go:

- `8731df8`: only the Go content slices, preserving every non-Go byte.
- `b7b2d2e`: Home/Profile background refresh, remote activity and Git/network
  shortcut guards, with online behavior preserved.
- `a838c25`: validate exact non-Java import filenames, Java behavior preserved.

Core editor gates `54a58ca`, retained-editor transitions `665febb`, generic
ToolsGrid scaling `7b8b7f2`, and About identity `8b33443` belong to their existing
owners. Go coordinated their use and did not overwrite those sources. Final
package builds use core `8b33443481036d9d17d31940d851fde0aab9e5df`.

## Product and content findings resolved

- Both terminal surfaces now use the Go profile delegate. Desktop commands use
  the real SDK and cwd, output/status and cancellation. Mobile supports the real
  embedded interpreter's `go run <file|directory>` and explicitly refuses SDK
  commands it does not provide. The two terminal surfaces have real-widget tests.
- Selected-entry runs preserve helpers/module context and source bytes; competing
  mains are filtered only in the selected directory. Modern native build tags,
  invalid/duplicate constraints and block-comment pseudo-directives are covered.
- Offline product account/Git/cloud/AI and network-tool entries are hidden.
  Restored-token Home/Profile/task refresh performs no background HTTP; local
  statistics and queued data remain available. This does not prohibit networking
  inside learner programs or manual desktop-shell commands.
- Native OHOS AccountKit bridge and placeholder client metadata were removed;
  native startup waits for initialization/layout and has tested failure handling.
  The agreement reader remains an HTTPS web reader, not an offline local page.
- The actual shared assets now contain 120 substantive Go tutorials and 120 Go
  examples, replacing the former 100 placeholder entries in each aggregate.
  All 120 sample compile/run assertions, dedup and chapter reviews passed.
  All entries are honestly desktop-labelled; 33 multi-file/test topics explain
  their import limitations. No unverified mobile claim was added.
- Curriculum verification resolves relative SDK paths before changing cwd and
  fails an absent explicit SDK. Explicit race verification now fails closed.
  Obsolete untracked root-level placeholder snapshots were precisely removed.

## Current validation commands and outcomes

Pinned SDK: `native/build/go-sdk-1.27.1/go/bin/go.exe`. Flutter:
`D:/ProgramFiles/flutter_ohos/bin/flutter.bat`, Dart 3.11.5.
Verification environment: `GOMAXPROCS=2`, `GOFLAGS=-p=1`, `GOTOOLCHAIN=local`;
Flutter tests use `--no-pub --concurrency 1`. Release builds use `--pub` so this
Flutter fork regenerates platform plugin registrations for the correct mode.

| Check | Result |
| --- | --- |
| `flutter analyze --no-pub` | Exit 0, no issues |
| Full `flutter test --no-pub --concurrency 1 --reporter expanded`, real SDK enabled | **111 passed**, 0 failed/0 skipped |
| Shared terminal_pane/editor_run/terminal_manager_delegate/sandbox/offline_background/task_activity/tools_grid | **99 passed**, exit 0 |
| Shared import/Java rename/Java overwrite + Go import regressions | **75 passed**, exit 0 |
| Newly committed shared About identity regressions | **4 passed**, exit 0 |
| Actual asset-load + shared parser validation | **13 passed**, exit 0 |
| Ordinary curriculum compiler/run assertions | **120 passed**, 0 failed |
| Real selected race gates T077/T078/T081/T119 | **4 RACE-OK**, exit 0 |
| Curriculum race failure regression unittest | **5 passed**, exit 0 |
| Native `go test -mod=vendor -count=1 ./...`, `go vet -mod=vendor ./...` | Exit 0 after final vendor fixes |
| Five bundled native runtime rebuilds | Android 3 ABIs + OHOS 2 ABIs, exit 0 |
| Final APK/HAP ELF packaging verifier | PASS, exit 0 |
| Android `zipalign -c -P 16 4` | Exit 0 |
| Android API37/x86_64/16 KB emulator, real bundled FFI + sandbox delegate integration | **5 cases passed**, driver exit 0 |
| Normal release APK install/cold launch + five product pages + standalone terminal | PASS; product restored after integration target |

Counts above overlap and are not summed into an invented total. Full 120-topic
race/fuzz/Apple/Windows-native-UI device coverage is not claimed. The Windows host
ran actual official Go SDK compiler/process tests; iOS/Xcode was not available.

The integration-test harness also now installs/restores the real Go profile and
uses a marker file rather than buffered stdout to synchronize interruption.
Targeted analysis passed after those corrections. The five Android emulator
cases below executed that corrected harness; the extra reported teardown count
is not counted as a sixth product test.

## Fresh final packages

Final Android command:
`flutter build apk --release --pub --target lib/main.dart` — exit 0.
All three runtime members are byte-identical to the rebuilt source libraries;
ELF LOAD alignment is 0x4000 and archive 16 KB alignment passes.

- `build/app/outputs/flutter-apk/app-release.apk`
- Retained copy: `.artifacts/release-integrity/packages/qfli-go-1.0.0-android-release.apk`
- SHA256: `849f20bd06258be5edcf69c016fdd6ca78348cca97f4101581db425b67aa543b`

Final OHOS command:
`flutter build hap --release --pub --no-codesign`, with temporary typed
Hvigor signing disable and exact-byte restoration — exit 0. Both arm64 and
x86_64 runtime libraries are included; all 31 allocated ELF sections per ABI
match the rebuilt libraries after stripping.

- `build/ohos/hap/entry-default-unsigned.hap`
- Retained copy: `.artifacts/release-integrity/packages/qfli-go-1.0.0-ohos-unsigned.hap`
- SHA256: `175adfe2fe9507735ca74caac1ed63e1c7ec736dde5ea07d92bebe88a0d19dad0c`

Android release currently uses the existing debug signing configuration. A
production store signature is not supplied/generated by this audit. OHOS signed
build failed on missing matching Go signing material; the fresh successful
artifact is **unsigned**. See `ohos-signing.md`. The old signed 10-09 artifact is
not a result of this round.

## Device status

- Android temporary read-only Pixel_10, `emulator-5580`, API37/x86_64,
  `getconf PAGE_SIZE=16384`, `sys.boot_completed=1`: **five actual integration
  cases passed**, `flutter drive` exit 0. The real bundled interpreter exercised
  selected multi-file programs, main/worker panics and os.Exit, cancellation,
  sandbox-delegate file/directory runs, helper diagnostics, unsupported-command
  refusal and marker-synchronized terminal interruption. Command:

  ```powershell
  $env:ADB_SERVER_SOCKET='tcp:localhost:5039'
  $env:ANDROID_ADB_SERVER_PORT='5039'
  $env:ADB_MDNS_AUTO_CONNECT='0'
  flutter drive --no-pub --use-application-binary .artifacts/release-integrity/packages/qfli-go-integration-debug.apk --target integration_test/go_native_test.dart --driver .artifacts/release-integrity/integration_driver.dart --no-keep-app-running -d emulator-5580
  ```

  Afterwards the retained normal release APK was installed with `adb -P 5039
  -s emulator-5580 install -r`, and `am start -W -n
  com.azurekiln.qfli.goshift/.MainActivity` returned `Status: ok`, `COLD`.
  Package inspection confirmed version 1.0.0 and x86_64. Home, Tools, Tutorials,
  Examples and Profile were captured and visually inspected; loaded examples
  display 120, Tools/Profile expose local functions without account/Git/cloud
  entry points. The standalone terminal opened and actual `go version` produced
  the honest mobile `go run`-only explanation and **exit code 127**. The normal
  product was returned to Home and force-stopped before handing over the
  emulator. No Go crash appears in the retained crash buffer; its only process
  is the image's repeatedly failing UWB system service.

  Raw evidence: `android-device-tests.log`, `android-release-smoke.log`,
  `android-release-{home,tools,tutorials,examples,profile}.png/.xml`,
  `android-release-pages.png`, `android-release-terminal-command.png/.xml` and
  `android-release-crash.log` under `.artifacts/release-integrity/`.
  The original Home XML is named `android-release-ui.xml`.
  The instance uses a separate private ADB server on 5039; the shared server
  on 5037 and original AVD data were not reset. Global coordination seq48
  explicitly hands emulator 5580 and its eventual cleanup to Rust after Go's
  checks; Rust explicitly accepted that ownership/cleanup in seq49. No later
  Go device operations are performed after that handoff.
- Android OPD2413, Android 16/API36/arm64, direct endpoint
  `192.168.68.236:35991`: **not executed this round**. Shared physical-device
  ownership was respected; the emulator evidence above does not establish
  arm64 real-device success. The packaged arm64 library passed build/ELF checks.
- OHOS `192.168.68.207:46551`, OpenHarmony 7/API26/arm64: current signed Flutter
  install/test blocked by absent matching Go keystore/profile. Cross-compiled
  native test transfer succeeded but execution was denied (remote exit 126),
  then the exact remote temporary file was removed. No current OHOS device test
  success is claimed, and existing production data was left intact.

## Closure and external release gates

The integrity audit and its code/content deliveries are complete against
AC1-AC6, including AC5's requirement to fix or record every discovered blocker.
This is not a store-ready declaration. Remaining external release gates are:

- Android production signing: the existing release configuration uses a debug
  key. No replacement store key was generated or substituted.
- Go-specific OHOS private key/certificate/profile: currently configured files
  are absent and other products' available credentials do not match. Fresh
  signed HAP/install/Flutter-FFI device execution remain blocked.
- This round's Android arm64 real-device coverage remains unverified. Apple
  builds/runs, all-topic race/fuzz and native desktop Flutter GUI coverage are
  also not claimed.

Source commits: `775c207` (OHOS startup), `96df3ad` (curriculum), `4ace2f4`
(native/entry/build constraints), `df2f46d` (both terminals), `2b2fef6` (offline
and import regressions), and `7502c08` (canonical formatting). Shared-core
commits are listed above. Final review found no unresolved in-scope source
defect; remaining conditions are recorded rather than converted into passes.

## Logs and preserved work

Raw current logs and retained packages: `.artifacts/release-integrity/` (ignored).
Durable focused reviews and executable contracts are committed in this research
directory. Original unrelated `.codex/`, desktop-generated plugin registrants
and workstation OHOS signing edits are preserved; they are not silently reset,
cleaned, committed as feature work or included as signing credentials.
