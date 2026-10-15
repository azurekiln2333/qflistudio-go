# Pi 3 — Go offline entry & platform integrity audit (w8:p7)

Owner: pi-go-offline (Herdr w8 right pane 3/7), directed by main coordinator
`w8:p1` (Codex). Parent task: `.trellis/tasks/10-15-release-integrity-audit`.

Boundary: this is the **Go workspace only** (`D:\MyNewProjects\qfli_go`).
The shared core (`../qfli_studio_core`) is **read-only** here; precise paths and
line numbers are recorded for the coordinator to integrate any shared fix.

Verified identity: `Get-Location` = `D:\MyNewProjects\qfli_go`;
`git rev-parse --show-toplevel` = `D:/MyNewProjects/qfli_go`. No sibling project
or shared-core file was edited.

## 1. How offline is actually enforced

`StudioProfile.offlineOnly` defaults to `isOffline`
(`lib/services/studio_profile.dart:111`). The Go product sets `isOffline: true`
in `lib/main.dart` and therefore inherits `offlineOnly == true`
(`lib/main.dart:26-44`). `main.dart` and the terminal/runtime are owned by Pi 1
and were only read.

`offlineOnly` is the shared policy switch. `isOffline` additionally swaps the
tutorial/example tabs to their local variants. The audit below asked which
product entry points are reachable for the Go profile, i.e. whether every
network surface actually consults this switch.

### Surfaces correctly gated (verified)

| Surface | Gate | Location |
| --- | --- | --- |
| Cloud project scope tab + cloud projects in every scope | `offlineOnly == true` | `lib/pages/home_page.dart:102, 308, 550` |
| "New cloud project" menu item | `offlineOnly != true` | `lib/pages/home_page.dart:430` |
| Remote cloud refresh on pull-to-refresh / reload | early `return` | `lib/pages/home_page.dart:700` |
| Tutorials tab → community `PostListPage` | local tab chosen instead | `lib/pages/home_page.dart:162-168, 308` |
| Profile login header, stats, check-in/points, admin, sign-out, ICP footer, login route | `offlineOnly` | `lib/pages/profile_page.dart:81-99, 196, 217, 228` |
| Editor AI assistant menu item + panel | `offlineOnly != true` | `lib/editor/editor_page.dart:1625, 1646` |
| Editor online terminal (server execution) menu item | `offlineOnly != true` | `lib/editor/editor_page.dart:1646` |
| Online terminal internals (`showOnline`/`runOnlineProject`) | `onlineEnabled` | `lib/editor/terminal_pane.dart:561-580, 598, 1287` |
| Editor passes `onlineEnabled: offlineOnly != true` | `offlineOnly` | `lib/editor/editor_page.dart:1881` |
| Cloud project sync on editor open | `offlineOnly != true` | `lib/editor/editor_page.dart:203` |
| `.sql` → cloud MySQL run | `offlineOnly != true` | `lib/editor/editor_page.dart:1001` |
| Fallback to online runner on missing local runtime | `offlineOnly != true` | `lib/editor/editor_page.dart:1092, 1116` |
| Settings page "AI 助手" section | `showAi` = `offlineOnly != true` | `lib/editor/editor_page.dart:1415-1419`; section at `lib/pages/settings_page.dart:132` |
| Community feed reachable only via `TutorialsTab`/`DiscussionTab` | never rendered offline | `lib/pages/home_page.dart:1186-1204` |
| `FunctionsTab` common tools | offline-only by construction | `lib/pages/tools_grid.dart:31-84` (`commonTools` = Unicode/Base64/URL/Regex/JSON/Hash/Timestamp/UUID/Color, all local computation) |
| Standalone terminal (`TerminaxTerminalPage`) | sandbox backend only, no server session | `lib/pages/terminax_terminal_page.dart`; `lib/terminal/state/terminal_manager.dart:44-52` |

Startup: `AppBootstrap.run` (`lib/splash_screen.dart:46-72`) awaits only
`ProjectStore.load`, `AuthStore.load`, `SettingsStore.load`. `AuthStore.load`
(`lib/store/auth_store.dart:28-53`) is local file IO and only restores a token
whose `serviceOrigin` is owned by `ApiConfig`; it performs **no** network call.
`ProjectStore.load` (`lib/store/project_store.dart:77`) is local file IO.
So startup does **not** log in or sync to the cloud.

### Defects found (all in shared core, read-only for this Pi)

> Status: the coordinator `w8:p1` owns the shared-core fixes and applied them
> immediately after this audit was reported. This Pi did not edit the shared
> core; the line numbers below are the audit-time coordinates. The Go-side
> regression test `test/go_offline_profile_test.dart` pins the contract and is
> re-run after the shared fix lands.

1. **Editor "Git" menu item is not gated by `offlineOnly`** —
   `lib/editor/editor_page.dart:1584-1600` (menu item) and the handler at
   `lib/editor/editor_page.dart:1432-1433` → `_openGit()` at
   `lib/editor/editor_page.dart:589-595` pushes
   `GitPage(project:, auth:)`. On the Go offline profile the item is still
   shown and opens `GitPage`. Inside `GitPage`
   (`lib/pages/git_page.dart`):
   - cloud project branch is auth-gated (`:74 _runCloud` → `:73 '云端 git 需要先登录'`), but
   - a **local desktop** project exposes `git push` (`:267-271`),
     `git pull` (`:278-282`) and `git remote add origin` (`:154-192`) using
     `GitService` — real network operations, reachable from the Go product.
   For the acceptance criterion "the offline profile exposes no network-dependent
   account/Git/cloud routes", this is a genuine leak. Suggested minimal shared
   fix: wrap the `const PopupMenuItem(value: 'git', ...)` at
   `lib/editor/editor_page.dart:1584` in
   `if (StudioProfile.current?.offlineOnly != true)` (same guard already used for
   `ai`/`online_terminal` at `:1625` / `:1646`). The `git` case in the switch can
   stay (unreachable when the item is hidden) or be guarded the same way.
   **FIXED by the coordinator `w8:p1`** (shared core), then verified by
   `test/go_offline_profile_test.dart`.

2. **Profile pull-to-refresh can still issue a network request on an offline
   profile** — `lib/pages/profile_page.dart:44-50` `_refresh()` calls
   `widget.auth.refreshMe()` unconditionally, and the whole page is wrapped in a
   `RefreshIndicator` (`:89`). `AuthStore.refreshMe`
   (`lib/store/auth_store.dart:107-121`) calls `ApiClient.instance.me(token)`
   whenever a token is present. The account UI is hidden for offline, but if a
   trustworthy token survives in `auth.json` (e.g. a debug build that logged in,
   or a shared desktop app-support dir), the local stats refresh fires a network
   request. Low likelihood in a clean store install, but it is a residual
   "暗中" network path. Suggested shared fix: short-circuit `_refresh()` when
   `StudioProfile.current?.offlineOnly == true`, or skip `refreshMe` in
   `AuthStore` for offline profiles.
   **FIXED by the coordinator `w8:p1`** (shared core).

3. **HomeTab `TaskActivityService.refreshIfDue` fires on a stale token** —
   `lib/pages/home_page.dart:325, 344` call
   `TaskActivityService.instance.refreshIfDue(auth)`, which performs a server
   fetch (`lib/services/task_activity_service.dart:302-325`, `_refreshTasks`).
   It is reached from `HomeTab.initState` and `_onAuthChanged` guarded only by
   `_loggedIn`. For the Go offline profile this can issue a background network
   request whenever a token is present. Same trigger condition as (2).
   Suggested shared fix: guard both call sites with
   `StudioProfile.current?.offlineOnly != true`.
   **FIXED by the coordinator `w8:p1`** (shared core).

No other product entry point was found that reaches the network for the Go
profile. In particular: the Go runner (`lib/go_runner.dart`) is pure local
`Process.start` / FFI, the native bridge (`lib/native_go_bridge_ffi.dart`) only
loads `libqfli_go_runtime.so`, and the offline learning content is local assets.
Learner-authored `net/http` examples are just source text and are **not** a
product entry point — no library is globally disabled.

## 2. Platform configuration audit (Go project, owned files)

### Android — `android/app/src/main/AndroidManifest.xml`

- No `<uses-permission>` of any kind, in particular **no
  `android.permission.INTERNET`**. Correct for the offline product.
- Single launcher activity, no network/deep-link intent filters. Baseline
  `HEAD` was identical (no permission was ever present). No change needed.

### OHOS — `ohos/entry/src/main/ets/entryability/EntryAbility.ets`

- Pre-existing (not part of Pi 1's diff, present at baseline `58330ef`):
  the file imported `@kit.AccountKit` and **unconditionally** registered the
  `qflistudio/huawei_account` method channel that executes Huawei ID
  authorization (a `login` handler performing
  `AuthorizationWithHuaweiIDRequest -> executeRequest -> authorizationCode`).
  For the Go offline product no Dart code ever calls this channel: the only
  caller is `lib/pages/auth/login_page.dart:27, 260` via `HuaweiQuickLoginView`,
  which lives inside `LoginPage`, reachable only through the account/profile
  login entry that `offlineOnly` hides (`lib/pages/profile_page.dart:71-74`).
  The native login capability was dead code for this product and a store-review
  liability.
  **FIXED (this Pi owns `EntryAbility.ets`):** removed the `@kit.AccountKit`
  import, the `CHANNEL_HUAWEI` constant and the entire Huawei channel
  registration block. The `openAgreement`, `startupProgress`, `openUrl`,
  `shareText` and picker handlers are untouched, and `MethodChannel` /
  `MethodCall` / `MethodResult` / `BusinessError` imports are still exercised by
  those handlers. `entry/ohos` build caches retain stale `.ts` copies; they are
  generated output and are not tracked source.
- Pi 1's startup additions in this file (`openAgreement`, `startupProgress`) and
  in `pages/Index.ets` were reviewed and are intact: `startupProgress` validates
  a finite number, clamps to `[0, 1]` and emits `EVENT_STARTUP_PROGRESS`, which
  matches the documented contract in `.trellis/spec/frontend/native-startup.md`.
  The protocol page (`pages/AgreementReader`) and its route remain in place.

### OHOS — `ohos/entry/src/main/module.json5`

- `metadata` declared `client_id = REPLACE_WITH_AGC_CLIENT_ID` (baseline,
  present since `58330ef`, never filled). It is the AGC/Huawei account-login
  binding and is meaningless for the offline product. **FIXED (this Pi):** the
  `metadata` entry was removed; the rest of the ability definition (skills,
  start-window icon/background, `exported: true`) is unchanged.
- `ohos.permission.INTERNET` is **kept**. Per the coordinator's direction, the
  shared HTML preview's loopback socket bind and the debug `integration_test`
  plugin require it, and "hide the network product entries" does not mean
  "disable local sockets". No permission was added or removed.

### Platform release-signing limitations (recorded, NOT changed)

- **Android release uses the debug signing config.**
  `android/app/build.gradle.kts:34-38` (`release { signingConfig =
  signingConfigs.getByName("debug") }`) with the stock `// TODO: Add your own
  signing config for the release build.` comment. A store submission needs a
  real release keystore. No keystore was generated or replaced here; the user's
  signing material is untouched. This must be resolved before publishing.
- **OHOS HAP is signed with an auto-generated DevEco "debug" material.**
  `ohos/build-profile.json5:31-33` (`keyAlias: debugKey`, material under
  `C:\Users\lichengyu\.ohos\config\default_ohos_*.{cer,p7b,p12}`), bound to
  `bundleName com.azurekiln.qfli.goshift` in `ohos/AppScope/app.json5`. Reusable
  for local device runs, but an AGC release profile is required for store
  submission. Recorded only; no signing material was created or replaced.


### OHOS — `ohos/entry/src/main/resources/base/profile/main_pages.json`

- Routes are `pages/Index` and `pages/AgreementReader`. `AgreementReader` is the
  local compliance/agreement reader (native), not a network entry. Consistent
  with the contract in `.trellis/spec/frontend/native-startup.md`.

## 3. Regression test added

`test/go_offline_profile_test.dart` (new, owned by this Pi) mounts the **real**
shared components under the **real** Go profile and asserts:

- `goProfile.offlineOnly == true` and `goProfile.isOffline == true`.
- The home page exposes only the offline project scopes (no `云端项目`).
- `FunctionsTab` under the Go profile renders the shared offline tools and no
  network tool card (no "HTTP 请求" / "本地服务").
- `ProfileTab` under the Go profile renders no login entry, no sign-out and no
  ICP footer, while local sections (设置 / 本机记录) remain.
- The settings page under the Go profile does not expose the AI assistant
  section (`showAi: offlineOnly != true`).
- The editor's Git entry point is **not** reachable for the Go profile. This
  test is the regression for shared defect #1; it now **passes** after the
  coordinator's shared-core fix.
- **No offline background refresh fires for a trustworthy residual token.**
  - `ProfileTab` pull-to-refresh must not call `AuthStore.refreshMe` when
    `offlineOnly`. A `_CountingAuthStore` subclass counts the call; the offline
    case asserts `0`.
  - `HomeTab` init and auth-change must not reach the server task/activity
    endpoint when `offlineOnly`. A `HttpOverrides` counting client records every
    HTTP attempt; the offline case asserts the list is empty.
  - **Online controls (not tautologies):** the same widget and gesture under a
    networked profile (`offlineOnly: false`) must call `refreshMe`
    (`> 0`) and must reach the task endpoint (non-empty). This proves the drag
    gesture and the `_drainIo` real-async drain actually exercise the refresh
    path, so the offline assertions are not passing because the harness simply
    never fires.

These tests depend on the coordinator's shared-core guards:
`lib/pages/home_page.dart` (`if (_loggedIn &&
StudioProfile.current?.offlineOnly != true)` at both the `initState` and
`_onAuthChanged` call sites) and `lib/pages/profile_page.dart`
(`if (StudioProfile.current?.offlineOnly == true) return;` in `_refresh`). The
regression file verifies them from the Go side without editing the shared core.

A subtle harness note: the shell fires these refreshes with `unawaited`, so a
bare `tester.pump()` only advances the fake clock and never observes the HTTP
attempt. The `_drainIo` helper alternates `tester.runAsync` with `pump` to let
those real-I/O futures settle.

The test mounts the real `HomePage`, `FunctionsTab`, `ProfileTab`,
`SettingsPage` and `EditorPage` under the real `goProfile`. It adds **no**
package dependencies: it fakes `plugins.flutter.io/path_provider` through a
`MethodChannel` mock (as `test/native_startup_test.dart` does) and does not set
an explicit locale, so it never needs `flutter_localizations`,
`path_provider_platform_interface` or `re_editor` in `pubspec.yaml`.
`pubspec.yaml` / `pubspec.lock` are byte-identical to their pre-task state.

## 4. Verification run by this Pi

Owner scope verified: `Get-Location` and `git rev-parse --show-toplevel` both
resolve to `D:\MyNewProjects\qfli_go`; no sibling project or shared-core file was
edited by this Pi.

- `flutter analyze --no-pub` (whole Go project) → `No issues found!`
- `flutter test --no-pub --concurrency=1 test/go_offline_profile_test.dart`
  → 10/10 passed.
- `flutter test --no-pub --concurrency=1 test/go_offline_profile_test.dart
  test/native_startup_test.dart test/go_app_test.dart
  test/go_platform_test.dart` → 27 passed, 1 skipped (the SDK-gated
  `go run` compiler case), 0 failed.

Builds and device runs are intentionally **not** performed here; they are
serialized by the main coordinator to avoid holding the shared toolchain/device
locks.
