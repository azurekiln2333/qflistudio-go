# Technical design

## Boundaries and ownership

The product repositories remain separate. C coordinator is the sole common-core owner for learning chips/badges, highlighting, explorer/workspaces and analyzer/panels (global channel seq77/79). `qfli_studio_core` owns those shared models and rendering/profile contracts. Each product owns real runtime analysis/debug adapters, language tools, content authoring/verification and native packaging. Content authors stage slices and the core integrator applies them after digest checks. Go does not edit common core paths. No worker overwrites aggregate content wholesale or commits other agents' changes.

Go coordinator owns `qfli_go/lib`, `native/go_runtime`, `tool/go_curriculum`, Go tests and Go packaging when explicitly required. Existing dirty OHOS branding/signing files are recorded as baseline and not automatically staged. C/C++ and Python requirements are integrated using their current coordinators' verified deliverables, not implemented in parallel from Go.

## Learning-content execution

Inventory actual tutorial/example catalog IDs and every runnable code block, including edited example versus tutorial variants, declared supporting files, stdin, expected output and required modules. Record content/source hashes and the packaged runtime revision. Baseline checks come before publishing new content. The official-Go verifier remains a compiler check; a second harness calls the shipped `runGo` path. Device integration must load the actual OHOS library through the app bridge and execute the same inventory, recording every result and failure. A missing target remains an open execution gate while host repairs proceed.

Keep existing IDs and learning topics. Where Yaegi fails on a valid topic, decide from concrete failure whether to fix the runtime or rewrite the runnable exercise to teach that concept on the shipped backend without losing substance. Do not pass by filtering failures, marking everything desktop-only, or asserting only successful process launch. Nondeterministic examples need semantic assertions and bounded execution. Unsafe-to-run examples need sandboxed fixtures and explicit supported behavior rather than accidental host side effects.

New Go topics have canonical source/support files and paired explanatory content. Target 160 additions spanning practical standard-library data processing, files, parsing, collections, algorithms, concurrency, testing-support utilities and offline applications; final topics must fit the proven runtime, not a copied desktop-only syllabus. Source and aggregates must remain reproducible. Only authorized Go slices enter shared assets, preserving every other language's bytes/content.

## Common IDE contracts

Propose typed immutable diagnostics with project/file identity, buffer revision, severity, message, code and source ranges. Analysis is debounceable and cancellable; stale results cannot decorate a changed buffer. Parse/type-check does not run edited user code. Providers advertise capabilities per runtime/platform and return a clear unsupported state rather than fabricated success.

Problems, Output, Debug Console and Terminal share a bottom-panel selector but retain independent data/lifecycle. Diagnostics select the correct owning root and file/range. Output is bounded and labeled by run/tool; cancellation and log clearing remain distinct. Debugger operations require real backend pause/step/resume semantics. Ports show actual locally owned listeners when introspection is available, with no automatic forwarding or exposure.

Workspace persistence stores a versioned workspace ID/name and ordered project-root references, not widget-local state. Root/file owner identity follows tabs, run commands, diagnostics, history and file actions. Expansion state is restored on first construction and switching, captured against the original root before asynchronous work, and resilient to stale/missing directories. Migration preserves existing single-project sessions.

Language chips are derived from visible profile/catalog languages and compose with search/level filters. Use the existing project language badge component where available. Tools have individual first-level cards/actions with product-specific implementations and contextual project selection. Highlight modes and extension aliases are tested for actual token spans in all supported languages, including headers and embedded HTML/CSS/JavaScript.

## Go adapters

Desktop analysis/tools use the existing official SDK selector and local project environment; package operations must disable network resolution. Mobile analysis may require exposing non-executing Go parser/type-check/gofmt support from the existing native Go library. Inspect the vendored interpreter's interfaces before defining a C ABI. Never call `runGo` as a syntax checker because it executes program side effects. New native exports require rebuilt OHOS/Android libraries, matching Dart FFI ownership and error handling, and native tests before packaging.

Useful direct Go tools should perform real formatting, AST/symbol navigation, import/module inspection, test-output parsing, code analysis and structured-data conversion where the embedded backend supports them. `go build/test/vet` remain honest official-SDK capabilities unless a real mobile implementation is supplied.

The vendored Yaegi version includes `interp.Debugger`, real line/function breakpoint requests, pause/continue/step/terminate, frames, scopes and variables. Bridge these through an ID-owned session registry with bounded event polling and deterministic stop/free. Validate multi-file compilation and imported-package initialization first; a debugger must operate on the same project/source view as normal runs. Parser/formatter support can use standard-library packages already compiled in the native module, with UTF-8 offsets mapped correctly to Dart UTF-16 editor ranges.

## Compatibility, failure recovery and rollout

Keep new profile hooks optional for existing products, preserving current constructors and terminal delegates. Gate new runtime hooks by availability. Save content backups/digests before the one shared apply. Split conventional commits by shared contract, Go runtime/adapters and validated curriculum. Revert only task-owned changes; never reset dirty worktrees. Push normal commits to configured remotes and verify remote SHA; record authentication/non-fast-forward failures without force.

## Current risks

No connected OHOS target is present. Native research subagents currently cannot authenticate due to an upstream 403 balance error; default Pi configuration may also be unavailable. These do not justify narrowing scope. Official web research must produce actual retrieved source text before recording claims. Full completion still needs every language's fresh device matrix and cross-product regression evidence.
