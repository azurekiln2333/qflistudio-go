# GitHub migration and cloud-only handoff design

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

## Boundaries and task map

The source scope is only the Go repository. GitHub is the canonical destination. Other products remain under their own Herdr coordinators. All implementation and Git execution belong to assigned Pi workers. w5V:p2 is the sole Git executor. It stages, commits, merges and pushes only on explicit sequenced instructions from coordinator w5V:p1. Other workers do not mutate the index or refs. Source coordinator w5V:p1 assigns disjoint ownership, reviews evidence and starts eligible tasks; it does not edit product files or execute Git operations.

| Child | Deliverable | Dependencies |
| --- | --- | --- |
| 11-26-go-github-preservation | Reviewed branch integration, portable source and Trellis history | Planning approval; live-ref audit |
| 11-26-go-cloud-ci-readiness | Cloud test gates, source-built native artifacts, six-platform installer workflows and local-execution policy | Preservation inventory; core dependency contract |
| 11-26-go-workspace-cutover | GitHub-only target, equivalence evidence and cleanup handoff | Preservation and final CI evidence |

The parent owns integration review, the source requirement map, evidence consolidation and cross-workspace communication. The user approved this plan on 2026-11-27 through Claude w5V:p6; the approval is recorded in prd.md. Independent reviewer w5V:p2 issued final review PASS after the metadata corrections. Coordinator w5V:p1 activated 11-26-go-github-preservation on 2026-11-27 and assigned implementation. Preserve the parent and other children's existing lifecycle states; their dependency gates and later activation still apply. Review PASS and task activation do not complete acceptance.

## Source preservation contract

1. Record initial HEAD, index/worktree differences, live remote refs, local refs and worktree/submodule inventory.
2. Fetch heads without pruning. Use ancestry and tree comparisons to identify unique work. Never infer live remote state from stale tracking refs.
3. Review existing task deletions against archive copies. Preserve historical tasks and unfinished acceptance criteria.
4. Distinguish portable project instructions from machine-local session pointers, credentials, logs, caches and generated output.
5. The assigned Pi signing/CI owner sanitizes tracked OHOS literal password fields and machine signing paths before the preservation checkpoint or any new publication. The Pi Git executor stages explicit files only after sanitization is reviewed. Review names and staged differences before each commit. Do not blanket-add ignored directories. Real exposed credentials require owner rotation.
6. Integrate reviewed branches into main without force push, reset of user edits or history rewrite. Preserve original branch names until their inclusion is proven. Branch deletion is a separate optional cleanup action.
7. Verify GitHub main by an independent ref query and compare the commit/tree with local main.

Checked-in generated native binaries need a coordinated transition: first provide source-built cloud outputs, then remove generated binaries from Git tracking. Keep local copies until source and cloud provenance are confirmed. Historical blobs remain in Git history unless a separately approved history migration is necessary.

## Cloud execution contract

AGENTS.md is the common agent entry point. It must state that builds, tests, dependency resolution, SDK setup and package generation run only in GitHub Actions. Trellis guidance and README commands must route agents to the same policy. Read-only Git inspection, file review and lightweight task metadata operations remain permitted. Cloud validation must include the Chinese documentation lint when Chinese documents change.

Use GitHub-hosted runners only. A self-hosted runner on the user's machine would violate the storage and compute objective. SDKs, toolchains, Flutter/native intermediates and test caches stay on those runners or in bounded GitHub caches/artifacts, never in Git source.

Native artifacts must be built from the same application source SHA used by the package job. Bind each artifact to its source hash, ABI inventory, exported symbols, checksum and source-test conclusion. Package jobs must not silently consume a checked-in library or an artifact from an unrelated run. Preserve provenance checks already present in the collectors.

Run native source tests/vet, CI helper tests and Flutter analyze/tests in the cloud. Native-dependent Flutter tests need a newly built Linux library and an explicit QFLI_GO_RUNTIME_LIBRARY. Do not treat skipped native tests or compilation-only runs as functional acceptance.

Existing six-platform packages are a starting point. Add actual Windows installer, Linux installer package and macOS disk image alongside mobile APK/IPA/HAP outputs. Keep portable bundles when useful. Signing is a separate mode with explicit secret requirements. Missing certificates must block a signed release and must never silently yield an unsigned release under a signed name. Release publication should be deliberate; ordinary validation runs upload bounded artifacts.

## Dependency portability

The core coordinator confirmed qflistudio-core as the canonical target sibling. Update Go dependency references to ../qflistudio-core and ../qflistudio-core/vendor/re_editor. Keep the Dart package/import name qfli_studio_core. Update lock metadata, CI checkout locations and helper expectations consistently, without an alias or junction. Tested core baseline is 476a30acee21dc486ee2849dd8064a7be665e4d5 with core-check run 45656065902; final migration SHA is pending. Do not change or copy the core repository from this session.

## Cutover and equivalence

Initialize the currently empty target directly from GitHub after source commits are available. The target may have one remote named origin pointing to the canonical GitHub repository; no Gitee/GitLab/GitCode/CNB remotes.

Compare source main, GitHub main and target main by exact commit and tree IDs. Also inspect tracked worktree differences, staged state and nonignored untracked files in both directories. Compare portable Trellis files against the committed tree and verify referenced context paths. Excluded SDKs, caches, build output, credentials and local session pointers are not part of source equivalence.

Archive completed migration child tasks and record final evidence before the final synchronization pass. Recheck both workspaces after the last journal/task commit. Do not leave a final journal edit unpushed after declaring the target current.

## Herdr coordination

Use observed pane IDs, never guessed pane topology. The source coordinator is w5V:p1; source Pi panes are p2-p5. Target coordinator is w6K:p1 with four Pi panes. Verify identities again before the final handoff. Pi owns implementation, Git index/commit/merge/push operations, GitHub dispatch and assigned cutover execution. The coordinator assigns, reviews, starts tasks and handles cross-repository coordination only. Workers contact only w5V:p1, never w5V:p6. Prefer gpt-6.1-sol; on model limits use bounded retries, then context compaction/new sessions, then deepseek-v4.1-flash only as the final fallback after those recovery options fail.

The target coordinator has received a hold notice and the cloud-only restriction. The final handoff is distinct: include exact source/target/GitHub SHAs, evidence paths, run IDs, artifact/signing state, unfinished product tasks and cleanup boundaries. Require an acknowledgment, not an inferred completion from idle status.

## Cleanup and rollback

Delete only exact, resolved, project-owned paths whose contents have been classified as reproducible output. Avoid reparse-point traversal. Never use git clean -fdx as a general cleanup shortcut. Do not remove the old source directory while its Herdr panes or any unpreserved data still depend on it.

WSL is machine-wide infrastructure. Inventory distributions and VHDX paths without starting a stopped distribution. Do not unregister a shared distribution or directly delete its VHDX until its data has an ownership and preservation disposition from the responsible product coordinators. If that evidence cannot be obtained, leave that deletion pending and provide the exact reason.

Rollback uses recorded commits and additive corrective commits. Keep the original workspace until the target and GitHub checks pass. Failed cloud runs remain visible evidence; do not suppress failures to finish migration.

