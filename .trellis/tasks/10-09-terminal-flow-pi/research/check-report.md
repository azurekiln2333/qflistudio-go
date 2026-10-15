# Check report: selected-entry Go execution

Date: 2026-10-09
Reviewer: trellis-check
Status: source and focused quality gates passed; source/test files frozen and handed back to the main session.

## Reviewed scope

Reviewed this task's delta against HEAD in lib/go_runner.dart, lib/go_entry_selector.dart, both native Go bridge files, native/go_runtime/runtime.go and runtime_test.go, test/go_entry_selector_test.dart, test/go_toolchain_test.dart, test/go_app_test.dart, and integration_test/go_native_test.dart. Loaded the full saved Trellis hook context, task artifacts, current local entry/terminal/runtime specs, and Pi's audit/implementation report. Shared core and pre-existing startup changes remained outside this review's write scope.

## Findings (fixed)

1. **Selected file identity and Go filename rules**
   - Files: lib/go_entry_selector.dart; native/go_runtime/runtime.go; selector/toolchain/native tests.
   - The desktop and native scanners excluded the selected main when its Windows path used different casing. The desktop scanner also treated other_TEST.go as a test even though Go builds that filename.
   - Desktop now compares paths with package:path semantics, and native respects Windows case-insensitive entry names. Go source/test extension checks retain their case-sensitive spelling.
   - Reproduced failing Windows cases before fixing; real SDK and interpreter regressions now pass.

2. **Symlink main sources and source decoding**
   - Files: lib/go_entry_selector.dart; test/go_entry_selector_test.dart; test/go_toolchain_test.dart.
   - Directory listing used followLinks:false and skipped Link entities, so a symlink main was not excluded. It could cause duplicate mains or become an unintended helper-entry fallback.
   - Regular-file symlink sources are now scanned. The real SDK proves regular entry, symlink entry, and helper rejection in the same directory. Windows symlink tests ran successfully without skips.
   - Discovery tolerates invalid UTF-8 without modifying source bytes; Go still diagnoses retained sources. A platform-excluded source with invalid UTF-8 no longer fails during discovery. Retained helper encoding errors still reach the compiler.
   - The lexer also accepts Go's permitted leading BOM; a failing unit regression was reproduced and fixed.

3. **Native success when the selected main was excluded**
   - Files: native/go_runtime/runtime.go and runtime_test.go.
   - Reproduced empty success for _selected.go, .selected.go, selected_test.go, a different-GOOS filename, and a legacy +build-excluded selected file when helpers remained.
   - After normal package evaluation, the runtime imports the already cached package using a Go-quoted path and resolves its main function reference. A missing main returns exit 1 with an entry/build diagnostic. This uses Yaegi's existing build view and does not call main again.
   - Tests prove init and main each execute once, including a Unicode/space directory. A disposable real-interpreter probe also proves a user global named qfliRunEntry does not conflict with the internal import alias.

4. **Malformed competing entry policy was inconsistent**
   - Files: native/go_runtime/runtime.go; lib/go_entry_selector.dart comments; native/toolchain tests.
   - Desktop already excluded an identifiable unfinished competing main, but native discarded all partial AST facts on any parse error.
   - Per the main session's explicit review decision, native retains recoverable AST declaration facts for non-selected sources. Selected syntax errors still take precedence, and retained helpers keep real parser/type diagnostics.
   - Real desktop and native tests now agree on an unfinished competing main body. Corrected the misleading claim that every malformed competing source stays in the compiler view.

5. **Preparation diagnostics and exit classification**
   - Files: native/go_runtime/runtime.go; lib/go_runner.dart; native/toolchain tests.
   - The native output-finalization defer overwrote the directory-read error returned directly in Stderr. The desktop directory-read failure used the unavailable-runtime sentinel.
   - Native writes that diagnostic into the synchronized stderr buffer. Desktop run preparation filesystem failures return exit 1 with the concise run title; missing SDK startup still returns the existing not-run sentinel.
   - Added directory-read and runner preparation regressions.

6. **Acceptance coverage gaps**
   - Files: test/go_toolchain_test.dart; integration_test/go_native_test.dart.
   - Added the missing final main run to the device main -> main2 -> main sequence.
   - Desktop assertions now cover exact titles, unchanged source/config bytes, meaningful platform exclusion, real helper/malformed-source diagnostics, ordinary six-tool behavior, and package build still reporting duplicate-main errors.
   - Cancellation and missing-SDK tests now have an actual competing entry, exercising overlay cleanup rather than only the plain command path.

## Findings (not fixed)

- **Bounded malformed-source recovery difference (accepted design limit):** the Dart lexer and go/parser do not promise identical recovery after arbitrary syntax corruption. A disposable probe with `package main unexpected\nfunc main() {}\n` confirms that the lexer recognizes the later main while Go's partial AST stops at the malformed package header. Such an unselected file can be excluded on desktop and remain a diagnostic on native. The main session explicitly chose a small lexer plus partial AST detection instead of a full Dart parser; no broader parser was added. Selected files and retained helpers continue to use real compiler/parser diagnostics.
- No other outstanding task-scope source defect was found.
- Native binary rebuilds, final full-suite checks, platform installation, and Apple execution evidence are owned by the main session. This reviewer did not run devices or build binaries. At handoff, the main session reported the full Flutter suite at 68/68 and Android device integration at 3/3 after rebuilding the libraries; OHOS verification was still in progress.

## Verification

- **Lint:** pass. `flutter analyze --no-pub` reported no issues; `go vet -mod=vendor ./...` was clean.
- **TypeCheck:** pass through Flutter analysis and native Go compilation/tests.
- **Formatting:** Dart formatter and gofmt completed successfully. Narrow `git diff --check` passed.
- **Focused Flutter tests:** 45 passed in selector, toolchain and app tests, with QFLI_GO_TEST_EXECUTABLE pointing to the installed Go 1.27.1 SDK.
- **Native tests:** `go test -mod=vendor -count=1 ./...` passed, including existing cancellation, main/worker panic, os.Exit and concurrent-output tests.
- **Overlay lifecycle observation:** qfli_go_overlay_* directory count was 0 before and 0 after the focused suite, which included success, missing-SDK process-start failure, and cancellation.
- Verification used process-local GOMAXPROCS=2, GOFLAGS=-p=1 and (native Windows checks) CGO_ENABLED=0.
- Disposable evidence is under .artifacts/terminal-flow-pi/check/. No repository reset, sibling edit, vendor edit or commit was performed.

## Handoff

Native runtime source was frozen after test/vet and released to Pi for rebuilding. Dart source/tests were frozen after the 45-test SDK run and analysis; the main session may continue final build/device work. Main owns local spec synchronization; its current entry-selection spec already records casing, partial AST handling, excluded-entry failure and diagnostic preservation. Also retain the symlink-source and loss-tolerant-discovery cases in the contract.
