# Portable Trellis implementation handoff

Date: 2026-11-27. Active child: `11-26-go-github-preservation`.
Owner: Pi worker w5V:p3, model `gpt-6.1-sol`. Reports go only to w5V:p1.
Status: owned portability batch ready for independent p2 review; files frozen
following this report. This is not preservation acceptance or a cloud test pass.

Policy correction, 2026-11-27: prefer gpt-6.1-sol; on model limits use bounded
retries, then context compaction/new sessions, then deepseek-v4.1-flash only as the
final fallback after those recovery options fail. All w5V role IDs in active
instructions below apply only to the pre-handoff source migration. After verified
Herdr handoff, target Codex assigns its own workers and Git executor; source pane
IDs do not govern target work. The current worker's observed model remains
historical evidence, not a permanent no-fallback rule.

## Implemented

- Retained the user's existing `.gitignore`/Trellis preservation changes. Replaced
  the blanket `.agents` exclusion with a 12-directory shared-skill allowlist.
  All 46 existing Markdown skill/reference files are now visible for review and
  explicit staging. Unreviewed agent state stays ignored.
- Set `session_auto_commit: false`. Did not change Python runtime scripts or run
  task lifecycle commands; the coordinator already activated preservation.
- Added the common cloud-only policy outside the managed `AGENTS.md` block.
  Routed Chinese lint to GitHub Actions and reconciled known workflow, runtime
  agent, Codex agent and shared-skill conflicts. Added a concrete execution spec;
  existing product specs now explicitly scope verification to hosted Actions.
- Repaired exactly 16 stale `file` references in six archived JSONL manifests.
  Only archive prefixes changed; row counts, order and reasons were preserved.
- Recorded p2 final planning review PASS and coordinator activation on 2026-11-27.
  Preservation remains `in_progress`; parent and the other two children retain
  `planning`. Acceptance checkboxes remain open. The sole Git executor remains
  w5V:p2, acting only on sequenced instructions from w5V:p1.
- Preserved existing user task/journal changes and the six-file app-package task
  deletion/archive transition. Did not recreate the deleted source task folder,
  normalize its archived record or alter unrelated task statuses.

## Read-only evidence

Permitted file review, read-only Git inspection and `python -B` task metadata
readback found 145 manifest references, zero missing targets and zero duplicate
paths. A HEAD-to-current metadata comparison confirmed the six repaired
manifests contain exactly 16 changed paths with all reasons unchanged.

`git check-ignore --no-index` inspection confirmed runtime identity, session
pointers and Python caches remain ignored. Reviewed skill files, workflow and
the new execution spec are not ignored. These are local metadata observations,
not hosted automated verification or proof of committed clone completeness.

The coordinator supplied OHOS-only sanitization checkpoint
`810946ed999827b8f483e16595fd7b45da378147`, implemented by p4 and committed by p2.
This worker did not edit signing configuration or execute Git mutations. The
checkpoint satisfies the stated ordering prerequisite for review, not credential
rotation, signed-release acceptance or permission to bypass staged review.

## Known omissions and holds

- This batch is not committed by this worker. p2 must independently review and
  stage explicit paths, including the already-visible portable scripts/specs/
  task archives/curated journals, without forced whole-tree inclusion.
- No local build, test, lint/analyze, dependency setup, SDK download, code
  generation or binary artifact download ran. Exact-SHA hosted verification,
  including Chinese lint and clone/context checks, remains pending.
- Five tracked native libraries remain untouched until source-built cloud
  consumers replace them. Historical binary test captures and generated Flutter
  scaffolds were not deleted. No blanket cleanup was performed.
- p5 owns ignored-source preservation and its research archive; this worker did
  not modify it. Other platform template trees remain ignored intentionally.
- Core canonical paths are `../qflistudio-core` and its `vendor/re_editor`.
  Tested baseline remains `476a30acee21dc486ee2849dd8064a7be665e4d5`, core-check
  `45656065902` success per coordinator evidence. The final migration SHA does
  not yet exist. Product dependency/CI/helper changes are outside this batch.
- Historical examples/evidence are preserved under explicit policy overrides.
  Existing placeholder quality/spec sections were not broadly redesigned.
- Template hashes were not rewritten to disguise local customizations. Future
  Trellis updates must preserve/reconcile the project override and edited skills.

## Exact paths modified in this activated portability batch

```text
.gitignore
AGENTS.md
.codex/agents/trellis-check.toml
.codex/agents/trellis-implement.toml
.codex/agents/trellis-research.toml
.trellis/config.yaml
.trellis/workflow.md
.trellis/agents/check.md
.trellis/agents/implement.md
.trellis/spec/backend/cloud-only-execution.md
.trellis/spec/backend/index.md
.trellis/spec/backend/quality-guidelines.md
.trellis/spec/backend/go-curriculum-tooling.md
.trellis/spec/backend/go-entry-selection.md
.trellis/spec/backend/native-go-runtime.md
.trellis/spec/frontend/index.md
.trellis/spec/frontend/quality-guidelines.md
.trellis/spec/frontend/content-code-import.md
.trellis/spec/frontend/editor-terminal-run.md
.trellis/spec/frontend/native-startup.md
.trellis/spec/guides/index.md
.agents/skills/trellis-before-dev/SKILL.md
.agents/skills/trellis-brainstorm/SKILL.md
.agents/skills/trellis-break-loop/SKILL.md
.agents/skills/trellis-channel/SKILL.md
.agents/skills/trellis-check/SKILL.md
.agents/skills/trellis-continue/SKILL.md
.agents/skills/trellis-finish-work/SKILL.md
.agents/skills/trellis-meta/SKILL.md
.agents/skills/trellis-session-insight/SKILL.md
.agents/skills/trellis-spec-bootstrap/SKILL.md
.agents/skills/trellis-start/SKILL.md
.agents/skills/trellis-update-spec/SKILL.md
.trellis/tasks/archive/2026-10/10-01-go-platform-support/check.jsonl
.trellis/tasks/archive/2026-10/10-01-go-platform-support/implement.jsonl
.trellis/tasks/archive/2026-10/10-09-terminal-flow-pi/check.jsonl
.trellis/tasks/archive/2026-10/10-09-terminal-flow-pi/implement.jsonl
.trellis/tasks/archive/2026-10/10-12-go-curriculum-pi/check.jsonl
.trellis/tasks/archive/2026-10/10-12-go-curriculum-pi/implement.jsonl
.trellis/tasks/11-26-github-workspace-migration/task.json
.trellis/tasks/11-26-github-workspace-migration/prd.md
.trellis/tasks/11-26-github-workspace-migration/design.md
.trellis/tasks/11-26-github-workspace-migration/implement.md
.trellis/tasks/11-26-github-workspace-migration/research/audit.md
.trellis/tasks/11-26-go-github-preservation/task.json
.trellis/tasks/11-26-go-github-preservation/prd.md
.trellis/tasks/11-26-go-github-preservation/design.md
.trellis/tasks/11-26-go-github-preservation/implement.md
.trellis/tasks/11-26-go-github-preservation/research/portable-trellis.md
.trellis/tasks/11-26-go-cloud-ci-readiness/task.json
.trellis/tasks/11-26-go-cloud-ci-readiness/prd.md
.trellis/tasks/11-26-go-cloud-ci-readiness/design.md
.trellis/tasks/11-26-go-cloud-ci-readiness/implement.md
.trellis/tasks/11-26-go-workspace-cutover/task.json
.trellis/tasks/11-26-go-workspace-cutover/prd.md
.trellis/tasks/11-26-go-workspace-cutover/design.md
.trellis/tasks/11-26-go-workspace-cutover/implement.md
```

The remaining 34 shared-skill reference files are newly exposed existing content,
not rewritten files. Portable untracked runtime scripts, other specs, management
baselines and user task/journal changes likewise remain preservation inputs for
p2's explicit review; do not infer that this exact modified-path list is a
complete staging instruction for the entire preservation task.
