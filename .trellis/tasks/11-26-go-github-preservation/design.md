# Design

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

Assigned Pi workers own implementation. w5V:p2 is the sole Git executor. It stages, commits, merges and pushes only on explicit sequenced instructions from coordinator w5V:p1. Other workers do not mutate the index or refs. Coordinator w5V:p1 assigns disjoint ownership, reviews results and starts eligible tasks; it does not implement or execute Git operations. Workers report only to w5V:p1 through Herdr, never to w5V:p6. Prefer gpt-6.1-sol; on model limits use bounded retries, then compaction/new sessions, then deepseek-v4.1-flash only as the final fallback after those recovery options fail. Record the baseline HEAD, tree and dirty state. Query live heads and fetch without pruning. Use ancestry and unique-commit diffs to choose fast-forward or merge. Do not infer current remote state from stale tracking refs.

Audit .trellis and ignored instructions against existing hooks and context manifests. Review deleted app-package task files against archived equivalents. Preserve history and unfinished criteria. Track reviewed .agents skills needed by project agents. Repair only the nine stale archived-context paths. Set session_auto_commit=false. Require the assigned Pi signing/CI owner to sanitize OHOS signing configuration before the preservation checkpoint or any new publication. After review, the Pi Git executor stages explicit approved paths. Generated mobile binaries leave tracking only after cloud consumers can regenerate them. Preserve ignored build/ci_watch.py and native/build/verify_linux_sdk.py. Review reports/toolchain modifications before cleanup.

Record original branch SHAs, remote availability, staged paths and canonical GitHub commit/tree. Never force-push or rewrite history. Rollback uses additive commits and the retained source workspace.
