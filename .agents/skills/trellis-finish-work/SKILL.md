---
name: trellis-finish-work
description: "Wrap up the current session: verify quality gate passed, remind user to commit, archive completed tasks, and record session progress to the developer journal. Use when done coding and ready to end the session."
---

# Finish Work

## Project execution override

Read `AGENTS.md` and `.trellis/spec/backend/cloud-only-execution.md` first.
All project checks, builds, dependency/toolchain setup, code generation and
artifact verification/downloads are GitHub-hosted Actions only, never local.
Use `python -B` for permitted task metadata. This project sets
`session_auto_commit: false`: lifecycle helpers write metadata but never own Git
staging/commits. Only archive completed acceptance, not merely the active task.
During the pre-handoff source migration only, w5V:p1 assigns lifecycle writes and
w5V:p2 alone executes sequenced Git operations. After verified Herdr handoff,
target Codex assigns its own workers and Git executor; source pane IDs do not
govern target work. Follow AGENTS.md model recovery/final-fallback policy. Do not
run this skill as an unassigned worker.

Wrap up the current session: archive the active task (and any other completed-but-unarchived tasks the user wants to clean up) and record the session journal. Code commits are NOT done here — those happen in workflow Phase 3.4 before you invoke this command.

## Step 1: Survey current state

```bash
python ./.trellis/scripts/get_context.py --mode record
```

This prints:

- **My active tasks** — review whether any besides the current one are actually done (code merged, AC met) and should be archived this round.
- **Git status** — quick visual on what's dirty.
- **Recent commits** — you'll need their hashes in Step 4 for `--commit`.

If `--mode record` surfaces other tasks, leave them unchanged unless their owner explicitly authorizes archival. Archive the current task only when every acceptance criterion and required hosted check is met or its blocker is explicitly accepted by the user.

## Step 2: Sanity check — classify dirty paths

Run:

```bash
git status --porcelain
```

Classify `.trellis/workspace/` and `.trellis/tasks/` paths too. Auto-commit is disabled; preserve existing metadata edits and include only explicitly assigned changes in the Git executor's reviewed sequence.

For each remaining dirty path, decide whether it belongs to **the current task** or to **other parallel work** (e.g., another terminal window editing the same repo). Heuristics:

- Paths referenced in the current task's `prd.md` / `implement.jsonl` / `check.jsonl` → current task
- Paths in code areas matching the task's stated scope, or that you remember editing this session → current task
- Paths in unrelated areas you have no recollection of touching this session → other parallel work

Then route:

- **Any remaining path looks like current-task work** — bail out with:
  > "Working tree has uncommitted code changes from this task: `<list>`. Return to workflow Phase 3.4 to commit them before running ``finish-work` (Trellis command)`."

  Do NOT run `git commit` here. Do NOT prompt the user to commit. The user goes back to Phase 3.4 and the AI drives the batched commit there.
- **All remaining paths look unrelated** (other parallel-window work) — report them once and continue to Step 3:
  > "FYI, dirty files outside this task's scope — leaving them for the other window: `<list>`."
- **Genuinely unsure** — ask the user once: "Are `<list>` this task's work I forgot to commit, or another window's? (commit / ignore)" — then route per their answer.

## Step 3: Archive task(s)

```bash
python ./.trellis/scripts/task.py archive <task-name>
```

Archive only coordinator-assigned tasks whose acceptance is complete. With `session_auto_commit: false`, archive writes metadata but produces no commit; provide the exact moved paths to the designated Git executor.

If there is no active task and the user did not confirm any cleanup archives, skip this step.

## Step 4: Record session journal

```bash
python ./.trellis/scripts/add_session.py \
  --title "Session Title" \
  --commit "hash1,hash2" \
  --summary "Brief summary"
```

Use the work-commit hashes produced in Phase 3.4 (visible in Step 1's `Recent commits` list, or via `git log --oneline`) for `--commit`. Do not include the archive commit hashes from Step 3. With `session_auto_commit: false`, this writes journal metadata without a commit; the designated Git executor handles reviewed staging/commits separately.

Final git log order: `<work commits from 3.4>` → `chore(task): archive ...` (one or more) → `chore: record journal`.
