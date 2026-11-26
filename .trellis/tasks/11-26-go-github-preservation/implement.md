# Execution plan

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

## Phase gate

The user approved the final parent/child plan on 2026-11-27, as recorded in the parent prd.md. Reviewer w5V:p2 issued final review PASS after metadata corrections. Coordinator w5V:p1 confirmed task.py start succeeded on 2026-11-27 and assigned this child's implementation; it is in_progress. Acceptance remains open. All implementation and Git execution belong to assigned Pi workers with gpt-6.1-sol. The coordinator assigns, reviews and starts tasks without implementing. Report only to w5V:p1 through Herdr; never contact w5V:p6.

## Ordered steps

1. Refresh baseline and live refs without pruning.
2. Complete portable/ignored-source and generated-file dispositions.
3. Require the assigned Pi signing/CI owner to sanitize OHOS password literals and machine signing paths before the preservation checkpoint or any new publication. Keep credential values out of evidence.
4. After sanitization review, the Pi Git executor stages only approved source/progress/instruction paths and commits the preservation checkpoint.
5. Integrate every reviewed unique branch into main and push GitHub.
6. Coordinate generated-library removal with cloud readiness.
7. Record ancestry and exact canonical commit/tree after final commits.

## Validation

Preservation is activated; workers edit only their assigned files. Local verification remains read-only Git/file/task metadata and GitHub log/API review. Use python -B for permitted task metadata. All project tests, lint, compilation, dependency setup and package checks run in GitHub-hosted Actions. Record exact SHA and run/job identities. Load the parent design for rollback and final synchronization requirements.
