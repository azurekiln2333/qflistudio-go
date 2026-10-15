# Design

## Boundaries

The shared editor already selects the project entry on tap and the active file on long press. Its terminal already renders a continuous transcript. Keep ../qfli_studio_core read-only; no ProgramRunner API or Java changes. Correct Go execution after the existing entryFile handoff.

Pi owns Go production code and focused tests. Codex owns task/spec documents, visual verification, review and narrow integration. Existing dirty changes and other active language sessions must be preserved.

## Selected-entry execution

- The selected source must be a Go main-package file declaring a top-level main function. Running an ordinary helper must fail visibly rather than launch a different file.
- Ignore competing entry declarations only within the selected source directory. Retain every normal helper, imported subpackage, build constraint and project-relative asset. Do not edit, rename or rewrite user source or entry metadata.
- Desktop: retain the original go run . package execution. If competing main files exist, use Go's standard -overlay JSON Replace map with those absolute paths mapped to an empty string, so the compiler excludes them from its build view. Keep ordinary packages on the existing command without an overlay.
- A small Dart lexer detects actual top-level package/main declarations while skipping comments, string/rune/raw literals and method receivers. Add focused lexical edge cases; do not rely on a column-zero regular expression.
- The overlay is a per-run temporary artifact. Do not expose its path in the terminal. Retain it until the child process exits, including cancellation, then clean up only that owned directory. Preparation failures also release it.
- Native: use go/parser AST declarations and a filtered projectSourceFS directory view for the entry directory. Keep Yaegi's normal package evaluation, imported directories, C ABI, cancellation and panic recovery intact. No vendored interpreter API changes.
- Compilation/parser errors remain diagnostics. Do not suppress user output or hide failures behind a fallback to main.

## Presentation

Use a short go run <selected basename> title for Go runs, with no runtime implementation suffix or Chinese run banner. Existing shared terminal code owns quiet success, nonzero status and prompt continuity.

## Compatibility

Keep build, test, fmt, vet and mod tidy package semantics unchanged. Existing Go SDK prerequisite and embedded-runtime limitations stay accurate. Rebuild Android and OHOS runtime libraries after native source changes. The iOS build phase consumes the changed source, but Windows cannot establish an Xcode/device result.

## Verification and rollback

Prove main / main2 / main with both entries present and a shared helper; use real SDK and interpreter output. Check module imports, build constraints, lexical false positives, no-main rejection, ordinary project behavior and cancellation. Run the shared widget tests and inspect the actual widget renders from the Go dependency context.

Review only this session's delta. Go runner/runtime files were clean at task start; main.dart, native startup and shared-core files were already dirty. Roll back only task-owned changes if required, never reset repositories.
