# Migration execution plan

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

## Phase gate

- [x] User approved task creation and planning.
- [x] Create parent and three child tasks with explicit dependency boundaries.
- [x] Consolidate all four Pi audit reports and core coordination evidence in research/audit.md.
- [x] Complete PRD, design, implementation plan and curated context manifests for review.
- [x] Receive the user's implementation approval on 2026-11-27 through Claude w5V:p6; preserve the exact approval in prd.md.
- [x] Record Pi-only implementation/Git execution and coordinator-only assignment/review/task activation.
- [x] Receive w5V:p2's final review PASS after the correction-only recheck.
- [x] Have w5V:p1 explicitly activate 11-26-go-github-preservation on 2026-11-27; coordinator confirmed task.py start succeeded and assigned implementation. Other children await their dependency gates and explicit activation. Product/migration acceptance remains unchecked.

## Ordered execution

1. Preserve: refresh live refs and working state; review all existing changes and archived tasks; classify ignored portable knowledge and generated files.
2. Sanitize and persist: the assigned Pi signing/CI owner sanitizes OHOS password literals and machine paths before the preservation checkpoint or any new publication. After review, the Pi Git executor commits portable instructions, Trellis records and preservation evidence in small explicit-path commits. Keep machine-local state excluded.
3. Integrate: fast-forward or merge every reviewed unique branch into main; record all remote ref ancestry; verify the canonical GitHub ref after push.
4. Prepare cloud policy: add common agent rules and update conflicting guidance. Add cloud enforcement checks for accidental output and cloud-only test execution.
5. Repair CI: diagnose failing native tests from logs, apply the smallest source fix, run native/helper/Flutter tests only in Actions, and preserve real failure status.
6. Replace native inputs: build matching Android/OHOS native libraries in the cloud, transfer them by checked provenance, then stop tracking generated binaries.
7. Complete packaging: generate real desktop installers and mobile packages, add explicit signing input gates, retain bounded artifacts and record exact coverage.
8. Validate: use the final source revision in actual hosted runs; inspect jobs and metadata without downloading build archives locally. Resolve failures or retain truthful blockers.
9. Cut over: clone the canonical main into the empty E-drive target; align the core directory contract and verify the exact source graph.
10. Record: update product status without closing unrelated unfinished feature tasks; record CI, signing and device-test limitations; archive completed child tasks only after their criteria pass.
11. Resync: push final task/journal evidence, pull target main with fast-forward only, and compare all three commit/tree IDs and both Git statuses.
12. Hand off: send verified evidence to target Codex through Herdr, obtain acknowledgment, then provide the old-workspace cleanup procedure.

## Validation operations

Preservation is activated. Assigned Pi workers edit only their owned files; w5V:p2 alone performs explicitly sequenced Git operations. CI and cutover children still require their own activation/dependency gates. Coordinator w5V:p1 does not implement or execute Git operations. Verification remains read-only Git/file/task metadata and gh API/log review. Use python -B for permitted task metadata. Do not run local compilers, builds, tests, lint/analyze, dependency installation, SDK downloads, code generation or binary artifact downloads.

Cloud checks include native Go test/vet and race regressions where required, Python helper tests, Flutter analyze/tests with real native runtime binding, actionlint/shell syntax checks, source-only package builds, ABI/export/provenance validation, installer contents, artifact SHA256SUMS, and Chinese documentation lint. Each cloud result must name its source SHA and run/job identity.

## Review and rollback points

- Before the preservation checkpoint or publication: require reviewed OHOS sanitization by its assigned Pi owner, then have the Pi Git executor inspect exact staged paths and secret/generated-file checks.
- Before merges: confirm all agent writers are paused or confined to owned files and record branch SHAs.
- Before binary removal: prove cloud consumers build or retrieve the matching runtime.
- Before target initialization: confirm it is still empty; never overwrite unexpected files.
- Before cleanup: compare source/GitHub/target, confirm exact path ownership, and avoid shared WSL deletion.
- Before completion: rerun metadata comparisons after the final Trellis commit.

## Communication

Pre-handoff source implementation, Git execution and GitHub dispatch belong to assigned Pi workers, preferring gpt-6.1-sol. Coordinator w5V:p1 assigns, reviews and starts tasks without implementing. Assignments name the active child task, owned files, forbidden local commands and other writers. Workers report only to w5V:p1 through Herdr and never contact w5V:p6. The coordinator handles target/cross-repository communication. On model limits use bounded retries, then preserve an evidence summary before compaction/new sessions. Use deepseek-v4.1-flash only as the final fallback after those recovery options fail. After verified Herdr handoff, target Codex assigns its own workers and Git executor.

