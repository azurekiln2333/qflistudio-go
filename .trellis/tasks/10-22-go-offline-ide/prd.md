# Complete Go offline IDE adapters and direct tools

## Goal

Implement Go's real offline diagnostics, debugger and useful tools as part of parent R4/R5/R7/R10, connecting optional coordinated shared contracts. Respect the parent full scope and offline constraint.

## Requirements and acceptance

- Analyze unsaved Go source without executing initializers, main, goroutines or file/network side effects. Return real source ranges/severities and reject stale results in the editor. Syntax validation must work on OHOS with no installed SDK.
- Offer real Go formatting, symbol/import inspection and useful project-aware tool actions directly in the Tools tab. Use current project ownership; report actual errors. Official-SDK-only operations remain clearly capability-based until implemented on mobile.
- Expose Yaegi's actual debugger sessions, line breakpoints, pause/step/continue/stop, stack and variables. Prove execution stops before a marked side effect, stepping changes position and termination releases the session.
- Integrate Problems/Output/Debug Console/Terminal and actual local-port capabilities through the shared owner's APIs; keep buffers bounded and outputs attributable to sessions/tools.
- Native, Dart FFI, tool/widget and lifecycle tests pass; changed native exports are present in rebuilt OHOS libraries and exercised on the target.

## Dependencies and exclusions

Shared-core owner publishes the optional diagnostic/debug/panel profile contracts before adapter integration. This child owns only Go product/native files and tests. Native standard-library parser/formatter and vendored debugger are available for implementation research. Never analyze by calling the executable runGo path; never advertise fake SDK/debug actions. No online package/tool download or port forwarding. Cross-product highlighting/workspaces and other language providers belong to their declared owners and integration child.
