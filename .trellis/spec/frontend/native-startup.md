# HarmonyOS Native Startup

Execution policy: apply `AGENTS.md` and [Cloud-Only Execution](../backend/cloud-only-execution.md).
All analyze/test/build and dependency/toolchain setup commands below are
GitHub-hosted Actions only. No local project checks or artifact downloads.

## Scope and ownership

The Go product entry in `lib/main.dart` controls when Flutter submits its first
frame. `ohos/entry/src/main/ets/pages/Index.ets` supplies the native loading
builder to `FlutterPage`; `EntryAbility.ets` bridges initialization progress.
This follows the sibling `qflistudio` implementation. Shared bootstrap code
already supplies progress and is consumed without modification.

## Signatures and payload

| Boundary | Contract |
| --- | --- |
| Dart platform channel | `MethodChannel('qflistudio/platform')` |
| Method | `startupProgress` |
| Argument | `{ 'progress': double }`, normalized from 0 to 1 |
| Success | `null` |
| Invalid value | `INVALID_PROGRESS`; reject non-numbers and non-finite numbers |
| Native event | `EVENT_STARTUP_PROGRESS`, with the finite value clamped to [0, 1] |
| Native indicator | Event value multiplied by 100 for `Progress(total: 100)` |

`AppBootstrap.run(..., onProgress: ValueChanged<double>?)` reports 1/3, 2/3,
and 1 as the project, authentication, and settings loads finish. Individual
configuration load failures still count as completed; bootstrap can reach ready.
The splash subscribes in `aboutToAppear` and removes the same callback in
`aboutToDisappear`.

## First-frame contract

1. On OHOS, call `deferFirstFrame()` before `runApp`.
2. Start bootstrap in a post-frame callback. Deferred frames still perform build
   and layout, so initialization must not wait for rasterization.
3. Preserve the reference timings: 160 ms before bootstrap, a minimum display of
   1100 ms, and 320 ms after bootstrap. These only control presentation timing.
4. After bootstrap marks the app ready, await `binding.endOfFrame` so the home
   tree has completed build and layout.
5. Pair deferral with `allowFirstFrame()` in `finally`.
6. The installed OHOS embedding removes `splashScreenView` when its real
   `onFirstFrame` callback fires. The native page fades out over 280 ms.

The progress value reaching 1 must not dismiss the splash: the home frame may
still be pending. Waiting on `waitUntilFirstFrameRasterized` before
`allowFirstFrame` would deadlock. Other platforms keep the existing Flutter
fallback and do not send native startup progress.

`start_window_background` supplies the native background in both themes:
light `#F8F9FF`, dark `#111418`. Use the product's `app.media.icon`.

## Errors and cases

| Condition | Expected behavior |
| --- | --- |
| Slow local initialization | Keep the native layer and continue deferring Flutter frames |
| Initialization complete | Build/layout home, submit the first frame, then fade the native layer |
| Native progress channel missing | Ignore `MissingPluginException`; release the first frame normally |
| Native progress channel reports an error | Catch `PlatformException`; release the first frame normally |
| Invalid native progress payload | Return `INVALID_PROGRESS` without emitting an event |
| Finite payload outside [0, 1] | Clamp it before emitting |
| Another native target | Use the existing Flutter loading page with no OHOS delay |

Good: slow bootstrap stays covered even after the minimum display time.
Base: successful startup reports three completion steps and reveals the home.
Bad: removing the native layer on a timer or on progress 100 can expose an empty
surface before Flutter has presented the first frame.

## Verification

- `test/native_startup_test.dart`: slow startup holds `sendFramesToEngine`
  false; home appears before submission; progress is 1/3, 2/3, 1; other targets
  are not deferred; a rejected progress channel does not leave startup blocked.
- Use `TargetPlatformVariant` to restore debug platform overrides before
  Flutter's invariant checks. Create the cached AppPaths lookup outside per-test
  fake clocks so subsequent startup cases do not retain a closed test zone.
- `flutter analyze --no-pub` and `flutter test --no-pub test/native_startup_test.dart`.
- `flutter build hap --debug --no-pub` verifies the native builder and bridge.
- On a connected HarmonyOS device, inspect a cold start in light and dark modes
  and confirm continuous coverage through the first home frame. Widget tests
  and package compilation do not verify device compositor behavior.

## Offline native host

The Go standalone `EntryAbility` rejects both `openAgreement` and `openUrl`
with `OFFLINE_ONLY` before interpreting their arguments. It does not route to
AgreementReader or dispatch an external ability. Only Index is registered in
`main_pages.json`. Startup progress, local picker and system text sharing keep
their existing contracts.

This host policy is separate from authored Go programs. Do not remove Go's
`net`/`net/http` exports or INTERNET permission as a side effect: existing
loopback HTTP examples and debugger regressions use the native networking
capability. No network sandbox or zero-packet guarantee is implied.

`integration_test/go_catalog_test.dart` registers an actual OHOS channel check
for both rejected methods and HTTPS/HTTP/loopback/file/custom URI arguments,
then checks that startupProgress still succeeds. It adds
`QFLI_GO_OFFLINE_HOST_AUDIT` and `goOfflineHostAudit` evidence. Other host
platforms skip this OHOS-specific check; a Dart source test or HAP marker alone
does not prove its native execution.
