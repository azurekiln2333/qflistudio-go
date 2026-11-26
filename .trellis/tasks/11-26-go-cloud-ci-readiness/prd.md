# Complete Go cloud-only CI and installer workflows

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

## Goal

Repair cloud test failures and source-built native artifact flow, cover six-platform packages and installers, and enforce cloud-only execution for all agents.

## Requirements

- Repair native debugger regressions using hosted evidence without weakening provenance/safety checks.
- Run native source/helper tests and Flutter analysis/tests on GitHub-hosted runners.
- Build matching Android/OHOS native inputs from source for each package SHA; add standalone Windows/Linux native artifacts.
- Provide Windows installer, Linux installer package, macOS disk image, Android APK, iOS IPA and OHOS HAP workflows.
- Add explicit signing-input gates; absent credentials must block signed release rather than silently publish unsigned output.
- Commit common cloud-only agent rules and reconcile conflicting README/Trellis instructions.
- Keep intermediates, SDKs, caches and package output in bounded cloud storage and preserve artifact provenance.
- Use canonical ../qflistudio-core and ../qflistudio-core/vendor/re_editor without aliases. Keep package/import name qfli_studio_core. Tested baseline is 476a30acee21dc486ee2849dd8064a7be665e4d5 (core-check run 45656065902); the final coordinated migration SHA remains pending.

## Acceptance Criteria

- [ ] Recurring native failures have an evidence-based fix and successful hosted checks.
- [ ] Flutter analysis/tests run in cloud with real native library binding where required.
- [ ] Android/OHOS packaging no longer consumes tracked prebuilt runtime fallback.
- [ ] Standalone native and six-platform installer/package workflows have actual hosted run evidence.
- [ ] Signed modes validate all required inputs and document credential blockers honestly.
- [ ] Agent instructions consistently prohibit local builds/tests/dependency installs.
- [ ] No generated output is added to source; cloud manifests bind source SHA, checksums, ABIs and signing state.

## Dependencies

Requires preservation inventory and the confirmed core dependency contract. The user approved the parent/child plan on 2026-11-27; see the parent prd.md. Reviewer w5V:p2 issued final review PASS after metadata corrections. Only the preservation child has been activated; this child still requires its dependencies and explicit activation by w5V:p1. Pi owns implementation, Git execution and GitHub dispatch. The coordinator assigns, reviews and starts tasks without implementing. The preservation child must not remove tracked native inputs before this child replaces consumers. Target cutover waits for this child’s final evidence or explicitly accepted external blockers.

## Scope boundary

Parent requirements: 11-26-github-workspace-migration. Evidence: ../11-26-github-workspace-migration/research/audit.md. This child owns only the Go repository. No local builds/tests, fabricated cloud results, unrelated product edits or shared-history rewrite.
