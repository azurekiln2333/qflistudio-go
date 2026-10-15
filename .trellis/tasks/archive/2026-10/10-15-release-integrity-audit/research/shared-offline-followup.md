# Shared offline background and shortcut follow-up

## Ownership and baseline

- Coordinator authorized this bounded shared-core follow-up and owns integration
  and commits. Implementation agent: `shared_offline_followup`.
- `Get-Location` and `git rev-parse --show-toplevel` verified
  `D:/MyNewProjects/qfli_studio_core`; test commands ran from
  `D:/MyNewProjects/qfli_go` with `--no-pub`.
- All assigned paths were clean before edits. Existing `editor_page.dart`,
  `retained_editor_host.dart`, aggregate content assets, language products and
  platform files were not edited.
- Read Go parent PRD/design/implementation/context manifest plus shared-core
  AGENTS, frontend indexes/component/state/quality/type guidelines and thinking
  guides before editing. No public interfaces were added.

## Confirmed gaps and repairs

1. `lib/pages/profile_page.dart`: pull-to-refresh called `AuthStore.refreshMe`
   with restored credentials even when the account UI was hidden. Return early
   for `StudioProfile.current?.offlineOnly == true`.
2. `lib/pages/home_page.dart`: signed-in initialization and authentication changes
   launched daily-task refreshes for offline products. Gate both callers using
   the same profile policy.
3. `lib/services/task_activity_service.dart`: create/open/save activity generated
   remote pending events and synchronized them for any restored account.
   Offline mode now persists local daily/all-time counts without adding remote
   events or scheduling synchronization. Both forced and ordinary sync/refresh
   paths respect the offline policy. The serialized sync loop and task refresh
   also recheck the policy before making their next request. Old pending events
   are preserved, not deleted, and can still synchronize in a networked product.
4. `lib/terminal/widgets/shortcut_bar.dart`: the expanded panel exposed network
   tools and `git status` in offline products. Hide the network group and Git
   quick command; retain local commands, symbols and keyboard controls. The
   collapsed tooltip also follows the policy. Networked product UI is preserved.
5. `lib/terminal/shell/sandbox_shell_backend.dart`: help/error copy named Java
   despite language-owned delegates. Replace it with generic host toolchain
   wording; routing and sandbox capabilities are unchanged.

## Regression coverage

New shared file: `test/offline_background_and_shortcuts_test.dart` (8 tests).

- Credentials are written through real `AuthStore`, then loaded into a new store
  to reproduce restored sessions rather than only setting an in-memory token.
- Injected `ApiClient`/`MockClient` records requests: offline create/open/save and
  forced sync/refresh emit none, add no remote events, and preserve counts after
  service restart.
- An existing pending event survives offline forced sync/refresh, then uploads
  with its original event ID when the profile permits network access.
- Networked activity upload, task refresh, points update, checkin and calendar
  remain functional with the same endpoints.
- Actual `ProfileTab` refresh callbacks skip auth refresh offline and retain it
  online; an AuthStore override observes the refresh call without real HTTP.
- Actual expanded `ShortcutBar` hides all 11 network commands and Git offline,
  retains them online, and still emits local `pwd`/Tab actions in both cases.
- The sandbox help and an actual unknown-command diagnostic use generic host
  toolchain wording.

## Validation

Default SDK executable: `D:/ProgramFiles/flutter_ohos/bin/flutter.bat`.

```text
flutter test --no-pub --concurrency 1 \
  ../qfli_studio_core/test/offline_background_and_shortcuts_test.dart \
  ../qfli_studio_core/test/task_activity_service_test.dart \
  ../qfli_studio_core/test/sandbox_terminal_test.dart
=> 34 passed, exit 0

flutter analyze --no-pub \
  ../qfli_studio_core/lib/pages/profile_page.dart \
  ../qfli_studio_core/lib/pages/home_page.dart \
  ../qfli_studio_core/lib/services/task_activity_service.dart \
  ../qfli_studio_core/lib/terminal/widgets/shortcut_bar.dart \
  ../qfli_studio_core/lib/terminal/shell/sandbox_shell_backend.dart \
  ../qfli_studio_core/test/offline_background_and_shortcuts_test.dart
=> No issues found, exit 0

git diff --check -- <five owned tracked source paths>
=> exit 0 (line-ending notices only)
```

The initial shortcut widget tests needed one `pumpAndSettle` to finish the
localized widget/expanded-panel frame before asserting rendered descendants;
after fixing the test setup, the isolated 8-test run and combined 34-test run
both passed.

## Integration boundary and follow-ups

- No staging, commits, resets, builds, device operations, package resolution or
  content mutations were performed by this agent. Main owns the exact-path
  review/commit and release-wide validation.
- User-triggered checkin/calendar implementations were left unchanged, with
  positive networked regressions. Existing offline UI gates hide their routes;
  this follow-up repairs the reachable background activity paths.
- No device behavior or full release/build success is claimed by these results.
- Suggested scoped commit: `fix(offline): block background refresh and network shortcuts`.
