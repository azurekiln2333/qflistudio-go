# Requirement evidence ledger

Updated 2026-10-24 (Asia/Shanghai). The original request in source-request.txt remains authoritative across every standalone product. Implementation is active; the previous planning-only ledger was stale. No row closes the umbrella.

| Requirement | Current evidence | Remaining acceptance |
| --- | --- | --- |
| R1 every OHOS example | Original 120 topics produce 364 operations: 120 tutorial imports, 120 example imports, 120 canonical samples and 4 support tests. Go curriculum research/catalog-official-import-baseline.json: 364/364. Fresh catalog-native-neutral-cwd.json: 364/364, no inventory/coverage issues, deviceExecution=false, without process CWD presets. Native source hash dc2a647dc6d03d69e5e32befcb4411db3b637a09d533f6b2e91e4c9f439af9c1. Test metadata proves test/benchmark/fuzz execution. Historical failed reports preserved. | Repeat hash-bound audit after subsequent runtime fixes; rebuild libraries and execute all originals through packaged OHOS FFI. Host pass does not prove target execution. |
| R2 substantially more than 100 additions | All T121–T280 are authored: 160 distinct drafts. Each 80-topic owner snapshot assembles 240 operations with zero inventory issues; combined original+draft 280-topic substantive dedup passes. Bundled assets retain original120. | Fresh full-range official/native execution after final runtime fixes; earlier grouped passes predate corrected draft hashes. Publish only after original OHOS baseline passes, then verify expanded corpus on OHOS. |
| R3 chips/circles | Current shared source contains language/query/level filters and reusable circular LanguageBadge, including distinct C/C++. Go ContentRepository preserves filters/fixtures; 2 tests passed. Actual content import/render tests completed17 cases in the latest combined run. | Retest latest shared tree/final catalogs, mixed-language filters, detail badges, narrow and large-text layouts. Product-specific evidence is required. |
| R4 direct tools | GoToolsTab embeds format, imports/symbols, local module/vendor/replacement checks, JSON-to-struct and debugger cards directly in ToolsGrid. Native parser/formatter adapters are real. Fixed lazy-viewport offline assertion; subsequent controlled root run passed all10 offline-profile cases plus2repository+1tools-adapter cases (13/13). Official capability research is recorded. | Final current-tree full tests, actual target tools and visual checks. Earlier OOM is retained as a failed run; later13/13 is a distinct successful checkpoint. |
| R5 diagnostics/highlighting | GoCodeAnalyzer/native parser report current-source syntax errors with UTF-16 ranges. Native and actual Windows FFI parser/formatter tests passed at their checkpoints. Profile registers analyzer. Common diagnostics/Problems/highlighting belong to C. | Rebuild final runtime, rerun real FFI, verify editor waves/navigation on target. Syntax parsing is not semantic/type checking. |
| R6 workspace/tree | Current shared HEAD2f9039a3 publishes default-enabled standalone named-workspace entry and same-ID metadata refresh. Read-only Git comparison found no worktree differences from that commit in the ten inspected profile/Home/page/explorer/retained/store/dialog/spec paths. C reports69core+actual JSON1 PASS and12file analysis clean; those are C/JSON checkpoints. Go has11 active real-profile source cases, including retained dirty-buffer/cursor/tree preservation. | Execute current Go workspace tests and product/target persistence, sidebar recreation, ownership and reopen acceptance. Other-product passes do not prove Go behavior. No Go shared edits. |
| R7 panels/debug/logs/ports | Genuine native debugger supports breakpoints, steps, stack/locals and bounded output. Product GoStudioDebugger is registered in profile. Intermediate actual Windows FFI27/27 predates the latest native repairs. Independent native source review is complete at61c25dceaa6d7dd067410c32a493378bfef82ab9686345902b79ae2d883f68e7, with provenance/Helper/snapshot/native-alias repairs and new regressions authored. | All current native code remains uncompiled/unexecuted after85731 exit1. Run full native/vet/race, rebuild and repeat real FFI, then actual target debugger/panel interactions. Source review does not close runtime correctness. Ports require actual supported local services. |
| R8 C/C++ headers | C owns requirement. Read code-analysis-20261022.md and code-analysis-package-evidence.json: real dedicated Clang/bridge checks include nested local headers, mixed sources and link diagnostics; prior222Flutter/31native checks remain scoped checkpoints. Seq223 says original200/200 native+LLVM/WASI are host-only; current signedARM64 HAP starts1ab90015. | Current owning-app OHOS local-header/multi-file execution and final delivery. No matching x64 package/device proof is established by the ARM64 package inspection. |
| R9 Python modules | Python owns requirement. Read module-review.md and ohos-audit-build-ready.json: ten bundled modules (base64, bisect, contextlib, copy, csv, functools, itertools, statistics, string, textwrap), versioned local package install/update/remove and import regressions. Signedx64 audit HAPd1387df9 includes exact asset/native-strip binding. | Actual installed OHOS module/package/import and full original corpus execution, final debugger/editor and expanded corpus. This is local compatible pure-Python installation; no online pip or arbitrary native-extension support. |
| R10 offline/integration/commits | Go isOffline=true and tools local. SDK children use no-proxy/no-checksum/no-toolchain-download settings and the actual Go telemetry-child suppression marker. Both SDK paths consume shared ProcessSupervisor and buffer early output. Actual Windows late-subscription and nested-child Run/terminal-run/terminal-test regressions passed (2tests), scoped3file analysis clean in Go236 window. OHOS native host now rejects agreement/external URL methods; actual channel target test remains unexecuted. Build provenance and exact SDK-strip binding have11/11isolated tool checks. No implementation commits/pushes yet. | Native focused85731 exit1 remains open (debug initializer plus3Helper method forms); repair and repeat full native/Dart/shared/SDK gates, final source-bound ABI/package and target execution, independent check/spec update, selective conventional commits and verified normal pushes. Shared macOS descendant cleanup and actual Xcode/macOS builds remain open. Preserve unrelated dirty signing/branding/plugin files. |

## Current source-review follow-up

R6 has a confirmed standalone entry gap beyond the older persistence checks.
Go's profile uses `goShiftKey`, while shared `isMainStudioRelease` admits only
the main product/null profile. `home_page.dart:326-336` therefore omits the
named-workspace tab for Go, and `editor/file_explorer.dart:325-328` routes its
manage action to the legacy multi-root picker. Existing `ProjectHistory`
persistence does not establish the named save/reopen/CRUD flow. Global Go312
reported this, JSON317 confirmed the same distinction, and C320 accepted it as
an OPEN umbrella gap under main/C ownership. No child product-key bypass or
shared edit was made by Go. Final Go offline/widget tests must cover the
supported workspace entry after that checkpoint; the current three-scope
assertion must not be mistaken for named-workspace acceptance.

R7/native review also found opaque native callbacks selecting their lexical
debugger routine, including one already removed from the live registry. The
source-only report `10-22-go-offline-ide/research/native-epoch-source-review-20261023.md`
records the deterministic worker-created/main-invoked Pool callback scenario.
The approved repair assigns unknown-provenance entries labeled logical callback
execution owners and stops stacks at the opaque native boundary; it preserves
known direct synchronous caller identity and panic semantics. Promoted native
method-expression receiver handling is also under repair. These findings,
their new regressions and all later runtime/package/target gates remain OPEN;
source review is not a replacement for the retained native85731 exit1.

### 2026-10-24 source continuation

The preceding R6 absence finding is historical. The current shared worktree now
has default-enabled `StudioProfile.supportsSavedWorkspaces`, its separate
workspace helper, and Home/explorer entry gates. The real offline `goProfile`
inherits that capability without a product-key override. The Go source handoff
`10-22-go-curriculum-ohos/research/go-saved-workspace-source-handoff-20261024.md`
binds the exact inspected dependency bytes and eight active acceptance cases:
actual Home/save entry, rename/remove, disk/card/editor reopen with ordered
owners/cursors/expansion, separate legacy restoration, missing primary, missing
secondary and all-missing refusal. The offline scope assertion now requires four
local scopes and no cloud. These tests are authored, not executed; a separate
Trellis source check is in progress. C421 also distinguishes the dirty Home
dependency from its frozen publication candidate. Neither source presence nor
another product's test establishes Go or published-core acceptance.

The Dart callback metadata integration is also source-complete and awaiting an
executable check. Independent product source review is recorded in
`10-22-go-offline-ide/research/go-product-source-check-20261024.md`; it added an
actual callback-ABI regression, still unexecuted. The implementation handoff is
`10-22-go-offline-ide/research/callback-product-source-handoff-20261024.md`.
It adds honest logical callback labels, explicit opaque boundaries and retained
event history, preserving command IDs and legacy payload defaults. Native N1
ownership/stack repairs and promoted method expressions are still being
finalized. All new formatting, analysis, native, Dart/FFI and target gates remain
unexecuted. The retained native85731 exit1 has not been superseded by a pass.

Go236 remains released at seq287; exact SDK handle70405/shellPID64664 exit0,
earlier SDK21711 exit0 and native85731 exit1 were reconfirmed at seq414. No new
Go/SDK/Dart/Flutter/build/WSL command is permitted until a later explicit named
grant. Source-only work holds no host reservation. No full objective completion
is claimed.

The Go workspace source suite now has eleven active cases after adding three
mounted/retained same-ID metadata regressions. The owner repaired the shared
metadata gates and updated shared workspace specs; exact current dependency
hashes are in the workspace handoff's addendum. The separate same-ID audit now
explicitly corrects its non-atomic historical prose/later hash capture. No
executed failure or pass is attributed to those repaired hashes, and queued
store writes already preserve current metadata.

Independent native source review subsequently proved that a generic native
stack marker cannot establish retained-argument caller identity, and found a
locals count/read entry race plus autonomous native reply-pointer exposure
(`net/rpc.Client.Go`). These repairs and substantive source regressions are
being completed; passing historical corpus/SDK results do not close them.
Target acceptance source is also being extended: the prior native integration
harness lacked actual analyzer/formatter/debugger API checks. This does not
replace the separate target editor decoration, tools and panel UI gates.

### Current source and publication checkpoint, 2026-10-24

The previous goal turn only reconfirmed the already-recorded release; it added
no executable acceptance evidence. The current continuation reread the original
request and started independent review of concrete new source rather than
repeating the release as implementation progress.

The native review is now handed back in
`10-22-go-offline-ide/research/native-source-check-20261024.md`. Its exact current
digest is the R7 value above. No known concrete finding was intentionally left
unrepaired within that review scope, but formatting, compilation, full tests,
vet and real race execution are all UNRUN. The sticky native mutable-alias
unavailability reason is a conservative limit, not native heap introspection or
a general race-safety guarantee.

The target helper `integration_test/go_native_ide_acceptance.dart` now registers
five real bundled-FFI operation IDs in both integration entrypoints:
`analyze-unsaved-utf16`, `format-and-inspect`,
`shared-debug-break-step-continue`, `opaque-native-callback`, and
`debug-stop-close-reopen`. Its handoff is
`10-22-go-curriculum-ohos/research/go-target-ide-acceptance-source-handoff-20261024.md`.
It binds runtime identity and cleanup evidence, but all five cases are UNRUN.
Independent source review is now complete in
`10-22-go-curriculum-ohos/research/go-target-ide-acceptance-source-check-20261024.md`.
The separate `integration_test/go_product_ui_acceptance.dart` is also authored
and independently reviewed. Its four operation IDs cover editor waves/Problems,
gutter/debug panels, direct tools with real projects, and named multi-root
sidebar retention. Both entrypoints now chain predecessor cleanup, API cleanup
and UI acceptance. Review fixed a completed-analysis-failure cleanup hold while
retaining HOLD for watchdog/unknown states. All Dart format/type/lint/test,
actual FFI, screenshot and target execution gates remain UNRUN for this source.
Source review and registered widget assertions do not prove rendered behavior.

Shared capability publication is no longer merely a dirty-worktree dependency:
read-only Git inspection confirms current core HEAD
`2f9039a3ba95449679b17257b0313c1ee3644a2c`, titled
`feat(workspace): enable standalone named sessions and refresh retained metadata`.
The ten inspected shared paths match that commit. C487/488 report terminal,
empty owned Jobs,69/69 core tests, actual jsonProfile1/1 and clean12file analysis;
C493 reports all four normal remote main refs verified at that OID. Root verified
the local commit/source comparison only; neither owner checkpoints nor local
source identity establish Go widget or OHOS acceptance. Go450's earlier
same-ID source finding is superseded by these repairs.

Global Go485 reconfirms historical Go236 release, final SDK70405/PID64664 exit0,
earlier SDK21711 exit0 and native85731 exit1. There is no Go host reservation.
A source-only future-window runner is under review: source work must stay
bounded, and an unconfirmed cleanup observation must retain the same owned
handles and publish HOLD until actual terminal/empty confirmation. No new
Go/gofmt/SDK/Dart/Flutter/test/analyze/build/WSL/device command has been authorized
by this source continuation.

### Latest host coordination and reviewed UI source

The later named handoff is separate from historical Go236. Root explicitly
deferred Lua531 to C at global534; C536 accepted its short retry and C537
published exact terminal/empty-Job release back to NEW Go509, then Web510.
After the interrupted continuation, Go explicitly DEFERRED Go509 at global545
to ready Web510, followed by Note511. That deferral was globally published and
directed to C, Web and Note. Go509 was never accepted or executed. There is no
Go heavy process handle, Job or reservation to release; later Go execution
requires another explicit named grant. The source-only runner controls remain
UNRUN. Do not replay Go236, Rust205 or C211 from the historical chain.

The final reviewed UI helper SHA-256 is
`97c313836f111d196c7882048e8c2a689ab7b17165c7570ff3037dae7bdeecfd`.
Its full source-review report records all seven reviewed identities and the
concrete lifecycle repairs. Python AST/text inspection and scoped whitespace
checks passed; these are source checks only. No runtime or target gate was
closed in this continuation.

## Cross-product handoffs

Owner reports below are evidence leads, not umbrella completion. Global Trellis channel qfli-core-release-sync is the durable source. C remains sole common-core owner; current shared tree is actively dirty and Go has made no common-core edits.

- Java: prior280topics/1120target operations and16real JDI checks; seq164 starts new common adapter. New editor integration has a separate target gate.
- Lua/Script: seq153 repairedLua480/480native and signedx64 audit readiness. Complete JS/TS/Shell location audit/follow-up package remain open.
- SQL: seq157 original126entries/372locations; signedx64 hash0c5007b468e3e525d687b4e52983865b4c84d6ad2a89dd006aaf83bd8df76d78. Full target execution/expansion remain open.
- Python: seq159 original306 embedded units and Python-only aggregate generation preserving non-Python fingerprints. OHOS execution and expansion are separate gates.
- Rust: reservation128/secondary-root report147 retained; obtain final corpus/runtime/product handoff.
- Web: seq163 actual native474/481 with7 failures. Host481/481 does not replace target failures; normal-home relaunch after disconnection was not proven.
- JSON: read owner final-handoff.md/family-audit-20261023.md, durable docs commit8f4d8e3 and product6df694e. Captured x64 snapshot proves340Runner locations,16worker defaults and recorded ordinary UI; host116/116. Product has no configured remote. Later shared-core integration requires a fresh matching package/UI pass; physicalARM64 and signing remain separate.
- Dart/Note/other standalone apps: retain owners and obtain fresh explicit handoffs. No absence of errors counts as completion.

The newer read-only Dart/Note/SQL reconciliation is retained in
`research/dart-note-sql-evidence-20261024.md`, with exact artifact paths and
SHA-256 identities. It supersedes stale evidence leads above where specified:
Note's exact-core2f9039a named-workspace1/1 and full285/285 passed, but its
captured analysis/Android phases failed and the gate remains incomplete. Dart's
original240 portable host pass and authored180-topic expansion do not establish
installed OHOS acceptance; lesson273 passes unchanged and later package
signature plus profile are verified. SQL's original SQLite360 host pass excludes
the unverified12 MySQL scripts; its corrected unexecuted legacy history fixture
does not establish named-workspace consumption. No product is marked complete.

## Device coordination

Web explicitly released exact target127.0.0.1:5555 in seq163. Queue Lua121 -> SQL122 -> Python124 -> Rust128 -> later-ready Go/Dart. Handoff reported the exact target disconnected; an emulator process or old listing is not current availability. Go has not accepted a device window or installed/launched an app in this task. Prepare matching signed audit package before explicit handoff. PhysicalARM64 and x86_64 emulator proofs remain separate.

## Completion rule

Every original requirement remains in scope. Old reports, declarations, filtered manifests, host-only tests, builds or app launch alone cannot close target/all-product acceptance. Inspect exact content/native/package hashes, full operation coverage, outputs and cleanup. Continue independent implementation while device windows are queued. Do not complete the goal from Go host baseline.
