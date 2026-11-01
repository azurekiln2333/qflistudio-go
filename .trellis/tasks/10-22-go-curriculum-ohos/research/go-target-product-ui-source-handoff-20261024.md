# Go target product UI acceptance source handoff

Date: 2026-10-24, Asia/Shanghai.
Owner: `go_target_product_ui_1024`.
Active task: `10-22-go-curriculum-ohos`; dependency: `10-22-go-offline-ide`.

## Change boundary

The existing target IDE helper exercises real analyzer/tools/debugger APIs but
does not mount the editor or operate the product's panels/cards. This extension
owns only the new `integration_test/go_product_ui_acceptance.dart` helper and
this handoff. It will mount the actual unchanged `goProfile`, `EditorPage` and
`FunctionsTab`, exercising their real bundled-FFI adapters. It will inspect
installed diagnostics decorations, operate Problems navigation, use actual
gutter/debug panel controls, and use the direct source/module tools with real
project files. Named multi-root restoration will be included where existing
public persistence interfaces can be reused without product changes.

No integration entrypoint, production implementation, shared core, native
runtime, catalog, binary or sibling product is edited by this owner. The parent
owns registration after independent review. No test double replaces the Go
analyzer, debugger, tools, project store, filesystem or workspace store.

Go236 remains RELEASED. No Go/gofmt/SDK/Dart/Flutter/test/analyze/build/WSL/device
command, kill/reset, staging, commit or push is authorized by this source task.
All authored runtime/widget operations remain UNRUN and unformatted. Source
inspection is not a Dart parser/type-checker or target acceptance result.

## Implementation and ownership checkpoint

The helper is authored and was frozen at the 992-line snapshot below for
independent review by `go_target_acceptance_check_1024`. Code ownership, both
entrypoint registrations and any subsequent helper fixes have been handed to
that checker under the parent. This owner finishes only this handoff. The
snapshot identifies the reviewed input, not any later checker result.

Public registration:

```dart
Future<void> Function() registerGoProductUiAcceptance({
  required IntegrationTestWidgetsFlutterBinding binding,
  bool requireEmbeddedRuntime = false,
  Future<Map<String, Object?>> Function()? runtimeIdentity,
  Future<void> Function()? beforeAudit,
})
```

The parent/checker must connect the existing predecessor barrier to the native
API helper, then pass that helper's returned barrier as this helper's
`beforeAudit`. The new helper is intentionally not registered by this owner.
Its returned callable waits for the actual UI body and confirmed cleanup;
the test framework's six-minute observation timeout does not release ownership.
The actual `_ProductUiAudit` and retained fixtures are captured by that callable.

The default runtime identity reader is the existing public
`loadedGoNativeAuditRuntime`; catalog registration can inject its existing
loaded-library identity reader. A normal desktop registration is explicitly
skipped. `requireEmbeddedRuntime: true` instead requires the actual embedded
backend and fails on an SDK host. A skipped/filtered registration is a no-op
barrier and does not establish target acceptance.

Marker: `QFLI_GO_PRODUCT_UI_AUDIT`.
Merged `binding.reportData` key: `goProductUiAudit`.
Report: `product-ui-report.json` under the retained target temporary root.

## Authored operation contracts

Every operation below is **UNRUN**. The exact four IDs must appear once, pass
without skips, and have confirmed cleanup for final report success. The report
also requires loaded-runtime path/SHA-256 identity and unchanged process cwd.

| Operation ID | Actual product surface and assertions |
| --- | --- |
| `editor-unsaved-waves-problems` | Mount real `EditorPage` and verify the installed analyzer is `goProfile.codeAnalyzer`. Edit an unsaved CRLF document containing Chinese, emoji and illegal `💥`; require the native diagnostic's exact two-unit UTF-16 range/current file. Inspect the installed editing-controller span hook, matching diagnostic decorations and actual gutter painter. Operate the real Problems status and row, asserting editor selection. Fix the unsaved document and require cleared waves/gutter/Problems. Saved bytes and an initializer marker must remain untouched throughout. |
| `editor-gutter-debug-panels` | Use the actual gutter and shared Debug controls backed by `goProfile.debugger`. Require a verified line-5 pause with scalar 42/source navigation before a marker write; StepOver to line 6/scalar 43/new pause token; Resume to real termination, stdout `43`, marker write and registry release. Open actual Output and verify debug attribution. Edit a genuine `sync.Pool.New` callback, start through the same UI, require dirty source saved, logical native-callback label and honest unavailable locals; inspect its actual Debug Console boundary log, then use Stop and confirm registry release. |
| `direct-tools-real-source-projects` | Mount actual `FunctionsTab`, using unchanged `goProfile.toolsTabBuilder -> createGoIdeTools`. Operate direct Go tool cards, native malformed/valid formatter input and use-result replacement; inspect genuine alias/type/method output; inspect the second real project's go.mod, switch to the first project, require stale results clear and first-project module output. Assert both source files stay unchanged. The card reveal helper resets the real scroll position before searching lazy cards. |
| `named-multi-root-sidebar-retention` | Save a real named session through `WorkspaceStore`, with two project roots, ordered owned documents, distinct cursors, expanded src/cmd directories and roots. Mount the actual retained editor, close/reopen its sidebar, minimize/restore the editor, and require the same controller/tabs/dirty secondary text/cursor with unchanged disk bytes. Restore clean buffer bytes, drain analysis/debug, unmount, settle writes, load a separate store from disk and reconstruct the editor; require restored ownership/cursor/expanded trees and no source text in workspace JSON. |

This helper's workspace scope is **named-session API plus actual retained editor**.
It does not claim target Home save/rename/remove/CRUD coverage. The separately
authored `test/go_saved_workspaces_test.dart` and target Home interaction remain
distinct acceptance work. The tools' JSON-to-Go card is checked for direct
availability, not executed here. Run/terminal execution remains covered by
separate acceptance operations; debug stdout is not attributed to Run.

## Cleanup and retained ownership

`_cleanup` obtains the actual mounted analysis/debug controllers even if the
action failed before its normal assignment. It retains the original
`debug.close()` Future and the same controller/fixture, tracks session IDs
before/during/after close, and pumps until that Future actually finishes. After
15 seconds it publishes `cleanup-pending` with the observed session or starting
identity every five seconds. It neither starts the next case nor substitutes a
new close Future. Completion also requires `debug.busy == false` and real
`NativeGoDebugBackend` registry polls returning `ok: false` for every observed
native session ID.

The final source pass found that shared analysis `pending == false` can mean
the watchdog expired while the actual native isolate still runs. The helper
therefore retains the real `EditorAnalysisController` and waits for an accepted
completed result (`checked && !pending`) before unmount. Actual tool pages remain
mounted until their busy labels clear; those labels clear in the real tool
Future's `finally`. These waits use the same 15-second/every-five-second pending
publication pattern, preserving the actual mounted state and fixture. The
workspace's intentional reconstruction also waits for final accepted analysis
before disposing its first page.

**Known conservative limit for independent review:** the analysis controller
does not expose its actual in-flight Future or a public drained flag. A genuine
returned unavailable result also leaves `checked == false`, so this snapshot
will retain ownership rather than infer drain from an unavailable message.
That can hold the barrier after a completed failure; it is not evidence of a
live native request. Independent review owns any helper-only refinement.

Only after confirmed runtime drain does cleanup unmount the app, settle real
workspace writes, dispose owned stores/hosts and delete fixture-owned data.
The root report and PNGs remain available outside deleted fixture subdirectories.
Errors retain the fixture/controller references and leave the returned barrier
unresolved. A failed or uncertain cleanup cannot yield a successful report.

## Screenshots and evidence limits

`capture` first tries `binding.takeScreenshot`. When unsupported or empty, it
captures the actual mounted `RepaintBoundary` as PNG. Each artifact records
method, path, byte count and SHA-256, plus the binding failure if present.
The OHOS integration-test plugin inspected in the installed SDK explicitly
returns notImplemented for captureScreenshot/convertFlutterSurfaceToImage/
revertFlutterImage, so the fallback is necessary there. This snapshot does not
convert Android's Flutter surface first; a binding conversion error is recorded
and the same honest mounted-boundary fallback is used.

The diagnostics operation invokes the installed span hook and actual painter;
it does not inject fabricated diagnostics or call a decoration helper with
invented results. It still requires target execution and inspection of captured
images before claiming visually accepted editor waves. No screenshot was taken,
rendered or manually inspected by this source continuation.

## Source/API references

These are real inspected local interfaces; no production API was added.

| Path | Relevant contract |
| --- | --- |
| `integration_test/go_product_ui_acceptance.dart:52` | Registration, predecessor/body/ownership barrier. |
| `integration_test/go_product_ui_acceptance.dart:200` | Actual controller/native/analysis/tool cleanup; pending publication. |
| `integration_test/go_product_ui_acceptance.dart:350` | Binding/actual mounted-boundary screenshots and artifact identity. |
| `integration_test/go_product_ui_acceptance.dart:385` | Installed diagnostic spans/gutter and actual Problems navigation. |
| `integration_test/go_product_ui_acceptance.dart:467` | Actual gutter/Debug/Output/Console operations and native release polls. |
| `integration_test/go_product_ui_acceptance.dart:576` | Direct source and module tool widget interaction. |
| `integration_test/go_product_ui_acceptance.dart:662` | Named session, retained sidebar/editor and disk reconstruction. |
| `../qfli_studio_core/lib/editor/editor_analysis_controller.dart:117` | Watchdog observation is separate from `_run` actual completion at line 196. |
| `../qfli_studio_core/lib/editor/editor_debug_controller.dart:802` | Real `close()` retains its original close Future. |
| `lib/native_go_analysis_ffi.dart:14` | Analysis/formatting use actual isolate-backed FFI and native response freeing. |
| `lib/go_tools_page.dart:214` | Actual source tool Future and busy-state lifetime. |
| `../qfli_studio_core/lib/workspace/workspace_store.dart:142` | Real named save; saveSession at line 217. |
| `D:/ProgramFiles/flutter_ohos/packages/integration_test/lib/integration_test.dart:187` | Installed binding takeScreenshot returns `Future<List<int>>`. |
| `D:/ProgramFiles/flutter_ohos/packages/integration_test/ohos/src/main/ets/components/integration_test/IntegrationTestPlugin.ets` | Installed OHOS screenshot methods are notImplemented. |

## Frozen source snapshot

SHA-256 values below were captured in one bounded read-only Python invocation.
Dependencies remain concurrently owned; these hashes identify inspected bytes
and are not a publication or package binding. The independent checker may
produce a later helper identity after taking ownership.

| Path | SHA-256 |
| --- | --- |
| `integration_test/go_product_ui_acceptance.dart` (992 lines) | `7909fa810a870da323487764dcf591479efe8dc15350ba1f7f6129080f06f5b9` |
| `integration_test/go_native_ide_acceptance.dart` | `c8a490f190eff2edf00a298cf2a653cffa93bfbb67282e216adc028ee450613e` |
| `lib/main.dart` | `af2d50cc8a183c7131636bc6bacf4de6ed932efa0747fb69c4a5c78ed9fa0dd9` |
| `lib/go_code_analyzer.dart` | `71ffc2f4b0da4e13f5334782cc3ed38e748f1981d960ba1228ac30ba31dececb` |
| `lib/native_go_analysis_ffi.dart` | `88907783d67bca84527b7a0c2eaea979e40ccbeca5fe85d1ab4e286b0823abe6` |
| `lib/go_studio_debugger.dart` | `d2db8f005b95c73cbbe666526927f094747aed46aed8a3ecaa45b69e2cdb4a46` |
| `lib/go_debugger.dart` | `59510744f044d9d791280eb2f66ddd3881e7ee21cd056101eee63c74af0c1284` |
| `lib/go_tools_page.dart` | `bf3f93afc13457e3ceb3ab2324741023dd016abcc87c05020908d9cd03f43482` |
| `../qfli_studio_core/lib/editor/editor_page.dart` | `8549c7e4d00692c27876636d436811100a231d04cb842f263d50eaaab7c07ca4` |
| `../qfli_studio_core/lib/editor/editor_analysis_controller.dart` | `7b6e83e668c7eb3abe8b6b2b127bff39f52f32d5bb0c21fb0ca8f8b0113be20b` |
| `../qfli_studio_core/lib/editor/editor_diagnostics.dart` | `0627318dbeb531b3ca3f6eef60397e41e8e24ce959aeb2f0aa4ac240df0bdb2d` |
| `../qfli_studio_core/lib/editor/editor_problems_bar.dart` | `dafbfc6aec077afb715484861198d269b564a2bf248bb13a78eea7c184fd470f` |
| `../qfli_studio_core/lib/editor/editor_debug_controller.dart` | `4233d340f30ae39c152af31975e425fac016f7f4fb63d009c19ddaea1ae2b0d9` |
| `../qfli_studio_core/lib/editor/editor_debug_widgets.dart` | `b14cabf2e93eada57c011d5935e8d0d531ca0358f6b1281dcbc8b48fa647a521` |
| `../qfli_studio_core/lib/editor/editor_output_panel.dart` | `145d59d02f7a8117a639df8db117b8cd7edcd6ed98528608abf77ba9a035e2ae` |
| `../qfli_studio_core/lib/editor/retained_editor_host.dart` | `58d91921b177173842222f1d2aecb1261f73633abe3a8fefeb4ae33f27e8ba78` |
| `../qfli_studio_core/lib/workspace/workspace_store.dart` | `1c1cd747f3b3c66b92399aa92a6f61703774a6e1754423ca61acf222a9fecf8d` |
| `../qfli_studio_core/lib/pages/quick_tools_page.dart` | `ddd3ff649d3bf0618422943b021d82798be0ecee983b5a30a4b11fea72390f92` |

## Verification and remaining gates

- Bounded manual source/API inspection and full-file UTF-8, final newline,
  trailing-whitespace and conflict-marker checks passed for the frozen helper.
- Earlier scoped `git diff --check` returned exit 0, but both owned files are
  new/untracked; full-file Python scans provide the actual whitespace evidence.
- Python only inspected source text and hashes. It did not parse Dart or execute
  an inspector, fixture, emulator, native runtime, SDK or test.
- Dart formatting, analysis, type-checking, widget tests, real native FFI,
  packaged-runtime execution, target screenshots and visual review are **UNRUN**.
- Formatter exact-output expectation, target geometry/scrolling, debugger
  callback behavior and all persistence/reconstruction assertions still require
  execution. Independent review and parent registration are separate work.
- Native handle 85731's retained failure is not superseded by this source work.
  No full Go, OHOS or umbrella objective completion is claimed.
