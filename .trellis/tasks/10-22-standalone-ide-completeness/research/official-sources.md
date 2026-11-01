# Official tool research (retrieved 2026-10-22)

The browser search API returned no usable content. The following official pages were fetched directly over HTTPS with HTTP 200; `official-source-fetch.json` records URLs and response lengths. This is developer research; it does not introduce network use into any standalone app.

## VS Code workspace and debugger

- https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces
- https://code.visualstudio.com/docs/debugtest/debugging

The workspace Explorer displays multiple root folders; a saved workspace file holds folder references and workspace settings. Individual folders can retain their own settings. Apply this as persisted root references and correct file ownership rather than a project-switch menu pretending to be a multi-root workspace.

Debugger UI is backed by a language debugger: breakpoints, stack/variables, execution controls and Debug Console output/evaluation. Provide controls only when the runtime implements the corresponding operation, and test real paused execution. Remote debugging and port forwarding are outside the offline scope.

## Go syntax and formatting

- https://pkg.go.dev/go/parser
- https://pkg.go.dev/go/format

`parser.ParseFile` accepts in-memory source and produces an AST/errors; `AllErrors` collects additional syntax diagnostics and `SkipObjectResolution` avoids deprecated identifier resolution. Syntax parsing is distinct from type analysis. `format.Source` provides Go formatting and returns syntax/I/O errors. These standard-library packages can be compiled into the existing native Go runtime without fetching external services.

Source-backed feasibility: vendored `interp/program.go` exposes `Compile`, `CompilePath` and `CompileAST` separately from execution. Imported-source initialization must still be audited before promising side-effect-free type checking. Vendored `interp/debugger.go` already includes real Debug/Continue/Step/Interrupt/Terminate, line/function breakpoints, frames and variables. The Go debugger is therefore an implementation target, not assumed infeasible; it requires new session/FFI integration and tests.

## Python local packages

- https://pip.pypa.io/en/stable/cli/pip_install/

pip supports installation from local find-links locations with index lookup disabled using `--no-index`. This does not prove pip exists in the embedded Python build or that a desktop binary wheel works on OHOS. The Python coordinator must verify the bundled interpreter/modules, choose supported pure-Python or target-built packages, and enforce local-only resolution. Do not expose ordinary online pip installation in the standalone product.

## CLion inspections

- https://www.jetbrains.com/help/clion/code-inspection.html

CLion documents code inspections and severity profiles. Apply the useful interaction: ranges and severities in the editor plus actionable inspection results. Do not imitate unsupported compilation/debug features with static status cards.
