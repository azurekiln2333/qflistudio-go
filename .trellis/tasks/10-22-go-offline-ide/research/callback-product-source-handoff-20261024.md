# Callback product source handoff — 2026-10-24

Owner: `/root/callback_finish_1024`. Active task: `10-22-go-curriculum-ohos`;
debugger dependency: `10-22-go-offline-ide`.

Status: source implementation and source review complete; executable validation
is pending a later named grant. No source changes will follow this handoff
without review feedback.

## Released execution slot

Go236 remains RELEASED at the existing global sequence 287. Historical native
handle 85731 exited 1. Historical SDK handles 21711 and final SDK handle 70405
both exited 0. These ancestor records predate this source change and are not
fresh validation of the hashes below. This agent inherited no live handle and
started no Go, gofmt, Dart, Flutter, analyze, test, build, SDK, WSL or device
command. No process kill or reset was performed. C owns the independent
zero-live-process check before the Rust205 then C211 handoff.

## Files changed

- `lib/go_debugger.dart`: typed execution kind and event/frame boundary metadata,
  strict additive decoding and shared execution labels.
- `lib/go_studio_debugger.dart`: callback thread names, stopped-event kind
  fallback, boundary/local-unavailable information, retained boundary console
  notices, and thread names in the full-snapshot revision fingerprint.
- `lib/go_debugger_page.dart`: callback identity in paused state and history,
  explicit external-caller boundary details, and native unavailable-local reasons.
- `test/go_debugger_test.dart`: decoder compatibility, malformed metadata and
  callback-history regressions.
- `test/go_studio_debugger_test.dart`: adapter identity, fallback, boundary and
  metadata-only revision regressions.
- `test/go_debugger_page_test.dart`: visible callback/boundary/history regressions.
- This handoff document.

The six Dart files were already untracked task files before this worker's edits.
No files were staged or committed. Shared core, sibling code, native source,
binary artifacts, catalog content and build inputs were not edited by this worker.

## Compatibility and lifecycle invariants

Native owner `/root/native_finish_1024` confirmed threads/events accept optional
`kind: "goroutine" | "nativeCallback"`; events/frames accept optional
`opaqueNativeBoundary: bool`.

- Missing kind defaults to `GoDebugExecutionKind.goroutine`; missing boundary
  defaults to false. Existing const constructor call sites retain these defaults.
- Present unknown kinds and malformed metadata types, including explicit null,
  throw `FormatException`. Existing unrelated payload decoding is unchanged.
- Kind alone never infers an opaque boundary or hides valid scalar locals.
  Native callbacks are labeled `Native callback <id>` rather than physical
  goroutines. The existing `goroutineId` wire key and numeric command IDs remain.
- The older stopped-event fallback carries kind when the native thread list is
  absent. Event/frame metadata survives the existing immutable, bounded history
  after a callback execution owner disappears.
- Shared frames preserve the native unavailable reason. A missing reason at an
  explicit opaque boundary gets an explanatory fallback. Shared console and
  standalone history state that the external caller stack is unavailable; no
  parent frames are synthesized.
- The native owner's intended opaque-locals reason is exactly:
  `Opaque native callback may capture values outside this stack; locals were not read`.
- Thread name changes increase snapshot revision without changing an otherwise
  valid pause token. Existing command serialization, stale-token rejection,
  polling, source-path checks and real termination/cleanup waiting are preserved.

## Added regression names

`test/go_debugger_test.dart`:

- `legacy debugger payloads default execution metadata`
- `callback metadata decodes without assuming an opaque boundary`
- `execution metadata rejects unknown kinds and malformed types`
- `callback history retains metadata after its live owner exits`

`test/go_studio_debugger_test.dart`:

- `callback owners keep native command IDs and explicit locals reasons`
- `stopped-event fallback preserves callback kind and opaque boundary`
- `frame boundary alone explains unavailable callback locals`
- `kind-only updates publish labels without inventing a boundary`

`test/go_debugger_page_test.dart`:

- `callback labels and native boundary details survive in event history`
- `frame metadata explains unavailable callback locals`

These are source regressions awaiting execution, not passing-test claims.

## Source checks performed

- Manual review of all changed production sections, new cases and fake backend
  changes, including command numeric IDs, event-history retention and boundary
  flags independent of kind.
- `git diff --check --` for the six paths: exit 0. Because these paths are
  untracked, this alone does not validate their file contents.
- A Python read-only UTF-8/source whitespace scan covered all six full files:
  zero trailing-whitespace lines, zero merge-marker lines, and final newlines
  present in each. The same read computed the exact SHA256 values below.
- No formatter, analyzer, compiler, test runner, native runtime or device check
  was executed by this worker.

## Exact source hashes

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `lib/go_debugger.dart` | 15299 | `59510744f044d9d791280eb2f66ddd3881e7ee21cd056101eee63c74af0c1284` |
| `lib/go_studio_debugger.dart` | 18759 | `d2db8f005b95c73cbbe666526927f094747aed46aed8a3ecaa45b69e2cdb4a46` |
| `lib/go_debugger_page.dart` | 15360 | `8929909f3f5ac136302060df417a917d87e49470f66388d3fdcaa9f7b8dad7ca` |
| `test/go_debugger_test.dart` | 13281 | `0c220de8cbf0982ab47ba7c645573b2d24bed2f57cc3a084596038fef0d4c2fa` |
| `test/go_studio_debugger_test.dart` | 20347 | `84fa2ad406670e1c41bafcfccbc5313ef71a9dbc9193dbc7e8f4f6e84ef7727e` |
| `test/go_debugger_page_test.dart` | 12843 | `38c4f105b6624c6f72d67798531384749c931779035dacf0eda3f7b8e1b44703` |

## Unexecuted gates and remaining concerns

A later named grant must permit formatting/analyzer checks and the focused
Flutter suite for the three touched test files. Rebuilt-library FFI tests must
then exercise the real native callback lifecycle together with the native
owner's focused, full-module, vet and real race checks. Current binaries and
previous green SDK records cannot validate this source. Full affected product
checks and packaged OHOS execution remain acceptance gates in the parent tasks.

There is no known remaining Dart source-contract issue from this manual review.
Syntax, formatting, asynchronous widget behavior and actual ABI/native lifecycle
behavior remain unverified until the corresponding executable checks run.
Shared core has no dedicated boundary field, so this implementation conveys that
information through existing console and unavailable-local fields.
