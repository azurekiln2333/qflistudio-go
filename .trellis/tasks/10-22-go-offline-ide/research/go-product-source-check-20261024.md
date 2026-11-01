# Go product callback and workspace source check

Date: 2026-10-24, Asia/Shanghai. Reviewer: `go_product_check_1024`.
Active task: `10-22-go-curriculum-ohos`; debugger dependency:
`10-22-go-offline-ide`.

This is an independent source review, not an executable quality-gate pass.
Go236 remains released at seq287, reaffirmed at seq414. No Go, gofmt, Dart,
Flutter, SDK, test, analyzer, native build, WSL or device command ran. No live
runtime handle or resource reservation was inherited or created.

## Findings (fixed)

### Missing real callback ABI regression

- File: `test/go_studio_debugger_test.dart`.
- Issue: the new callback metadata/label/boundary tests all used fake backend
  records. Existing actual-FFI tests exercised ordinary main-function stepping
  and could not detect a mismatch in the new callback wire contract or real
  callback owner IDs.
- Fix: added `real shared adapter controls an opaque native callback and retains
  its boundary`, gated by the existing `QFLI_GO_RUNTIME_LIBRARY` artifact
  selection. A real `sync.Pool.New` callback pauses before printing, reports a
  live logical callback owner distinct from main, exposes one source frame and
  the exact native unavailable-locals reason, steps through the shared adapter
  using that owner ID, resumes, prints the expected output, retains the boundary
  notice after owner exit, and verifies the native session registry is released.
- The case is authored but UNRUN. Its skip without an explicit current rebuilt
  artifact is not acceptance. It must run with the final DLL, and separate
  actual OHOS evidence is still required.

No production source-contract defect or definite local field/API error was
found in this bounded source review. No production or workspace-test change
was needed. The implementers' handoffs remain historical source snapshots;
the adapter test hash below supersedes its earlier value.

## Source paths reviewed

Read the active task check manifest, PRD/design/implementation plan, debugger
dependency artifacts and relevant frontend/native/entry/curriculum/cross-layer
specs. Review followed these concrete paths:

- Native `debugger.go` thread/event/frame JSON fields into `GoDebugThread`,
  `GoDebugEvent` and `GoDebugFrame`, then native snapshot history, shared
  `DebugSnapshot`, and the standalone debugger page.
- Shared `debug_session.dart` command/token/immutable snapshot contracts and
  Go adapter serialization, pause generations, source validation, output bounds,
  cleanup and terminal-state publication.
- Real `goProfile`, default-enabled `supportsSavedWorkspaces`, independent Home
  workspace/cloud gates and explorer named-save action. The current capability
  is present; the older absent-capability finding must not drive skipped tests.
- Workspace dialog/store/session JSON, saved-card resolution, retained host,
  editor restore, file owner/cursor assignment and each root's tree restoration.
  Named-session restoration bypasses legacy project history as intended;
  standalone Go legacy restoration remains independently covered.
- All eight active workspace cases and the fourth-local-scope/no-cloud update
  in the existing offline profile test. The tests use the actual product
  identity, public shared APIs and real temporary files. Queued writes drain
  before fixture deletion while the fake zone and real IO are both advanced.

## Contract observations

- Missing kind/boundary fields preserve older payloads. Present malformed values
  fail decoding before replacing the accepted snapshot.
- A kind label alone does not fabricate an opaque boundary or suppress scalar
  locals. Boundary metadata and the exact native unavailable reason are consumed
  independently.
- Shared command IDs retain the native numeric execution owner. Kind-only label
  updates change snapshot revision while preserving the current pause token.
- Retained event history stays immutable and bounded after an owner exits; the
  stopped-event fallback preserves callback kind. The product synthesizes no
  external caller frames or physical goroutine identity.
- The native reviewer's later generic-retained-argument provenance repair does
  not change the additive schema. Timers and other uncertain callbacks can now
  correctly use the same `nativeCallback` rendering. No product allowlist or
  special handling was introduced.
- Workspace tests separately exercise actual Home/save entry, rename/removal,
  disk/card/editor reopening, ordered owners and cursors, sidebar/page
  reconstruction, legacy history and missing-member behavior. Model-only
  construction is not presented as the entire entry acceptance.

## Findings (not fixed)

### Actual target IDE acceptance source was missing at inspection

`integration_test/go_native_test.dart` contains five actual runtime paths:
multi-file execution, panic handling, Run cancellation, terminal execution and
terminal interrupt. `go_catalog_test.dart` covers the full corpus and offline
host URL/agreement refusals. Neither contained actual analyzer/formatter nor
debugger break-before-side-effect, step, continue and termination acceptance.
The ordinary actual-FFI tests in `test/` are selected by the desktop artifact
environment variable; their existence is not OHOS evidence.

This was reported to root with the exact source locations. Integration-test
files are outside this review's edit ownership; root is assigning the target
acceptance source separately. This finding does not claim anything about later
edits by that owner.

### Historical shared workspace specification observation

The workspace implementer's handoff records that the shared saved-workspace
scope documentation predates the new optional standalone capability. C/main
own that shared specification and publication checkpoint. No shared source or
spec was edited here. Dirty source capability presence alone does not prove
that the owner's publication candidate includes it.

This initial observation is superseded by the same-ID follow-up below: the
current shared saved-workspace and offline-workspace specifications now state
the optional standalone capability and propagation contract.

### Executable and target gates remain open

Formatting, analysis, actual widget scheduling, native callback behavior,
rebuilt-library ABI integration, full affected suites, real package execution
and OHOS interaction remain unverified. Source checks do not supersede native
handle85731 exit1 or broaden the successful historical SDK checks.

## Verification

- Source whitespace/merge-marker/final-newline scan: all eight reviewed Go Dart
  files clean. This was a read-only Python scan of complete files, not a Dart
  parser or test runner.
- Scoped `git diff --check`: exit0; existing LF-to-CRLF notice for the tracked
  offline-profile file. The other reviewed files are untracked, so the full-file
  scan above supplies their whitespace evidence.
- Lint: not run; waiting for a NEW explicit named grant.
- TypeCheck: not run; same resource constraint.
- Tests: not run; same resource constraint. All new callback and workspace cases
  remain UNRUN.
- No shared-core mutation, process kill/reset, build, install, staging, commit or
  push was performed.

After a new grant, format/analyze these eight Dart files, execute the three
debugger test files and the two workspace/offline test files serially, and run
the real callback ABI case with the final rebuilt DLL. Preserve exact handles,
terminal exits, logs, skips and before/after source identities. Root owns the
full native/SDK/shared/product/target gates beyond this bounded review.

## Reviewed Go source identities

| File | SHA-256 |
| --- | --- |
| `lib/go_debugger.dart` | `59510744f044d9d791280eb2f66ddd3881e7ee21cd056101eee63c74af0c1284` |
| `lib/go_studio_debugger.dart` | `d2db8f005b95c73cbbe666526927f094747aed46aed8a3ecaa45b69e2cdb4a46` |
| `lib/go_debugger_page.dart` | `8929909f3f5ac136302060df417a917d87e49470f66388d3fdcaa9f7b8dad7ca` |
| `test/go_debugger_test.dart` | `0c220de8cbf0982ab47ba7c645573b2d24bed2f57cc3a084596038fef0d4c2fa` |
| `test/go_studio_debugger_test.dart` | `5fd9f182c18ccb5cd59f9d74c971269e4201e8fbf21389e6f0616f919dfdd5c8` |
| `test/go_debugger_page_test.dart` | `38c4f105b6624c6f72d67798531384749c931779035dacf0eda3f7b8e1b44703` |
| `test/go_saved_workspaces_test.dart` | `33d2ebe1860b03d184f4a8bb463348436bc91c8f0e0789fbc1fa52ac1f8eac8b` |
| `test/go_offline_profile_test.dart` | `408c82044ebd373184646d8f42ac0b5bab7f48c520c44552dcc9fe14aad987ec` |

Reviewed shared debugger contract SHA-256:
`1a4bd5d1cb83906b7d8d1c9404f2d5c7aec54a9ee2ea556a93dcc633a80ff81b`.
Shared workspace dependency hashes matched the implementer's thirteen-file
handoff on the initial read. Native sources remain under active independent
repair, so no native source freeze or tested digest is asserted here.

## Same-ID workspace follow-up

The implementer subsequently added three active actual-Go widget cases, bringing
the file to eleven registered cases with no skips. Review used test snapshot
`8bc09493a32ccd864320ad4617e2f1ca41388a7a2a9da706072914cd7f756345`
and the handoff's same-ID addendum, then inspected the current shared source.
The initial research prose/final-hash race is explicitly corrected in
`same-id-workspace-propagation-source-audit-20261024.md`. Its final hashes already
include the owner's repairs and are not evidence of still-broken ID-only gates.

### Review and local fix

The cases physically mount the real retained host or the same keyed editor
page, then exercise `attachWorkspace`, incoming same-ID widget metadata, or the
explorer settings save callback. Assertions cover mounted titles and subsequent
settings values; retained keys, page/tree/controller/open-file identities;
current primary and ordered roots; the retained restore label; the dirty
secondary buffer and its changed cursor; and live nested expansion created
after initial restoration. The second case passes an older session only as
incoming widget data and never writes that copy to the store, correctly
isolating metadata refresh from stale-session restore.

The shared source now refreshes page and explorer metadata references for a
changed same-ID object, retains the tree on metadata-only changes, captures live
expansion before member/primary reordering, and notifies the retained owner for
same-ID settings saves. `attachWorkspace` accepts changed metadata independently
of ID/path equality. No shared edit or current source-derived propagation
failure was found in this bounded review.

One local test-coverage omission was fixed in `expectLiveBuffers`: the clean
primary file now explicitly remains non-dirty and retains both extent endpoints
as well as its base cursor endpoints. All three new cases consume this helper.
The resulting current workspace-test hash is the `33d2ebe...` value in the
source table above. All eleven cases remain authored and UNRUN.

### Current dependency snapshot

| Shared path under `../qfli_studio_core/` | SHA-256 |
| --- | --- |
| `lib/editor/editor_page.dart` | `8549c7e4d00692c27876636d436811100a231d04cb842f263d50eaaab7c07ca4` |
| `lib/editor/file_explorer.dart` | `6b99ad68a789e2a20d4f49f54ccbf9fa193e9eca852e34a8976bf0b13353a661` |
| `lib/editor/retained_editor_host.dart` | `58d91921b177173842222f1d2aecb1261f73633abe3a8fefeb4ae33f27e8ba78` |
| `lib/workspace/workspace_store.dart` | `1c1cd747f3b3c66b92399aa92a6f61703774a6e1754423ca61acf222a9fecf8d` |
| `lib/workspace/workspace_dialogs.dart` | `a947571b26fb23f513221e2955a5e81123beb0931d4031cd2ce2c3c424c00481` |
| `lib/editor/retained_editor_restore_control.dart` | `071f76e9931caa33f1641b867d9b10a0783b06b6865fbc85d0a3e3d703e87aae` |
| `.trellis/spec/frontend/saved-workspaces.md` | `4595cba6f1d7190003185bb1960c27fb362e0ee9b6fed8f6f838d50b166b700c` |
| `.trellis/spec/frontend/offline-workspace.md` | `47a27c88229e62472ad4e6b272b3d110d94d87aa0a4039f1d23e895730fd373a` |

The two shared specifications now describe standalone named workspaces and
same-ID propagation explicitly, superseding the initial documentation finding.
These are current source identities, not a publication freeze or runtime pass.
The workspace tests and this report passed a complete-file lightweight
whitespace/final-newline scan. Formatting, lint, type-check and runtime execution
remain unrun under the released host slot. Root owns the later named grant and
the coherent shared-publication/product/target gates.
