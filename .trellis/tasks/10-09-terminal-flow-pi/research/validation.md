> Historical evidence from 2026-10-09 only. Current implementation and commits were completed under 10-15-release-integrity-audit; there is no pending commit-approval request. Current test/build/device outcomes are recorded in that parent's research/release-validation.md. In particular, this file's old signed-HAP/device results do not establish current OHOS signing or device success.
# Final verification evidence

Date: 2026-10-09. Implementation and validation are complete; Git commit confirmation is the remaining workflow step.

## Shared Java / Go terminal

Go and Java both consume ../qfli_studio_core. The Java-session terminal/editor changes are already shared: a top-aligned continuous transcript, prompt after the last output line, no successful-run/exit-zero banner, and tap versus long-press entry dispatch. This task did not modify shared core or Java.

From qfli_go, the shared terminal_pane_test.dart and editor_run_test.dart suites passed: **22 tests**. Coverage includes scrolling, stream/session ownership, quiet success, real diagnostics, history, cancellation, save-before-run and tap/hold/tap selection.

The real TerminalPane render harness passed **5 cases**, each opened and visually inspected: desktop-dark, phone-dark, phone-light, short-viewport, phone-long-path. Output and prompt form one scrollback with no fixed lower input form. Fixtures exist only in research tests, not product data. Images are in research/screenshots/.

## Go source and independent review

Pi in the right Herdr pane w8:p2 implemented selected-entry execution and concise go run <basename> titles. The independent trellis-check reviewer fixed the concrete boundary cases recorded in check-report.md, then froze source/tests before the final builds.

Desktop keeps go run . and a temporary standard Go overlay only when competing main sources exist. Helpers, modules, imports, embed assets and build rules remain compiler-owned. Native uses go/parser plus a selected-directory source view. A cached-package main reference verifies that Yaegi actually included an entry, without invoking main or init again. Source files and entry metadata are not rewritten.

Final results:

| Check | Result |
| --- | --- |
| Full Flutter suite, real Go 1.27.1 SDK enabled, concurrency 1 | **68 passed**, 0 failures |
| Independent focused Flutter suite | **45 passed**, including actual Windows symlink tests |
| flutter analyze --no-pub | No issues |
| Native go test -mod=vendor -count=1 ./... | Passed |
| Native go vet -mod=vendor ./... | Passed |
| Dart formatting, gofmt, scoped git diff --check | Passed |
| Overlay leftovers after success / start failure / cancellation | 0 |

The SDK cases cover main -> main2 -> main with two main declarations, helper, module subpackage, embed resource and platform exclusion. They also check selected helper rejection, syntax/UTF-8 diagnostics, filename casing, symlinks, unchanged source/config bytes, normal package tools and cancellation with an actual overlay.

Native cases cover the same entry sequence and helpers/imports, malformed selected and retained helper diagnostics, identifiable unfinished competitors, ignored filenames/GOOS/build constraints, main/worker panic, os.Exit, cancellation, concurrent output, and init/main each running once. An internal-alias collision probe also passed.

Full-suite log: .artifacts/terminal-flow-pi/full-flutter-test.log. Independent review: research/check-report.md.

## Fresh mobile libraries and packages

Pi rebuilt all five libraries using tool/build_go_runtime.ps1 and the existing Windows Go 1.27.1, pinned OHOS Go 1.27.1 port, Android NDK 28.2.13676358 and OpenHarmony SDK. Build passed in 180.2 seconds. All five library hashes changed from the old baseline; generated C headers are byte-identical, preserving QfliGoRun/QfliGoCancel/QfliGoFree.

- Android arm64-v8a, armeabi-v7a, x86_64: correct ELF machine/class and every PT_LOAD aligned to 0x4000 (16 KB).
- OHOS arm64-v8a and x86_64: correct ELF machine/class.
- Final APK: all three runtime members are byte-identical to the new libraries. zipalign -c -P 16 4 also passed.
- Final signed HAP: both runtime members have all 31 allocated sections identical to the new libraries. HAP stripping changes only non-allocated sections and whole-file hashes.

Both normal application builds passed:

| Artifact | SHA256 |
| --- | --- |
| build/app/outputs/flutter-apk/app-debug.apk | 290E491C076A9E4A57E6643113A2E4FD42B7C254C96E797A4CB506EC233014E0 |
| build/ohos/hap/entry-default-signed.hap | 08A5994557E178F275762E7DB36E2DD7DA788ECE1A1D74FCFB58917B9F98185F |

Details: research/native-build-report.md and research/native-package-report.md. The verifier is research/native_artifacts_verify.py. It fails missing declared archives, wrong ABI/alignment and stale loaded code/data.

## Real devices

Command on each device: flutter test --no-pub -d <id> integration_test/go_native_test.dart --reporter expanded.

| Device | Result |
| --- | --- |
| OPD2413, Android 16 / API 36, arm64; adb-d361e7a0-gqqQSM._adb-tls-connect._tcp | **3 passed** |
| OpenHarmony 7.0.0.105 / API 26, arm64; 192.168.68.207:46551 | **3 passed** |

Both devices executed actual main -> main2 -> main output through FFI, then rejected a helper selected as entry. Program/worker panics, os.Exit and cancellation passed. The shared editor gesture tests separately prove tap/hold/tap forwards those exact entries without changing configuration.

After testing, rebuilt normal lib/main.dart APK/HAP, installed with replacement while preserving data, and launched the normal app on both devices. Android normal launch returned PID 20812; OHOS normal launch returned PID 50257. Neither device was left running the integration-test entry.

Logs under .artifacts/terminal-flow-pi/: android-native-test.log, ohos-native-test.log, android-normal-build.log, ohos-normal-build.log, android-normal-install.log, ohos-normal-install.log, android-zip-alignment.txt.

## Limits and preserved work

- Apple build/device execution was not available on this Windows host. The existing iOS Xcode phase consumes the updated source; no iOS success is claimed.
- The small Dart lexer and go/parser may recover differently after arbitrary malformed package syntax. This accepted design boundary is documented in check-report.md; selected sources and retained helpers retain real compiler/parser diagnostics.
- All 10 pre-existing source/config files in research/preserved-file-hashes.json remained unchanged at the final preservation check. Startup, content-import, unrelated tool state and sibling work are excluded from the prepared commit.
- Local Go entry-selection and editor-terminal specs were updated; .trellis/spec/ is deliberately ignored by this repository and is not force-added.
- No Git commit or push has been made. Proposed work and bookkeeping commits are in commit-plan.md, awaiting the single confirmation required by workflow Phase 3.4.
