# qfli_go release integrity audit

## Goal

Prepare the Go product for store submission by checking both terminal surfaces,
Go execution, offline-only entry points, learning content, and Android/OHOS builds.

## Scope and requirements

- R1: Verify standalone terminal and editor terminal against the real shared core;
  repair incomplete Go command routing, execution, cancellation, diagnostics and
  selected-entry behavior with honest platform capability boundaries.
- R2: Audit login, registration, Git, cloud terminal/projects, remote services and
  startup for the offline Go profile. Hide network-dependent product entry points
  using shared-core policy. Do not disable learner-authored source code globally.
- R3: Inspect the actual assets consumed by the Go app. Replace all placeholder
  Go content with 120 progressive, substantive tutorials and matching examples;
  validate every item and preserve every non-Go byte in shared content assets.
- R4: Run static checks, Flutter/shared regression tests, Go test/vet, and Android
  and OHOS release builds. Test connected targets when available and authorized;
  report build/device failures as failures, never as successful validation.
- R5: Coordinate exactly the three existing Pi panes in Herdr workspace w8, all
  verified with cwd D:\MyNewProjects\qfli_go. Preserve pre-existing work and do
  not change sibling language projects. Shared-core edits are integrated only by
  the main coordinator after checking the current diff and ownership.
- R6: Persist findings, results and remaining blockers in Trellis. Commit each
  reviewed coherent change using Conventional Commits and explicit file lists.

## Existing task links

- 10-09-terminal-flow-pi: selected-entry/runtime changes already in the worktree.
- 10-12-go-curriculum-pi: 120 topic sources/tooling awaiting final review/integration.
- 10-01-content-code-import: completed import regression work to revalidate.
- 10-01-go-platform-support: completed runtime support reference.

## Acceptance criteria

- AC1: Standalone and editor terminals exercise Go routing and local file commands;
  desktop SDK and mobile interpreter capabilities are stated and tested accurately.
- AC2: The offline profile exposes no network-dependent account/Git/cloud routes;
  startup performs no account/cloud refresh for this product.
- AC3: Exactly 120 tutorials and 120 examples are present in loaded Go assets,
  all topic runs pass with recorded assertions and no substantive placeholders.
- AC4: Non-Go shared content and sibling project working trees are preserved.
- AC5: Check/build/device evidence names commands, exit statuses, target identities,
  artifacts and limitations. Every discovered release blocker is fixed or recorded.
- AC6: Reviewed changes are committed with conventional, scoped subjects; task
  records identify those commits and any external blockers.

## Authorization and boundaries

The user approved this parent task and then explicitly directed immediate dispatch
to the three restarted Pi agents. Implementation and local Git commits are already
authorized. Builds and available-device tests are authorized; publishing or pushing
repositories is outside this request. Existing core network policy should be reused.
