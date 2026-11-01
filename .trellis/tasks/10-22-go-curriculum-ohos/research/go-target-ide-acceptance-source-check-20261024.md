# Independent Go target IDE acceptance source check

Date: 2026-10-24, Asia/Shanghai.
Reviewer: `go_target_acceptance_check_1024`, dispatched `trellis-check`.
Active task: `10-22-go-curriculum-ohos`; native IDE dependency:
`10-22-go-offline-ide`.

This is **SOURCE REVIEW ONLY**. All Dart formatting/parsing/type checking,
lint, unit tests, synthetic inspector fixture execution, native integration,
HAP builds and actual target operations remain **UNRUN**. No Go, gofmt, SDK,
Dart, Flutter, analyzer, build, WSL, device, kill/reset, commit or push command
was invoked by this reviewer. These source edits acquire and reserve no slot;
the root session owns all exact runtime handle/exit/release accounting.

## Findings fixed

### 1. Catalog timeout ownership escaped into a later registered test

The pre-review `_runNative` cancelled after its 20-second observation window,
then observed the result for five more seconds. A second timeout propagated to
the corpus loop. That loop already set `priorInvocationStuck`, retained the
fixture and refused subsequent native corpus calls; it did **not** delete the
active fixture or launch another corpus item. The actual gap was that the
original result Future then went out of scope and the next separately
registered IDE test could start.

`observeCatalogNativeExecution` now retains the exact `execution.result`
Future, dispatches cancellation once, publishes `HOLD-native-result-pending`
after the cleanup observation deadline, and awaits that same Future. A failed
cancellation dispatch is recorded and does not abandon the result. The original
execution timeout remains a failed result (`timedOut: true`, harness exit 124)
even after the native result eventually arrives; native exit/output/testing
metadata are retained separately.

The case/fixture path and explicitly labeled Dart Future identity are published
through merged `reportData` and `QFLI_GO_CATALOG_NATIVE_OWNERSHIP`. The public
`NativeGoExecution` exposes result/cancel only, while its numeric native ID is
private to the FFI bridge. The report therefore records `nativeRunId: null`
with an explicit reason. A Dart identity hash is **not** a native handle.

The corpus body also exposes an actual-finally completion barrier to the next
IDE test. A three-hour test-framework observation timeout cannot release that
barrier while the asynchronous body still owns its native result.

### 2. Existing native cancellation tests could dispose fixtures early

The infinite-program case previously awaited `result.exitCode.timeout(5s)`
then deleted its project from `finally`. The terminal-interruption case also
used a bounded `backend.execute` observation and only called shell shutdown in
cleanup. Current shared `BaseShellBackend.shutdown` disposes output; it does
not interrupt or await a delegated native execution. A failed startup-marker
assertion could take this cleanup path before interrupt was requested.

The native entrypoint now retains and drains the original exit/execute Future.
Observation expiration publishes a HOLD, awaits actual completion, then still
fails the original deadline. The terminal cleanup explicitly interrupts an
unfinished execution and awaits its exact Future before shell shutdown and
project deletion. A lightweight sequential body-finally barrier covers all five
existing tests and is passed to the IDE acceptance helper, so framework timeout
does not allow a later native body to overtake cleanup.

### 3. The API test also needed a completion barrier for later UI acceptance

`registerGoNativeIdeAcceptance` now accepts an optional predecessor barrier and
returns its own cleanup barrier:

```dart
Future<void> Function() registerGoNativeIdeAcceptance({
  required IntegrationTestWidgetsFlutterBinding binding,
  bool requireEmbeddedRuntime = false,
  Future<Map<String, Object?>> Function()? runtimeIdentity,
  Future<void> Function()? beforeAudit,
});
```

The returned callable waits the actual API body's finally, after predecessor
release and native lease cleanup. It remains pending if a session cleanup is
uncertain (`pendingCleanup` is nonempty). A skipped/not-selected test has no
owned body and its barrier is a no-op. Both entrypoints now capture this
callable as `waitForApi` and pass it to the independently authored product UI
helper's `beforeAudit`. The catalog path preserves `requireEmbeddedRuntime:
true` and its actual loaded-runtime identity reader for both gates. The native
path preserves the normal host skip. The chain is predecessor body cleanup,
then API body cleanup, then UI acceptance; no timeout grants a later test
ownership of the preceding test's runtime.

### 4. Packaged audit marker negative coverage was incomplete

The inspector requires both `QFLI_GO_NATIVE_IDE_AUDIT` and the independently
authored UI helper marker `QFLI_GO_PRODUCT_UI_AUDIT`. Synthetic positive kernels
contain both. Two explicit negative fixtures now omit each marker independently
and require rejection naming the missing marker. These are authored fixtures,
not executed HAP or synthetic-suite evidence.

### 5. UI cleanup confused a completed unavailable result with a live analyzer

Reviewed the complete 992-line frozen UI helper input with SHA-256
`7909fa810a870da323487764dcf591479efe8dc15350ba1f7f6129080f06f5b9`.
Its cleanup correctly refused to accept generic `pending == false`, because
the shared controller watchdog sets that flag without awaiting the provider.
However, requiring `checked == true` forever also retained a native request
whose actual provider Future had already returned an unavailable result.

The helper now accepts a checked/nonpending result, or only the two completed
failure prefixes proven by current source: `Go source analysis: ` is returned
by `GoSourceTools.inspect` after its awaited backend completes or throws;
`本地检查暂时不可用：` is assigned by `EditorAnalysisController` after awaiting
`analyze` throws. The single shared analysis lane cannot dispatch a second
provider until the first returns. Watchdog/unknown states remain HOLD and keep
the real mounted controller and fixture. A drained unavailable result is
recorded in `analysisDrainUnavailableReason`, marks the case failed, and
cannot become clean-analysis or successful UI acceptance evidence.

## Product UI source review

- Matched installed `re_editor.buildTextSpan`, diagnostic range decoration,
  gutter painter and actual Problems status/ListTile navigation APIs.
- Matched real gutter/debug controls, verified breakpoint/step/locals source,
  callback labels/unavailable-locals semantics, and Output/Debug Console keys
  and attribution. Native registry polls remain actual FFI calls.
- Matched real direct Go cards, project picker/report structure and busy
  labels. The mounted source/module tool labels clear in the actual awaited
  Future's `finally`, so cleanup retains the tool until that lane drains.
- Checked an apparent `FilledButton.icon` subtype concern against installed
  Flutter source: it is a constructor of `FilledButton`; the existing
  `find.widgetWithText(FilledButton, ...)` is valid and was not changed.
- Matched real named-session persistence, ordered document ownership/cursors,
  expanded roots and retained-editor restore interfaces. Named-session API
  plus retained editor is the claimed scope; target Home CRUD remains separate.
- Retained the original debug close Future/controller/fixtures, existing
  periodic pending evidence, exact session IDs and registry rejection checks.
  Screenshot bytes are hashed and retained; the fallback captures the actual
  mounted repaint boundary when the target binding screenshot is unavailable.

## Review and authored regression coverage

- Matched analyzer requests/results to the current `GoCodeAnalyzer` and shared
  document/diagnostic API. Unsaved CRLF/Unicode range assertions, initializer
  non-execution and unchanged disk bytes are preserved.
- Matched formatter/inspector calls to actual `createGoIdeTools` adapters and
  the native parser/formatter response decoder; no fake backend was introduced.
- Matched launch/step/resume/thread tokens, shared `done`, raw close/terminal
  registry rejection, callback kind/boundary/history and unavailable-locals
  accessors against current product source.
- Kept all five exact API operation IDs and existing catalog/native/offline-host
  checks. Host execution still cannot satisfy the target audit.
- Added two completer-driven unit regressions to the existing catalog audit test
  harness: successful and failed cancellation dispatch. Each asserts pending
  observation does not advance, the same Future identity remains owned, cancel
  is called once, eventual completion drains, and the original timeout remains
  a failure. Both are **UNRUN**.

No further concrete widget/API/type mismatch was found by manual inspection.
This is not a Dart compiler, analyzer or target execution pass. Helper and both
entrypoint ownership are handed back to the root after this source snapshot.

## Verification performed

- Read the complete saved Trellis role context and active task artifacts/specs.
- Python `ast.parse` passed for both changed Python sources without importing
  either module, invoking a subprocess, producing bytecode, or running tests.
- UTF-8 decode, final newline, trailing-whitespace and merge-marker scans were
  clean for all seven reviewed source files, including untracked files.
- Scoped `git diff --check`: exit 0. Git prints the existing LF-to-CRLF notice
  for the tracked native entrypoint.
- Dart formatting, lint, TypeCheck and all tests: **UNRUN**, awaiting a new
  explicit named grant. Runtime assertions remain unproven.

## Reviewed snapshot

These are SHA-256 hashes of the source-review snapshot, not a publication freeze.
Later root UI registrations or formatting will legitimately supersede them.

| Source path | SHA-256 |
| --- | --- |
| `integration_test/go_native_test.dart` | `ccc7239db6f916878d227fb00903435ee4effb815f94c3ad2b0d3de0ed06e2b3` |
| `integration_test/go_catalog_test.dart` | `e08e1292ed31ec398d823aabf340caea6c5e5df860fd845a092a9297049e88cc` |
| `integration_test/go_native_ide_acceptance.dart` | `c8a490f190eff2edf00a298cf2a653cffa93bfbb67282e216adc028ee450613e` |
| `integration_test/go_product_ui_acceptance.dart` | `97c313836f111d196c7882048e8c2a689ab7b17165c7570ff3037dae7bdeecfd` |
| `tool/inspect_go_catalog_hap.py` | `5dccdad8f47c0694c09376b518539b5d36c0b6b76f8661be604d4a8d43ea0518` |
| `test/go_catalog_audit_test.dart` | `cf2c6d4769a7b2cfaf034fda960f48dbfc3083d74a8e6bb47d5248eda7e83a1e` |
| `.trellis/tasks/10-22-go-offline-ide/research/fixtures/inspector_binding_review.py` | `86b73fc7065d87a4840bef5e6104f0a132bc1829fae70224ef8ca01523bae947` |

## Remaining gates

Independent UI source review and both registrations are complete. Obtain a NEW
named execution window. Format/analyze the changed Dart files and execute the authored
unit/inspector regressions. Rebuild the current native library and exercise all
actual-FFI tests. Finally bind source/runtime/package bytes and run exhaustive
catalog, native API and separate product UI acceptance on the actual OHOS target.
No original/all-product requirement is closed by this source review.
