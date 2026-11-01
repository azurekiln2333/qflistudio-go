# Go IDE execution plan

1. After approval/start, load relevant backend/native/entry and frontend/terminal contracts, inspect current sources and publish the Go file boundary.
2. Coordinate shared diagnostic/debug profile models before their use. Implement and test native pure parser/formatter/AST results first, including invalid Unicode/UTF-16 ranges and side-effect-free analysis.
3. Add Go Dart adapters, update FFI ownership and integrate current unsaved-buffer diagnostics, format actions and direct tool sections. Test valid/invalid sources, source revisions, project ownership and error display.
4. Implement real Yaegi debug session registry and event/command bridge. Native tests prove breakpoint, stack/variables, step, continue and terminate behavior; add Dart lifecycle/widget integration tests.
5. Connect shared panel actions and supported local ports. Verify logs remain bounded and Terminal cancellation semantics remain intact.
6. Run native tests/vet, Go analyze/full tests with real SDK enabled, shared contract regression suites and rebuilt native ABI/package inspections. Then test actual OHOS FFI/diagnostics/debug/tool behavior on a real target.
7. Update executable specs and hand audited changes to the root for conventional commits/push. Parent ledger remains open for unrelated requirements.

Dependencies: shared models before step 3/4 integration; new Go native exports before bundled-library rebuild; device execution after a real target is detected. Parent `implement.md` contains exact baseline build/test commands and rollback rules.
