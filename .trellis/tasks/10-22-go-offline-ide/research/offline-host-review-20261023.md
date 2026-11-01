# Offline OHOS host review

Date: 2026-10-23, Asia/Shanghai. Reviewer: `go_independent_check`.
Scope: static review of the Go host URL-dispatch repair and its audit wiring,
plus the existing lightweight synthetic inspector fixture. Only research files
and the research fixture were changed by the reviewer.

## Findings (fixed)

No product fix was needed during this review. The research fixture's synthetic
kernel payload was updated to include `QFLI_GO_OFFLINE_HOST_AUDIT`, matching the
new required marker in `tool/inspect_go_catalog_hap.py`.

## Findings (not fixed)

No new issue was found in the scoped source changes.

`EntryAbility.ets` rejects both `openAgreement` and `openUrl` with exactly
`OFFLINE_ONLY` before reading arguments. It no longer imports Want/router or
contains the former `router.pushUrl` / `startAbility` dispatch paths.
`main_pages.json` registers only `pages/Index`; the retained AgreementReader
source has no registered route or reference from the host. The startup event,
finite-value/clamping behavior, result reply, local picker and system text-share
paths retain their existing code and contracts. INTERNET permission remains in
the module profile as requested; this change does not disable authored Go
networking or claim an operating-system network sandbox.

The added integration check uses the actual platform MethodChannel, with no
mock handler. On OHOS it makes ten calls: both rejected methods against HTTPS,
HTTP, loopback HTTP, file and custom URI inputs. Every call must throw
PlatformException with `OFFLINE_ONLY`. Only after all ten succeed does it call
`startupProgress` and set `startupProgressPreserved`. The new reportData spread
retains the preceding catalog audit data. The new check is explicitly skipped
outside OHOS. The startup check proves a successful native method reply when
run; it does not separately prove visual progress delivery or cold-start
compositor behavior.

The native-startup spec describes this host policy and keeps authored Go
network capability separate. The inspector requires the new offline-host marker
alongside the existing catalog markers while retaining `deviceExecution=false`
and a separate signature gate.

The in-progress ordinary native callback/epoch repair was not reviewed or
executed in this pass, as directed by the coordinator.

## Source checkpoint

Full machine-readable record:
`research/offline-host-source-review-20261023.json`.

| File | SHA256 |
| --- | --- |
| `ohos/entry/src/main/ets/entryability/EntryAbility.ets` | `2522c581738465fdcf2911f01ecda0c54661728c7b866d9ecb8853b5b1529bd4` |
| `ohos/entry/src/main/resources/base/profile/main_pages.json` | `f21984fb1d5096f0db41314da0bb94c573e7ad018e5afae3044f8d5ff71b0bfc` |
| `integration_test/go_catalog_test.dart` | `5e1b1c95530f7c5f34643d15174ecfc903c34277c380d6715558b32d7e571d1a` |
| `tool/inspect_go_catalog_hap.py` | `16a1db6fdd7db360ad22a22c1f2124425421cab28604dd223ae9701ed8303199` |
| `.trellis/spec/frontend/native-startup.md` | `a384ec36d037b9b0c14e73b5f54e30d42f7702a6a7ed485d63ce5be82858a1d1` |
| `research/fixtures/inspector_binding_review.py` | `9af4788effb1d8694337dddc4cd17a24f6bde34984ad397653b318284eddf1a8` |

## Verification

- Updated synthetic inspector fixture: **11/11 pass**, recorded separately in
  `research/inspector-binding-review-offline-host-20261023.json`.
- It again accepts identity and the exact SDK strip transform for both actual
  Go library ABIs, and rejects single-byte package mismatches, source digest
  drift, missing build ABI, build script drift, missing catalog case and an
  unexpected packaged ABI. Synthetic kernel markers are fixture inputs and do
  not establish actual native host execution.
- Python AST parsing for inspector and fixture: pass.
- `main_pages.json` parsing: pass, exactly `pages/Index`.
- Focused `git diff --check`: pass (only line-ending conversion notices).
- Lint / TypeCheck: not run under the coordinator's no-heavy-build/check queue.
- Actual Dart/ArkTS integration tests: not run.
- Real Flutter/Go/native/HAP build, signature verification, installation and
  actual OHOS host/channel execution: **pending**. No native-runtime repair
  acceptance or whole-task completion is implied.
