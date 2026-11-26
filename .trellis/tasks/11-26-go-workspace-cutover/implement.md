# Execution plan

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

## Phase gate

The user approved the final parent/child plan on 2026-11-27, as recorded in the parent prd.md. Reviewer w5V:p2 issued final review PASS after metadata corrections. The preservation child is activated; keep this child planning until its dependencies are met and coordinator w5V:p1 explicitly activates it. All cutover implementation and Git execution belong to assigned Pi workers with gpt-6.1-sol. The coordinator assigns, reviews and starts tasks without implementing. Report only to w5V:p1 through Herdr; never contact w5V:p6.

## Ordered steps

1. Confirm source preservation, cloud evidence and final intended SHA. Use canonical ../qflistudio-core and ../qflistudio-core/vendor/re_editor, with tested baseline 476a30acee21dc486ee2849dd8064a7be665e4d5 (core-check run 45656065902) until the final coordinated core SHA is validated. Do not mistake the pending final SHA for an unresolved folder name.
2. Recheck target emptiness, capacity and Herdr identities.
3. Clone canonical GitHub main with only a GitHub origin.
4. Verify commit/tree/status and portable project/context completeness.
5. Record precise cleanup candidates and preservation/WSL holds.
6. Finalize task/journal evidence, push and fast-forward target.
7. Recheck all identities and both workspaces after the final write.
8. Send final Herdr handoff and obtain acknowledgment.
9. Report results and the exact original-directory cleanup sequence.

## Validation

This child is not yet activated. After activation, local verification remains read-only Git/file/task metadata and GitHub log/API review. Use python -B for permitted task metadata. All project tests, lint, compilation, dependency setup and package checks run in GitHub-hosted Actions. Record exact SHA and run/job identities. Load the parent design for rollback and final synchronization requirements.
