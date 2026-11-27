<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

If you're using Codex or another agent-capable tool, additional project-scoped helpers may live in:
- `.agents/skills/` — reusable Trellis skills
- `.codex/agents/` — optional custom subagents

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

<!-- TRELLIS:END -->

## Cloud-only execution policy

This project rule applies to every agent, skill, sub-agent, script example and
verification instruction in this repository, including imported Trellis guidance.
It takes precedence over generic instructions to run checks locally.

- Run builds, tests, lint, type-checking/analyze, dependency resolution or installs,
  SDK/toolchain downloads, code generation and package/artifact verification only
  on GitHub-hosted Actions runners. Never run them locally or on a self-hosted
  runner backed by the user's machine. Do not download build artifacts locally.
- Chinese documentation lint is also cloud-only. A missing hosted check is a
  pending verification item, not permission to run the command locally.
- Local source edits, file review, read-only Git inspection, GitHub run/log/API
  metadata queries and lightweight task metadata maintenance are allowed within
  assigned ownership. Use `python -B` for permitted Python task metadata commands.
  Do not use project helpers that create caches/output as inspection shortcuts.
- Record the exact source SHA, workflow/run/job identity, outcome and skipped or
  unverified scope for cloud checks. Never turn an old, skipped, failed or pending
  cloud result into a current pass. Keep credentials, SDKs, caches and generated
  output out of source and task evidence.
- Preserve other writers' changes. Do not force-add ignored trees, rewrite shared
  history or run cleanup without explicit path-specific preservation approval.

For the pre-handoff source migration only, `w5V:p2` is the sole Git executor.
It stages, commits, merges and pushes only on explicit sequenced instructions
from coordinator `w5V:p1`. Other workers do not mutate the index or refs. The
source coordinator assigns, reviews and starts eligible tasks without implementing.
Source workers report only to `w5V:p1` through Herdr, never to `w5V:p6`.
After verified Herdr handoff, target Codex assigns its own workers and Git executor;
the source pane IDs do not govern target work. Task/journal auto-commit is disabled.

Prefer `gpt-6.1-sol`. On model limits, use bounded retries, then context compaction
or a new session. Use `deepseek-v4.1-flash` only as the final fallback after those
recovery options fail.

See `.trellis/spec/backend/cloud-only-execution.md` for the portable execution
and evidence contract.

改写中文技术文本时套用受控中文规则：一句一动作、主动语态、一词一义（同一概念全篇同一个词）、不用分号连接动作、句长（指令 ≤ 25 字、说明 ≤ 40 字）、去掉虚动词（进行 / 加以 + 名词）、套话（需要注意的是、在一定程度上）、营销形容词（无缝、强大、赋能、闭环）与含糊词（若干、一些、相关）； 不得改动情态（可能 / 也许）：置信度是内容。机械首查只在 GitHub Actions 运行。
命令：`python scripts/ste-lint-zh.py <文件>`。
禁止在本机运行此检查。

## Workspace cloud rules (verbatim)

- Do not run local builds, tests, benchmarks, emulators, or native compilation.
- Do not run dependency installation, SDK installation, or dependency restore.
- Do not download build artifacts, installers, SDKs, or build caches to this workspace.
- Do not run Flutter, Dart, Gradle, CMake, Ninja, Xcode, Hvigor, or package-manager commands that generate output.
- Read and edit source locally. Inspect Git metadata and text without creating build or test outputs.
- Run validation through the repository's GitHub Actions workflows. Read results through GitHub API or log output.
- Keep artifacts on GitHub. Record immutable source revisions, run IDs, job conclusions, checksums, and signing limitations in Trellis.
- Keep durable Trellis tasks, specs, research, journals, and project instructions in version control. Keep local runtime/session state and secrets ignored.
- Use GitHub as the sole remote for migrated clones. Check both fetch and push URLs.
- Preserve another agent's work. Coordinate repository ownership and handoff through Herdr.
- Do not delete shared WSL distributions or old source workspaces without the owning coordinators' preservation decision.
- Folder names follow GitHub repository names. Shared core is `qflistudio-core`; its Dart package name remains `qfli_studio_core`.
