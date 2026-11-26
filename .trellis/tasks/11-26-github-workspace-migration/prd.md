# GitHub migration and cloud-only workspace handoff

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

## Goal

Preserve the complete Go product source and portable project progress on GitHub, consolidate reviewed branches into main, verify cloud-only build/test/package workflows, and transfer a clean source workspace to the E drive with a safe cleanup handoff.

## Background and confirmed evidence

- Source: D:/MyNewProjects/qfli_go. Target: E:/MyNewProjects/QFLIProjects/qflistudio-go. Target is currently empty and is not a Git repository.
- Canonical repository: azurekiln2333/qflistudio-go. Five configured remotes were queried and fetched successfully. Source/GitHub main is c5cab3d2541b77f3a584dc024d1245a1576c5e68. Source/GitHub ci/app-packages is f279134c0525ca704f5ae8ea122ce27e76a2e24b, two commits ahead. Every other remote tip is already an ancestor of main.
- Existing uncommitted work includes portable Trellis knowledge and an intentional archive transition. Sixteen archived context references need path repair. Five generated native libraries remain tracked. Ignored build directories contain project Python helpers and unclassified evidence.
- Latest application run 45484027345 passed seven jobs. Native run 45484027361 failed recurring debugger tests. Mobile app jobs still consume tracked libraries. Flutter analysis/tests, desktop installer formats and signed-release workflows are missing.
- Tracked OHOS signing configuration contains literal password fields and local credential paths. Repository Actions secret/variable counts are zero. No secret values belong in this task or handoff.
- Core coordinator confirms the canonical sibling name qflistudio-core. Go dependency paths and re_editor override must change together; package/import name qfli_studio_core stays unchanged. Core tested baseline is 476a30acee21dc486ee2849dd8064a7be665e4d5 (core-check run 45656065902). Its final migration SHA is still pending.
- Partial selected-path storage measurement is 7,797,485,678 logical bytes, not a reclaim estimate. None of the five WSL registrations is inside qfli_go. Shared/other-product guest data is unverified.
- The user approved task creation/planning by replying 继续. Source and target agent groups acknowledge the cloud-only restriction.
- On 2026-11-27 the user approved the final plan through Claude w5V:p6: “trellis 制定完，trellis 移交给 pi 去做，我已经交代挺清楚了”. All implementation and Git execution belong to Pi. Coordinator w5V:p1 assigns work, reviews results and starts eligible tasks; it does not implement. Independent reviewer w5V:p2 issued final review PASS after the metadata corrections. On 2026-11-27 coordinator w5V:p1 confirmed task.py start succeeded for 11-26-go-github-preservation and assigned implementation. The other children still require their dependency gates and explicit activation; no acceptance is complete merely because review passed.

Detailed evidence, file anchors and audit limitations are in research/audit.md.

## Requirements

- R1: Preserve all Go source, configuration, portable Trellis tasks/archives/specs/scripts/journals and reviewed agent skills on GitHub. Inventory ignored project logic and preserve unique evidence before deletion.
- R2: Account for all live local/remote branch tips and integrate reviewed unique work into main without losing edits or rewriting shared history. GitHub is canonical; target remotes must be GitHub-only.
- R3: Provide GitHub-hosted native/helper/Flutter tests and six-platform native/application/installer workflows for Windows, Linux, macOS, iOS, Android and OHOS. Bind native inputs and packages to matching source SHA and provenance. Do not treat compilation, skipped checks or unsigned output as functional/signed acceptance.
- R4: Commit a common prohibition on local builds, tests, lint/analyze, dependency installation, SDK downloads, code generation and artifact/cache-producing verification. Use hosted Actions and bounded cloud storage. Read-only inspection and lightweight source/task maintenance remain allowed.
- R5: Sanitize tracked signing configuration before publication. Use explicit cloud signing inputs with fail-closed release gates. Real exposed credentials require owner rotation; missing credentials remain an external acceptance blocker.
- R6: Align Go/core dependency paths, lock metadata, CI checkout and helper assumptions with the canonical target name. Retain a tested pinned core source graph and record the final coordinated core SHA.
- R7: Initialize the empty target from canonical GitHub, then prove source/GitHub/target commit and tree equality, portable context completeness and clean Git state after the last task/journal commit.
- R8: Coordinate through Herdr. Before verified handoff, Pi performs source implementation and Git execution; w5V:p1 assigns, reviews and starts tasks without implementing. Source workers report only to w5V:p1, never to w5V:p6. Prefer gpt-6.1-sol; on model limits use bounded retries, then compaction/new sessions, then deepseek-v4.1-flash only as the final fallback after those recovery options fail. Transfer evidence to target Codex and obtain acknowledgment; target Codex then assigns its own workers and Git executor.
- R9: Provide exact, bounded cleanup dispositions after preservation. Protect unique source/evidence and reparse targets. Keep WSL and sibling-product data until their owners establish preservation and cleanup authority. Do not close unrelated unfinished product tasks.

## Task map and dependencies

| Child | Owning requirements | Dependency |
| --- | --- | --- |
| 11-26-go-github-preservation | R1, R2, pre-publication part of R5 | Approved plan and live-ref audit |
| 11-26-go-cloud-ci-readiness | R3, R4, R5, R6 | Preservation inventory and core contract |
| 11-26-go-workspace-cutover | R7, R8, R9 | Final preservation and cloud evidence |

Parent owns integration review and final cross-child acceptance. Binary removal in preservation waits for source-built consumers in the CI child. Child dependencies are also recorded in each child PRD and execution plan.

## Acceptance Criteria

- [ ] Every live/local branch is accounted for and reviewed unique work is on canonical main.
- [ ] Portable project/Trellis knowledge and ignored unique source have a documented committed preservation disposition; context references resolve.
- [ ] New commits contain no credentials, build output, cache or SDK trees. Existing generated native files are removed from tracking only after cloud replacements are ready.
- [ ] Cloud native/helper/Flutter checks and six-platform installer/package jobs have source-SHA-specific run evidence. Failed/skipped/unverified checks remain explicit.
- [ ] Signed-release modes require real inputs; any unavailable credential/device acceptance remains visibly blocked, never completed by unsigned fallback.
- [ ] Canonical core paths and pinned source graph are reproducible in the cloud and documented for a fresh clone.
- [ ] Source main, GitHub main and target main have the same verified commit/tree, and both workspaces are clean after final progress commits.
- [ ] Target uses only GitHub and all target agents acknowledge the cloud-only rule and final handoff.
- [ ] Cleanup instructions list exact candidates, source/evidence holds and shared WSL exclusions with measured-size limitations.

## Out of Scope

- Editing other product repositories or shared parent instructions from this Go session. Their owners coordinate through Herdr.
- Local project tests/builds, dependency setup, SDK installation, binary artifact downloads, physical-device acceptance claims or store submission.
- Fabricated signing materials/results, unrelated feature redesign, force-push/history rewrite, or blanket cleanup of unknown/shared data.

## External gates and deferred execution checks

Credential provisioning/rotation belongs to the credential owner. Core final migration SHA belongs to the core coordinator. WSL guest ownership and ignored toolchain modifications must be resolved before their cleanup. These gates do not block planning or safe source preservation, but they block the corresponding completion claims. Recheck live refs, target capacity/emptiness and active writers immediately before implementation operations.
