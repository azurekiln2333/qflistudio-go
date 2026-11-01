# Go target IDE acceptance source handoff

Date: 2026-10-24, Asia/Shanghai.
Owner: `go_target_ide_acceptance_1024`.
Active task: `10-22-go-curriculum-ohos`; native IDE dependency:
`10-22-go-offline-ide`.

This is authored source and bounded manual review only. Every new target
operation below is **UNRUN**, and the Dart changes remain unformatted. No
Go, gofmt, Dart, Flutter, SDK, test, analyzer, native build, WSL, hdc, device,
kill/reset, staging, commit or push command was started by this continuation.
Python inspected source syntax/whitespace/hashes only; it did not execute the
inspector, fixture suite or any embedded Go code.

## Resource release and exact historical handles

Read-only global `qfli-core-release-sync` records identify the original release
at seq287, `2026-10-23T02:35:25.396Z`, and confirmation at seq414,
`2026-10-23T22:52:04.805Z`:

- Final SDK nested-cancel/scoped-analysis handle **70405 / shell PID 64664**:
  **EXIT 0**, nested-cancel **1/1 PASS**, analysis **No issues**.
- Earlier SDK delayed-output handle **21711**: **EXIT 0**, **1/1 PASS**.
- Native handle **85731**: **EXIT 1**, retained failure evidence.
- **Go236 remains RELEASED**, with no live Go handle or reservation inherited
  or created here. Its historical successor was Rust205, then C211. This
  confirmation grants no later slot and does not change the current queue.
  C owns zero-process verification; this worker issued no kill/reset.

The exact handles/release were reported directly to the parent. Source work
does not supersede the failed native attempt or broaden either successful SDK
regression result.

## Change boundary

The gap was missing actual bundled-runtime IDE API acceptance in the existing
target entrypoints. Added one helper test and minimal registrations plus the
debug-kernel marker requirement. Existing catalog/native execution cases and
the offline-host audit remain in place. No shared core, product adapter,
native runtime, bundled binary, build script, catalog or device configuration
was edited by this worker.

| File | Change |
| --- | --- |
| `integration_test/go_native_ide_acceptance.dart` | New five-operation actual-FFI audit, runtime identity and session cleanup ownership. |
| `integration_test/go_native_test.dart` | Preserve the binding and register the new helper last. |
| `integration_test/go_catalog_test.dart` | Register the same helper last with mandatory embedded backend and the existing `_loadedRuntime` reader. |
| `tool/inspect_go_catalog_hap.py` | Require `QFLI_GO_NATIVE_IDE_AUDIT` in the packaged debug kernel. |
| `.trellis/tasks/10-22-go-offline-ide/research/fixtures/inspector_binding_review.py` | Include that marker in its explicitly synthetic ZIP fixture. |

## Required operation contracts

All five IDs must appear exactly once and pass, all leases must release, and
runtime identity must be available before the final report can succeed.

| Operation ID | Authored target assertions |
| --- | --- |
| `analyze-unsaved-utf16` | Real `GoCodeAnalyzer` receives an unsaved CRLF/Unicode document differing from disk. The illegal `💥` range spans exactly two UTF-16 units. A newer valid revision is clean; initializer/main marker remains absent; saved bytes remain unchanged. |
| `format-and-inspect` | Actual `createGoIdeTools()` formatter returns the exact standard formatting, inspector reports alias/type/method, malformed source returns genuine errors, and disk source stays untouched. |
| `shared-debug-break-step-continue` | Actual `GoStudioDebugger` pauses at line 5 before a marker write, exposes scalar 42, steps to line 6 with scalar 43, resumes using the newly observed pause token/thread ID, prints `43`, writes the marker, terminates and releases the native registry entry. |
| `opaque-native-callback` | Actual `GoDebugger` pauses inside compiled `sync.Pool.New` callback dispatch. Logical callback owner differs from main and exposes nativeCallback kind, opaque boundary, one source frame and the exact unavailable-locals reason. Step/continue produce expected output and preserve boundary metadata after owner exit. |
| `debug-stop-close-reopen` | A private loopback HTTP fixture holds a real compiled `http.Get`. Close remains pending and nonterminal until the fixture releases the response. Then actual terminal/registry release is required before a fresh session starts and prints its expected output. |

These direct API assertions do not establish editor decorations, Problems
rendering, tool-card interaction, Debug-panel rendering or full product UI
acceptance. The independent ordinary actual-FFI callback test remains separate.

## Runtime identity and reporting

- `QFLI_GO_NATIVE_IDE_AUDIT` publishes JSON and merges `goNativeIdeAudit` into
  the existing `binding.reportData`; it does not replace catalog/offline-host
  report entries. A temporary JSON report also records its own path.
- Records contain case outcomes, partial evidence on failure, source hashes,
  snapshots, session IDs, cleanup observations and process working-directory
  invariance. Required cases skipped after a cleanup failure are `not-run`.
- Ordinary host native tests skip the new embedded audit explicitly. The
  catalog registration requires the embedded backend and cannot silently
  substitute desktop SDK execution.
- The catalog helper reuses `_loadedRuntime` unchanged: `/proc/self/maps`
  identifies the actually loaded library path and its bytes are hashed. The
  ordinary native runner uses the equivalent reader by default.
- iOS identifies the resolved application executable containing the static
  runtime, with evidence label `target-api-statically-linked-app-container`.
  It does not claim an independent loaded-SO digest on iOS.
- Runtime identity is read after source-tool operations load FFI and again
  after debugger operations; missing identity or path/hash drift prevents
  success. This does not replace source-bound package/build provenance.

## Cleanup ownership

Each successfully returned raw/shared session is tracked. Raw sessions close,
require actual terminal state, verify the native registry rejects polling,
then dispose. Shared sessions dispose, await `done`, require terminal state,
and verify the same native registry release.

A 15-second close observation timeout publishes the exact pending session ID
and then waits on the **same** close future. It starts no subsequent case while
that future is pending and does not fabricate terminal state. A cleanup error
retains its fixture and blocks all later operations. Fixture-directory/root
deletion failures now remain visible in the report instead of bypassing final
publication. The HTTP fixture releases its own held response before outer
session cleanup waits; it never resets a runtime/process.

Initial temporary-root creation can fail before this helper can publish its
structured report; no native operation/session has started at that point.
The integration runner still observes the thrown preflight failure. The test
harness's four-minute timeout remains an observation limit, never release
evidence for a still-pending native close.

## Bounded source verification

- Manual inspection checked current analyzer/tools/debug/shared snapshot APIs,
  actual callback fixture shape and installed Dart IO interfaces.
- Corrected the shared-step continuation to use the stepped snapshot's thread
  ID, because its pause generation changes while native owner suffix remains
  stable. Both owner IDs are retained as evidence.
- Python `ast.parse`: both changed Python files parsed successfully; no
  bytecode, subprocess, test or SDK invocation was made by this inspection.
- Full-file UTF-8/final-newline/merge-marker/trailing-whitespace inspection:
  all five source files clean.
- Scoped `git diff --check`: exit 0. Git reports the existing LF-to-CRLF
  conversion notice for the tracked native test; untracked files are covered
  by the full-file inspection above.
- Dart formatting, parsing, type checking, lint, target integration, all new
  debugger/source assertions and inspector fixture execution: **UNRUN**.

## Exact source snapshot

Hashes are SHA-256 of the inspected bytes, not a publication freeze. Other
workers' files and previous edits in the touched entrypoints were preserved.

| Source path | SHA-256 |
| --- | --- |
| `integration_test/go_native_test.dart` | `af05a83ba4eadf3cce11dc6ff385a1eeb0ba9426d1391fefc557f3f3a04105d3` |
| `integration_test/go_catalog_test.dart` | `f53348d4078b1a8937f892c1853d9e838de9ce84ef7be0eb6df178185210ff78` |
| `integration_test/go_native_ide_acceptance.dart` | `e4c8981da779e9f0c094dd50926a1c4e6dd591ae6a68deea4c05cb5babfc5e1d` |
| `tool/inspect_go_catalog_hap.py` | `19377bbf9f6498f7fcbdaa1f0f561604842e0f781593efdb9df6dad20246da36` |
| `.trellis/tasks/10-22-go-offline-ide/research/fixtures/inspector_binding_review.py` | `c76a0b686f381e437ca1bc8ac1dc3721b82a152f25be553c7542bd61d712b990` |

## Remaining gates

Parent-owned independent source review is next. A NEW explicit named grant is
required for formatting/analysis/host-native/SDK execution; no readiness or
grant is inferred from this source handoff. Then exercise current rebuilt
native artifacts, all affected regressions and the updated inspector fixture
before claiming executable acceptance. Finally build/source-bind the actual
package and execute these APIs on the actual target, followed by separate
editor/tools/panel interaction evidence. No target acceptance gate is closed
by this handoff.
