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

Counts above overlap and are not summed into an invented total. Full 120-topic
race/fuzz/Apple/Windows-native-UI device coverage is not claimed. The Windows host
ran actual official Go SDK compiler/process tests; iOS/Xcode was not available.

The integration-test harness also now installs/restores the real Go profile and
uses a marker file rather than buffered stdout to synchronize interruption.
Targeted analysis passed after those corrections. Device execution remains a
separate gate below.

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

- Android OPD2413, Android 16/API36/arm64, direct endpoint
  `192.168.68.236:35991`: five-case integration APK prebuilt. Queued behind the
  existing Web/Python/SQL/Rust exclusive device windows; no Go installation or
  UI action is performed before handoff. This entry will be updated with the
  actual device outcome and product restoration evidence.
- OHOS `192.168.68.207:46551`, OpenHarmony 7/API26/arm64: current signed Flutter
  install/test blocked by absent matching Go keystore/profile. Cross-compiled
  native test transfer succeeded but execution was denied (remote exit 126),
  then the exact remote temporary file was removed. No current OHOS device test
  success is claimed, and existing production data was left intact.

## Logs and preserved work

Raw current logs and retained packages: `.artifacts/release-integrity/` (ignored).
Durable focused reviews and executable contracts are committed in this research
directory. Original unrelated `.codex/`, desktop-generated plugin registrants
and workstation OHOS signing edits are preserved; they are not silently reset,
cleaned, committed as feature work or included as signing credentials.
