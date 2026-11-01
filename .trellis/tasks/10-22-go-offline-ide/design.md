# Go offline IDE design

Read parent `design.md`, `research/official-sources.md` and native runtime/entry/terminal specs. Keep new profile hooks optional to avoid breaking independent apps.

Expose pure parse/format entry points from the native Go module using standard `go/parser`, `go/token`, `go/scanner`, `go/ast` and `go/format`. Input is current UTF-8 source plus file identity; output owns error ranges, formatted text and AST summaries. Correctly map native byte/line/column positions into Dart UTF-16 offsets. Audit any Yaegi compile/type-check path for imported-source initialization before using it for safe analysis. Unit tests assert edited code cannot create a marker file during analysis.

Bridge existing `interp.Debugger` using a thread-safe session registry and explicit native memory ownership. Event callbacks produce bounded immutable records rather than calling Flutter from Go threads. Dart polls or receives platform-safe events, validates session identity and renders paused state. Continue/step/breakpoint/terminate operations are typed commands. Session stop is idempotent, handles cancel-before-registration and survives errors/panics. Preserve the existing projectSourceFS and entry selection.

Go tools contribute a direct `ToolsGrid` section via `toolsTabBuilder`, with per-tool forms/actions and selected project context; do not wrap them in another product-features page. Reuse real SDK resolution and terminal command semantics for desktop operations while preventing dependency resolution from using the network in offline products.

Ship FFI ABI changes and Android/OHOS rebuilds together. Native tests plus Dart mocks cover errors, range mapping, stale-buffer handling, session lifecycle and actual native debugger stepping. Final target integration exercises shipped symbols and GUI interactions.
