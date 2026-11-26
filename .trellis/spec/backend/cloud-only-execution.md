# Cloud-Only Execution and Portable Agent Context

## 1. Scope / Trigger

Apply this contract to all agents and all repository instructions. It covers
verification, dependency/toolchain setup, generated output and portable Trellis
context. `AGENTS.md`, outside its managed Trellis block, is the common policy
entry point. Historical task evidence does not authorize repeating local checks.

## 2. Signatures

Permitted local metadata examples, within assigned ownership:

```text
python -B .trellis/scripts/get_context.py --mode packages
python -B .trellis/scripts/task.py list-context <task> <action>
python -B .trellis/scripts/task.py current --source
```

File review, read-only Git inspection and GitHub run/log/API metadata queries are
also permitted. Only the coordinator activates eligible migration tasks. Do not
run task lifecycle commands just to inspect state.

Project verification commands belong only in GitHub-hosted Actions. This includes
Go test/vet/build, Flutter analyze/test/build/pub, Python helper tests, generators
and `python scripts/ste-lint-zh.py <files>`. `python -B` does not make a test,
generator, dependency installer or output-producing helper safe to run locally.

## 3. Contracts

- Use GitHub-hosted runners, not local or machine-backed self-hosted runners.
- No local builds, tests, lint/analyze/type-check, dependency setup, SDK/toolchain
  downloads, code generation or binary artifact downloads.
- Evidence identifies source SHA, workflow, run ID, job ID/name, conclusion and
  skipped/unverified scope. A result for another revision is historical evidence.
- `session_auto_commit: false` in `.trellis/config.yaml` prevents archive/journal
  helpers from silently staging or committing shared work. Review and stage
  explicit files through the assigned Git executor, never forced whole trees.
- Portable context includes reviewed workflow/config/scripts/specs, task records,
  archives, curated journals and the reviewed `.agents/skills` tree. Preserve
  `.trellis/.version` and `.template-hashes.json` as update baselines.
- Keep `.trellis/.developer`, `.runtime`, task pointers, raw sessions, caches,
  backup/conflict/temp files, credentials, SDKs and generated output excluded.
- When a task is archived, JSONL `file` paths must name the archived location.
  Change only stale prefixes; preserve reasons, record order and unrelated data.
- During the pre-handoff source migration only, `w5V:p2` alone stages, commits,
  merges and pushes on explicit sequenced instructions from `w5V:p1`. Other
  source workers never mutate the index or refs. After verified Herdr handoff,
  target Codex assigns its own workers and Git executor; source pane IDs do not
  govern target work. Ownership never authorizes edits outside assigned files.
- Prefer `gpt-6.1-sol`. On model limits use bounded retries, then context
  compaction/new sessions. Use `deepseek-v4.1-flash` only as the final fallback
  after those recovery options fail.

## 4. Validation & Error Matrix

| Condition | Required response |
| --- | --- |
| Generic skill says to run checks locally | Apply `AGENTS.md`; route checks to Actions |
| Hosted check missing, pending, failed or skipped | Report that state; do not claim pass or run locally |
| Required context path missing after archive | Repair the exact archive prefix or report the missing target |
| File is ignored | Classify it; do not infer disposable or force-add the tree |
| Signing values or machine credential paths found | Stop publication until assigned owner sanitizes; never print values |
| Another worker owns the index/refs | Report file readiness; do not stage, commit, fetch or change refs |

## 5. Good / Base / Bad Cases

- Good: an assigned worker edits instructions, reads metadata with `python -B`,
  and reports cloud validation as pending with the reviewed file list.
- Base: a hosted run at the reviewed SHA fails; retain its failed conclusion and
  propose an owned source fix without downloading artifacts to the workstation.
- Bad: running local tests, Chinese lint or dependency installation because the
  hosted job is absent, or claiming an old green run validates new changes.

## 6. Tests Required

All automated checks run in GitHub Actions. Required assertion points are:

- Task manifests contain unique paths and each referenced file exists in a fresh
  checkout, including archived task targets.
- Reviewed shared skills are available from a clone while identity, session,
  runtime, cache and credential paths remain excluded.
- Trellis config disables auto-commit and agent entry points route checks to the
  common cloud-only policy.
- Any changed Chinese documentation receives hosted Chinese lint evidence.

These are requirements, not claims that a hosted check already exists or passed.
Local read-only file/task metadata inspection can identify unresolved paths and
instruction conflicts; it is not a substitute for hosted test evidence.

## 7. Wrong vs Correct

Wrong: run `flutter test` or the Chinese linter locally to finish a checklist,
then mark verification green without an exact-SHA hosted result.

Correct: edit only assigned source/context, report the hosted check as pending,
and provide the Git executor/coordinator the exact paths and required cloud gates.
