# Hosted regression fixtures

## 1. Scope / Trigger

Apply this contract when repairing Go product tests after a shared-core or
hosted-runner change. All checks run in GitHub-hosted Actions under
[Cloud-Only Execution](../backend/cloud-only-execution.md).
Source inspection does not establish a hosted pass.

## 2. Signatures

- `Future<void> startGoApp({AppFormFactor? formFactor})` starts the real Go app.
- `main()` delegates with no override, preserving normal host resolution.
- Phone startup tests pass `AppFormFactor.phone` explicitly.
- `testWidgets` accepts a boolean `skip`; preserve the original predicate.
- `.gitattributes` uses exact `-text` paths for byte-sensitive curriculum files.

## 3. Contracts

`TargetPlatformVariant` controls Flutter's target-platform override. It does not
replace the operating-system lookup used by shared-core form-factor resolution.
Phone startup tests select the phone shell while exercising the real bootstrap,
progress channel, timing, first-frame deferral and release. See
[Native Startup](native-startup.md) for the platform contract.

The four local project scopes are history, workspace, all and favorite. Assert
their four exact `home-scope-tab-*` keys and cloud absence. The independent
`home-scope-tab-agents` tab does not add a project scope. Tools use a lazy vertical
viewport beneath `PageStorageKey<String>('tools-scroll')`; scroll each required
card into view and retain its assertion. Pump after `scrollUntilVisible` finishes
its final `ensureVisible` before reusing the lazy viewport. Wait for a previous
dialog's exit transition before opening and asserting the next one.

`WorkspaceStore.instance` retains its queue tail across widget test clocks.
Before closing each clock, enqueue a final `WorkspaceStore.instance.load()`
inside `tester.runAsync` and capture its future. Do not await its fake-zone
predecessor there. Include the captured future in the original error-observing
drain while pumping prior fake-zone work. This leaves the singleton tail in the
real zone. Retain all store/history drains, error assertions and timeout bounds.

Curriculum assertions compare authored bytes, not normalized text. Preserve the
existing mixed newline bytes of `tool/go_curriculum/samples/T002` through `T040`
and `T083` `go.mod` files. Preserve raw CRLF bytes of
`assets/curriculum/examples.json` and `tutorials.json`, whose SHA256 values are
recorded in the existing audit manifests. These 42 exact paths use `-text`.
Do not replace this with `eol=crlf`, bulk normalization, regenerated manifests,
or relaxed equality assertions. The other catalog copies remain semantic inputs.

After changing attributes, the Git executor explicitly stages these exact paths
and verifies indexed bytes against the reviewed raw hashes. A cached clean
status does not establish that the index contains the required bytes.

## 4. Validation & Error Matrix

| Condition | Required result |
| --- | --- |
| Phone startup test runs on Linux | Phone shell selected explicitly; real startup assertions retained |
| Screenshot encoder returns null | Fail with a diagnostic; never report an empty successful image |
| Agents appears beside four local scopes | Assert Agents separately and retain all four scope checks |
| Required tool card starts below the viewport | Scroll the real vertical viewport, then assert and interact |
| Reusing a lazy viewport after `scrollUntilVisible` | Pump its final `ensureVisible` before the next lookup |
| Singleton queue survives a widget test clock | Enqueue its final load in the real zone; pump and observe every drain before closing the fake clock |
| Catalog or fixture bytes differ from the frozen contract | Keep the strict failure; repair source byte preservation |
| Test evidence belongs to another SHA | Record it as historical, not a current pass |

## 5. Good / Base / Bad Cases

- Good: select the intended shell, wait for transitions, then retain all checks.
- Base: `main()` keeps platform defaults for normal product launches.
- Bad: increase a tab count, remove a screenshot assertion, normalize fixture
  strings, or regenerate audit hashes solely to make a failing test pass.

## 6. Tests Required

Hosted `flutter analyze --no-pub` and the Quality workflow's Flutter suite must
cover native startup, saved workspaces, offline profile, tools, curriculum
content and catalog audit. Keep real native preflight and integration assertions.
Record source SHA, workflow/run/attempt/job IDs, failures and skips separately.
Both fixture repairs require hosted proof at the changed source SHA. A reviewed
viewport sequence alone does not establish the cause of a hosted tools failure.

## 7. Wrong vs Correct

Wrong: assume `TargetPlatformVariant` selects a phone shell on every host, or
use newline conversion to repair a byte-equality assertion.

Correct: call `startGoApp(formFactor: AppFormFactor.phone)` in phone startup
tests and preserve exact curriculum bytes through narrow Git attributes.
