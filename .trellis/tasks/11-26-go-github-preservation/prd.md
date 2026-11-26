# Preserve Go source and Trellis history on GitHub main

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

## Goal

Audit all refs and portable project files, remove generated files from tracking safely, merge reviewed work to main, and verify GitHub synchronization.

## Requirements

- Account for all live remote and local branch tips, preserving reviewed unique commits on GitHub main.
- Preserve portable Trellis tasks, archives, specs, scripts, journals and agent instructions.
- Review existing changes and ignored source before staging; resolve task deletions against archived copies.
- Exclude credentials, runtime state, caches, generated outputs and SDKs. Require the assigned Pi signing/CI owner to sanitize tracked OHOS password literals and machine signing paths before the preservation checkpoint or any new publication.
- Coordinate removal of tracked native binaries with the cloud CI child, keeping local copies until preservation is verified.

## Acceptance Criteria

- [ ] Every audited branch tip is included in main or has a documented unresolved blocker.
- [ ] Portable project/Trellis files are committed and context paths resolve.
- [ ] Reviewed commits add no credentials, caches or generated output.
- [ ] GitHub main matches the recorded local commit/tree.
- [ ] Unfinished product tasks retain truthful status and ignored unique files have an explicit preservation disposition.

## Dependencies

The user approved the parent/child plan on 2026-11-27; see the parent prd.md. Reviewer w5V:p2 issued final review PASS after the metadata corrections. On 2026-11-27 coordinator w5V:p1 confirmed task.py start succeeded and assigned this child's implementation. Its status is in_progress, not completed. Pi owns implementation and Git execution. The coordinator assigns, reviews and starts tasks without implementing. Preservation is activated and may precede CI work, subject to pre-publication sanitization and disjoint ownership. Removal of generated native libraries depends on the source-built artifact flow in 11-26-go-cloud-ci-readiness. Final main synchronization follows that child’s reviewed changes.

## Scope boundary

Parent requirements: 11-26-github-workspace-migration. Evidence: ../11-26-github-workspace-migration/research/audit.md. This child owns only the Go repository. No local builds/tests, fabricated cloud results, unrelated product edits or shared-history rewrite.
