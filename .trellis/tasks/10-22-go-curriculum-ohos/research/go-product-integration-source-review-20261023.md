# Go product integration source review

Date: 2026-10-23, Asia/Shanghai. This records current source observations for
R3/R4/R6/R7, following the original attachment and active task artifacts. It is
not a new widget, native, package or target pass. The corpus agent reported the
workspace finding before its account-concurrency failure; root inspected the
concrete source and completed this report. No shared source was edited.

The companion JSON records ten exact source snapshots. They are review inputs,
not a shared-core freeze. Main/C continue to own shared workspace and editor
integration. Go236 remains released at global seq287; no new Go, Dart, Flutter,
build, WSL or device command was run for this review.

## R3: content filters and badges

`lib/main.dart` registers `GoContentRepository`. That repository preserves the
typed `ContentFilter` for tutorial/example queries and rejects non-Go entries
from its Go-owned bundled catalogs.

Shared `local_content_pages.dart` applies the same selection to tutorial and
example rows, composes language/level/query criteria, and derives chip choices
from actual visible catalog languages. `_ContentTitle` uses `LanguageBadge` on
list rows and both example/lesson detail app bars. `language_badge.dart` keeps
`c` distinct from normalized `c++`/`cpp`. This establishes source wiring; it
does not establish current mixed-language rendering, combined-filter behavior,
small-screen layout or actual target navigation. Those shared/product gates
remain open after the current shared checkpoint.

## R4: individual first-level tools

The approved design calls for individual first-level cards/actions in
`ToolsGrid`, without another language-features hub. The Go profile registers
`GoToolsTab` directly through `toolsTabBuilder`, supplying the real native tool
backend. The section exposes formatting, imports/symbols, local module checks,
JSON-to-struct conversion and the individual debugger entry. Each builder opens
that tool's working form; there is no additional product-features collection.
Project selection uses the product store and updates browsed ownership.

The current tests cover first-level card interaction, project changes, stale
source-result rejection, output/error behavior and narrow/large-text layouts.
The earlier controlled 13-case offline/profile/repository/tool checkpoint is
historical evidence recorded in the umbrella ledger. No test was rerun here.

## R6: named-workspace entry is absent for Go

This is a confirmed source gap, rather than a reported runtime reproduction:

- Go sets `productKey: StudioProductCatalog.goShiftKey` in `lib/main.dart`.
- Shared `saved_workspace.dart:14-17` makes `isMainStudioRelease` true only for
  a null profile or the main product.
- Shared `home_page.dart:326-336` therefore omits the workspace tab for Go.
- Shared `editor/file_explorer.dart:325-328` routes Go's manage action to the
  legacy multi-root picker when there is no existing saved workspace.

The legacy picker and `ProjectHistory` still preserve multi-root selection and
tree expansion. They do not prove the named workspace save/reopen/CRUD flow
required by the parent design. Go312 reported the gap to main/C; JSON317
confirmed the same distinction for its child profile; C320 explicitly accepted
this OPEN umbrella gap and retained common ownership. Go has not changed its
product key or edited shared core to bypass the guard.

After the owner publishes supported standalone entry, update the Go offline
Home regression: it currently asserts exactly three offline scopes. The added
local workspace scope must remain independent of cloud/account/network policy.
Verify persisted session/root ownership, missing roots, sidebar recreation,
rename/remove and reopen in the actual child profile and on the target. Do not
replace these checks with a main-profile workspace pass.

## R7: registered debugger, native follow-up still open

The Go profile registers `GoStudioDebugger`, and the individual debugger tool
is connected to the actual product backend. Its shared adapter and standalone
form must continue to consume current native snapshots and real command IDs.

The independent native review found opaque retained callbacks can inherit an
exited lexical debug routine. See dependency research
`native-epoch-source-review-20261023.md`. Native and product owners are now
implementing labeled logical callback execution ownership and explicit opaque
stack boundaries, preserving proven direct synchronous caller identity and
panic semantics. No new run establishes that behavior yet. Current native,
real FFI, latest shared panels, target debugger and actual local-port acceptance
remain open. The previous native85731 exit1 remains retained evidence.

All 160 draft topics remain unpromoted pending original OHOS acceptance. The
existing static corpus handoff is cited without rerunning its completed checks.
No implementation commit, push, package build or device ownership change was
made by this review.
