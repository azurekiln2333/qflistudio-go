---
name: trellis-channel
description: Use Trellis channel for live multi-agent collaboration, spawned workers, cross-agent review, progress inspection, forum channels, and channel log debugging.
---

# trellis-channel

## Project execution override

Read `AGENTS.md` and `.trellis/spec/backend/cloud-only-execution.md` first.
All project checks, builds, dependency/toolchain setup, code generation and
artifact verification/downloads are GitHub-hosted Actions only, never local.
Use `python -B` for permitted task metadata. The pre-handoff source migration uses Herdr, not a new
Trellis channel: source workers contact only w5V:p1 and do not redispatch. After
verified Herdr handoff, target Codex assigns its own workers and Git executor.
source pane IDs do not govern target work. Follow AGENTS.md model recovery/final-
fallback policy. Channel examples do not override assigned communication/Git ownership.

Trellis channel supports agent collaboration.
It supports peer workers and event logs.
It supports interruption and debugging.
It supports durable forum feedback.

Use it to brainstorm, dispatch, or review.
Use it to open forums or inspect threads.
Use it to debug stalled channels.

This skill is an index. Load only the reference file for the current job — do not preload all of them.

## First Commands

```bash
trellis --version
trellis channel --help
trellis channel list --all
trellis channel list --scope global --all
```

If the user names a channel or thread, inspect it before asking for background:

```bash
trellis channel forum <board> --scope global
trellis channel thread <board> <thread> --scope global
trellis channel context list <board> --scope global --thread <thread>
```

## Route By User Intent

| User intent | Read |
|---|---|
| "和 codex/claude 讨论一下", "brainstorm with another agent" | `references/workflows.md` |
| "派一个 implement/check agent", "让 agent review", "spawn a worker" | `references/workflows.md`, then `references/workers.md` |
| "开 issue 区 / topic 群 / changelog / board", "make a forum" | `references/forum.md` |
| "看看这个 thread / linked context", "inspect a thread" | `references/forum.md` |
| "channel 卡住了 / 没输出 / progress 内容不全", "worker stalled" | `references/progress-debugging.md` |
| "具体命令怎么写", "what flags does X take" | `references/command-reference.md` |

## Core Rules

- New forum channels use `--type forum`. A `thread` is one item inside a forum channel.
- Use `--context-file` / `--context-raw` and `trellis channel context add/delete/list`. `--linked-context-*` is deprecated terminology.
- Use `--stdin` or `--text-file` for long messages. Do not put long mixed Chinese/English text in the positional shell argument.
- Pretty `messages` output is an operator dashboard and may truncate progress. Use `--raw` for audit.
- `--as` is the speaker or worker handle, depending on the command. Use explicit, stable names when multiple agents or sessions are involved.
- `--scope project` (default) operates on the current cwd's project bucket. `--scope global` operates on the shared `__global__` bucket. Pick scope deliberately. A global board is invisible from project listings unless `--scope global` is passed.
- For brainstorm, do multiple pressure-test rounds. One answer plus one confirmation is review, not brainstorm.
- **Dispatcher wait pattern**: use Trellis system events.
- Wait for `--kind done` or `--kind turn_finished`.
- Do not use a user `--tag` as the completion signal.
- CLI help lists `phase_done` and `question` as examples.
- Only `interrupt` is reserved. Other tags are labels.
- Workers may write tags instead of sending them. Do not rely on that behavior.
- See `references/command-reference.md` "tag vs kind".
- Forum channels are event-sourced. Do not parse `events.jsonl` first. Use `forum`, `thread`, `messages --thread`, and `context list`.
- `@mindfoldhq/trellis-core` owns reusable channel/thread state, event append, seq allocation, context/title projection, reducers, and task helpers. The CLI owns flags, terminal rendering, prompts, worker lifecycle, and process exits.

## Reference Files

- `references/workflows.md` — canonical collaboration patterns A–F (peer brainstorm, spawned review, dispatch-and-wait, forum issue capture, interrupt-and-redirect, one-shot run).
- `references/forum.md` — forum channels, context, title, rename, changelog forums, thread filtering.
- `references/workers.md` — spawn, agent cards, context injection (`--file` / `--jsonl`), interrupts, kill semantics.
- `references/progress-debugging.md` — progress/raw inspection, stalled worker diagnosis, OOM guard, exit codes.
- `references/command-reference.md` — current CLI command reference (every subcommand, every flag, output conventions, scope/type model).

## Not For

- One static review where a markdown file and prompt are enough.
- Replacing normal tool calls with self-logging.
- Long-term memory retrieval. Use durable forum channels for actionable issues, and `trellis mem` (the `trellis-session-insight` skill) for session/history search.
