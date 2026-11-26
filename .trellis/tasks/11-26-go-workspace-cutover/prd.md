# Verify Go workspace cutover and cleanup handoff

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

## Goal

Clone the canonical GitHub main into the E-drive target, verify source and Trellis equivalence, coordinate core dependency layout, and hand off safe cleanup through Herdr.

## Requirements

- Initialize the empty E-drive target from canonical GitHub main only after preservation.
- Compare source, GitHub and target commit/tree identities, tracked worktree state and portable Trellis files.
- Keep target remotes GitHub-only and preserve the canonical core source graph at ../qflistudio-core and ../qflistudio-core/vendor/re_editor. Tested baseline is 476a30acee21dc486ee2849dd8064a7be665e4d5 (core-check run 45656065902); only the final coordinated migration SHA remains pending.
- Transfer evidence and unfinished work through Herdr to target Codex and obtain explicit acknowledgment.
- Classify exact cleanup paths; retain unique source/evidence and avoid reparse traversal.
- Coordinate shared WSL ownership before any distribution removal.
- Complete task/journal commits before the final push/pull and clean-status checks.

## Acceptance Criteria

- [ ] Target has only canonical GitHub remotes.
- [ ] Source main, live GitHub main and target main have matching commit/tree IDs.
- [ ] Both workspaces have no staged, unstaged or nonignored untracked differences after final evidence commits.
- [ ] Portable Trellis files/context paths and cloud-only rules are present in target.
- [ ] Target Codex acknowledges the final evidence and responsibility transfer.
- [ ] Cleanup report lists exact candidates, preservation holds, measured-size limits and WSL exclusions.

## Dependencies

Depends on 11-26-go-github-preservation and 11-26-go-cloud-ci-readiness. The user approved the parent/child plan on 2026-11-27; see the parent prd.md. Reviewer w5V:p2 issued final review PASS after metadata corrections. Only the preservation child has been activated; this child still requires its dependencies and explicit activation by w5V:p1. Pi owns cutover implementation and Git execution. The coordinator assigns, reviews and starts tasks without implementing. The current target hold acknowledgment is not the final handoff. No clone or cleanup runs during planning.

## Scope boundary

Parent requirements: 11-26-github-workspace-migration. Evidence: ../11-26-github-workspace-migration/research/audit.md. This child owns only the Go repository. No local builds/tests, fabricated cloud results, unrelated product edits or shared-history rewrite.
