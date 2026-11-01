# Complete offline standalone IDEs and verify every OHOS example

## Goal

Fulfil the complete attached Chinese request across the standalone language products. Make the apps useful offline IDEs, with teaching code that really runs on their current OHOS toolchains. This task coordinates Go deliverables and cross-product acceptance; other live product coordinators retain their own repositories. Finishing Go alone does not finish the user goal.

The source of truth is `C:/Users/lichengyu/.codex/attachments/8486130d-e230-4931-8cb3-866e3cf3aa11/pasted-text-1.txt`. The user authorizes Trellis planning, implementation, up to four Pi collaborators, conventional commits, and normal pushes when available. The latest runtime workflow instruction still requires review of the completed plan before `task.py start`.

## Confirmed facts

- `qfli_go` is a separate Git repository on `fix/go-release-integrity`, depending on sibling `qfli_studio_core` by path. Other language product repositories are siblings too.
- Initial shared-core worktree is clean. Product worktrees contain pre-existing changes, including OHOS signing/icons/configuration; preserve and distinguish them from this task.
- Go has 120 topics, each with a tutorial and an example (240 catalog code blocks). Only 3 topic pairs differ in code. There are 87 single-file topics, 15 module projects and 18 test packages. Existing documentation explicitly limits all topics to desktop official-Go verification; the mobile runtime is vendored Yaegi through FFI, not an official Go compiler.
- Shared `FileExplorer.initState` rebuilds the root without calling `_restoreExpanded`; the restoration exists only on project switching. A regression must exercise sidebar disposal/recreation.
- Shared highlighting currently registers C, C++, CSS, Dart, Java, JavaScript, JSON, Kotlin, Markdown and XML; Go/Lua/Rust/SQL need inspection and real token checks.
- Other product coordinators have created tasks for this same request on 2026-10-22. Coordinate ownership through global `qfli-core-release-sync` before shared changes.
- `hdc list targets` currently reports `[Empty]`; an OHOS build or host interpreter result cannot prove device execution.
- Three native research agents failed with HTTP 403 insufficient balance. Existing Go Pi panes have been located in live workspace `w1V`, independently of stale inherited `HERDR_*` IDs.
- All four existing Go Pi research prompts subsequently failed with `model_not_available` for their configured `deepseek-v4.1-flash`. No agent report or claimed passing check is inferred from those terminal completions.

## Requirements and acceptance

| ID | Required behavior | Evidence needed |
| --- | --- | --- |
| R1 | Audit every existing example and executable tutorial code block for every standalone language on the actual current OHOS packaged runtime; repair unsupported code/runtime behavior rather than silently hiding failing content. | Complete item inventory, hashes, exact backend/build identity, assertions and per-item OHOS execution reports with zero unexplained omissions. Desktop/host/build evidence is separate. |
| R2 | Add substantially more than 100 meaningful, distinct runnable examples after baseline validation; increase further where useful. Go delivery target: 160 additions, alongside all existing lessons. | Distinct curriculum map, explanations, expected results, runnable source/support files, dedup review, host and OHOS passing reports for all new items. No cosmetic constant/title variants counted as distinct additions. |
| R3 | Examples and tutorials in multi-language apps have language filter chips that combine with existing search/level filters. Show language circles beside list/detail titles consistently with project lists; C and C++ remain distinct. | Real catalog/widget tests for C/C++, combined filters and title badges, including narrow screen/large text. |
| R4 | Useful language-specific offline tools appear directly on the Tools page, contextual to language/project. Remove generic dedicated-feature detours. Research official VS Code/JetBrains/language tools. | Flat tools-page interaction tests and real tool outputs; current-project selection; official-source research and capability map. |
| R5 | Editor shows real syntax/type diagnostics with file/line/column, wave underlines, explanation and Problems navigation. Improve editing and verify highlighting for every supported language. | Non-executing analysis providers, invalid/valid/unsaved-buffer tests, obsolete-result rejection, rendered underlines and location-navigation regressions. |
| R6 | Reopening the sidebar preserves expanded folders, including project switches. Support persisted workspaces containing several project roots and correct ownership of open files and operations. | Sidebar recreation, app/session restoration, workspace CRUD, missing roots, path ownership and file-operation tests. |
| R7 | Add feasible genuine offline debugger/breakpoint controls and Problems, Output, Debug Console, Terminal and local Ports features. Capability gating reflects actual backend support. | Actual pause/step/resume/stop tests where supported; panel routing/log retention/cancellation and local-port inspection tests. Decorative or fake controls do not count. |
| R8 | C/C++ accepts user-created relative/nested headers and multi-file projects, with actionable include/compile failures. | Current C coordinator's compiler/runtime and OHOS project-fixture results. |
| R9 | Python provides practical offline module/package management and includes necessary common modules. Investigate sandbox pip and local package installation without online indexes/downloads. | Current Python coordinator's bundled-import inventory, module tests, pure-Python/local-wheel or archive installation tests, unsupported native-wheel errors and OHOS execution reports. |
| R10 | All standalone apps retain offline behavior and compatible shared contracts. Avoid conflicting shared-core writers. Verify changes, conventional commits and normal remote pushes. | Coordinated file ownership, full analyses/tests/builds and offline checks across affected products, task-only commits, remote commit identity or exact push failure. |

## Constraints and exclusions

No network-dependent app features, online package installation, remote debugger, cloud execution, external port exposure, destructive project cleanup, forced Git push, or silent loss of existing content/user work. Online research by the development agent is allowed and requested. Preserve shared retained-editor, import, terminal, backup and profile behavior. Document backend limits while working toward the required runnable content; metadata relabeling is not a repair.

## Task structure and completion

Child deliverables: Go exhaustive curriculum validation and expansion; Go offline IDE adapters/tools; cross-product integration and release evidence. Shared-core UI, analysis/workspace contracts and other language adapters have explicit external owners before editing. Dependencies and verification ordering live in `design.md` and `implement.md`.

`research/acceptance.md` tracks every R1–R10 requirement against current files and reports. Unknown, missing, historical, skipped and host-only evidence never proves OHOS execution. Keep the umbrella goal active until all applicable products and requested deliverables are proven complete.

