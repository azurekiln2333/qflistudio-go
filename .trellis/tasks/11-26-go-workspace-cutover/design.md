# Design

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

Assigned Pi workers own cutover implementation and Git execution after explicit activation. Coordinator w5V:p1 assigns, reviews and starts eligible tasks without implementing. Workers report only to w5V:p1 through Herdr, never to w5V:p6. Prefer gpt-6.1-sol; on model limits use bounded retries, then compaction/new sessions, then deepseek-v4.1-flash only as the final fallback after those recovery options fail. Target and cross-repository coordination stays with w5V:p1.

Recheck E:/MyNewProjects/QFLIProjects/qflistudio-go is empty and not a reparse point immediately before clone. Stop on unexpected files. Clone canonical GitHub main directly with one GitHub origin. Do not copy old .git, caches or binaries. Never run local setup/build/test commands.

Match exact HEAD and tree IDs with source and live GitHub. Inspect staged, tracked and nonignored untracked state. Validate portable task/context paths. Raw byte comparisons must account for .gitattributes and line endings. Record the core URL/revision and canonical sibling ../qflistudio-core, including ../qflistudio-core/vendor/re_editor. The Dart package/import name remains qfli_studio_core.

Finalize/archive only completed task work and commit journal/evidence before the last push and target fast-forward. Recheck both statuses after all writes. Send source/tree/evidence SHAs, CI run IDs, package/signing state, unfinished tasks and cleanup boundaries through observed Herdr panes. Require target acknowledgment.

Cleanup is path-specific and follows preservation. build/ci_watch.py, native/build/verify_linux_sdk.py, toolchain source changes and .artifacts reports require disposition before parent-directory removal. Skip reparse points. Do not blanket git clean or delete shared folders. No WSL registration is under qfli_go; terminal/Java distributions belong to sibling scopes and Ubuntu ownership is unverified. Keep those intact pending owner evidence.

Retain the old source workspace while active panes depend on it. If comparison or acknowledgment fails, keep the source as recovery location and do not overwrite target changes.


Core contract: use https://github.com/azurekiln2333/qflistudio-core.git at final coordinated revision. The confirmed sibling is qflistudio-core. The tested baseline 476a30acee21dc486ee2849dd8064a7be665e4d5 (core-check 45656065902) is provisional. 

Cleanup holds: tracked native libraries, historical test captures, build/ci_watch.py, native/build/verify_linux_sdk.py, native toolchains, .artifacts reports and reparse targets require explicit disposition. Do not blanket-delete parent directories. 
