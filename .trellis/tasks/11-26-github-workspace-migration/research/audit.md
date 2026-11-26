# Migration planning audit

Audit date: 2026-11-26. Source scope: D:/MyNewProjects/qfli_go. Target: E:/MyNewProjects/QFLIProjects/qflistudio-go. Four existing Herdr Pi agents used gpt-6.1-sol and returned reports through Herdr. No local build/test/install or binary artifact download was performed. The coordinator wrote planning artifacts only; the branch worker refreshed remote metadata without pruning.

## 1. Live branch and remote evidence

| Key | Exact commit |
| --- | --- |
| A | 82e17af4233e3aa2c6dd8eac2cb3f808f0f20a4f |
| B | e5eb5d631639a65c31da0e8fad964ec631de7771 |
| M | c5cab3d2541b77f3a584dc024d1245a1576c5e68 |
| C | ca8b5a4f8203bf8db3b22d069024f6187ebbc83f |
| H | f279134c0525ca704f5ae8ea122ce27e76a2e24b |

Source main and GitHub main are M. Source ci/app-packages and GitHub ci/app-packages are H. Live heads on CNB, GitCode, GitLab and Gitee are main=A, fix/go-release-integrity=A and feat/go-offline-ide=B. GitHub/CNB/GitCode/GitLab default HEAD points to main; Gitee default HEAD points to fix/go-release-integrity, also A.

All five live inventories succeeded at 18:22:06-18:22:08 +08:00. All-head fetches completed at 18:23:10-18:23:20. GitLab had one TLS handshake failure, then its single retry succeeded. No unresolved read/fetch blocker remains. Push access and GitLab's SSH push endpoint were not tested. The worker disabled prompts, used 45-second process limits and at most two attempts. Temporary promisor/filter configuration added by the audit was removed to restore the previous configuration.

A is B's parent. A -> B -> ... -> M -> C -> H is linear. A is 17 commits behind main and B is 16 behind main. main...HEAD has 0 main-only and 2 HEAD-only commits. C adds the application package workflow; H fixes Flutter downloads/Android registrant generation. Both are already on GitHub. git rev-list --all --not HEAD and git rev-list --branches --not --remotes were empty. Therefore older mirror branches need no merge/cherry-pick: their contents are already included. Recheck live refs before implementing the fast-forward from M to reviewed H/successors.

One worktree was found. The repository is not shallow. No tags, stashes, gitlinks/submodules, root .gitmodules, replace/notes/original refs were found. HEAD tree is 71fd8e093dca51a7b8f32a1492449840d9d6c5d2. Source is dirty: the worker observed 14 tracked unstaged entries and 15 untracked short-status entries including concurrent planning work. These are status entries, not file counts. Staged differences were empty; index SHA256 remained 398873bb91ba40c3861561adce174825a3346f49b73ddef3c03d796426b3170c.

Source: branch researcher w5V:p2. A provider concurrency error occurred after the audit; same-model retry was requested, and the evidence report arrived without model downgrade.

## 2. Portable project knowledge and existing changes

The portability worker counted 1,821 indexed .trellis paths, 85 visible untracked paths and 60 ignored paths at its observation. Portable untracked knowledge includes 22 specs, workflow.md, PROJECT_STATUS.md, 28 Python scripts, agents/check.md and agents/implement.md, config.yaml, workspace/index.md, task/archive records and management baselines. AGENTS.md is tracked but its referenced workflow/spec/scripts are not all present in HEAD. Review and include this knowledge.

All 46 .agents/skills files are currently ignored by /.agents/. Review and track the shared skill tree so a fresh clone includes its instructions. The eight tracked .codex integration files depend on this context. Do not blanket-include other ignored agent templates or raw sessions. Keep .trellis/.developer, .runtime, .current-task, .ralph-state.json, caches, temp/conflict files and backups excluded. Review .trellis/.version and .template-hashes.json as portable management baselines. Set session_auto_commit=false explicitly during implementation to prevent archive/journal operations silently staging shared edits.

All six deleted 11-17-app-package-ci files have archive/2026-11 replacements. prd.md/design.md match bytes; context JSONL matches after CRLF normalization. implement.md adds actual run evidence and local-only/device caveats. task.json semantically changes status, completion date and branch. Preserve the archive transition and intentional evidence updates. The record has irregular CRCRLF formatting; do not confuse it with content changes. The newer independent CI audit below confirms helper tests actually ran in the latest package jobs, so retain the distinction between historical local evidence and hosted evidence.

Sixteen archived JSONL references point to nine pre-archive paths. All targets exist under archive/2026-10. Repair only stale task prefixes for 10-01-go-platform-support (apple-review.md, validation.md), 10-09-terminal-flow-pi (pi-audit.md, validation.md), and 10-12-go-curriculum-pi (prd.md, design.md, implement.md, research/content-audit.md, research/curriculum-map.md). Active task contexts had no missing targets in this audit.

Five tracked libqfli_go_runtime.so files total 110,373,932 bytes: Android arm64-v8a/armeabi-v7a/x86_64 and OHOS arm64-v8a/x86_64. Both OHOS libraries are already ignored but still tracked. Replace their consumers with source-built cloud artifacts before removing them from the future Git index. Do not rewrite history. Six generated Flutter registrant/CMake scaffold files require a separate generation-contract decision; do not blanket-remove them.

Sixteen tracked stdout/stderr binary captures under the offline-IDE research directories need classification as historical evidence. Trellis research includes 1,045 JSON, 429 Markdown, 196 Go and 36 Python files; it is not a disposable build directory. Existing task/journal edits are preservation inputs, not permission to close incomplete feature work.

Source: portability researcher w5V:p3.

## 3. Credential configuration finding

Tracked ohos/build-profile.json5 has nonempty literal keyPassword/storePassword fields at lines 10/14 and 23/27, plus machine-specific certificate/profile/container paths. No matching credential-container files were found in the Git index. Secret values were not included in the reports.

Before any new publication, replace password literals and machine paths with a sanitized default and cloud-only signing injection. If the literals are real credentials, their owner must rotate them because removing the current file values does not revoke historical exposure. Do not copy local keystores into Git, task files or artifacts. Do not print/request their contents. This does not authorize history rewrite or unrelated account changes.

Source: portability researcher w5V:p3. Repository metadata independently confirms the repository is public, default branch main and repository Actions secret/variable counts are both zero.

## 4. GitHub CI evidence

Both latest audited workflows ran at H on 2026-11-24:

- Native runtime run 45484027361 (#6): failure. Source job failed; five native build jobs succeeded.
- App packages run 45484027345 (#2): success, seven jobs: Android, OHOS, Linux x64, Windows x64, iOS arm64, macOS arm64 and macOS x64.

Native failing tests: TestDebugOpaqueCallbackCreatedByMainCalledByWorker (debugger_test.go:574, goroutine event missing opaqueNativeBoundary) and TestDebugRetainedNativeArgumentAfterRegistrarExit/returns (nil pointer). The latter stack traverses Yaegi interp.isInterfaceSrc(type.go:2477), isInterface(type.go:2485), itype.concrete(type.go:1369), or(op.go:608), Debugger.SetBreakpoints(debugger.go:630), and newNativeProvenanceDebugger(native_callback_provenance_test.go:100). Nil expression-type handling during breakpoint inspection is a hypothesis requiring implementation-time confirmation. Similar failures occur in runs #4/#5. Go vet passes. The native artifact helper suite reported 56 passed and one skipped.

The native workflow produces Android, OHOS (arm64/x64), macOS universal, iOS device and iOS simulator artifacts. It has no standalone Windows/Linux native artifact jobs. Native source tests run on Ubuntu only. App helper tests reported 45 per job with a Windows-only skip. Neither workflow currently executes Flutter analyze/test or device integration tests. App manifests correctly report runtimeTests/deviceTests as not_run.

Current workflows trigger by path-filtered push or manual dispatch, not pull request or release. Branch-protection API returned 404. There are no repository Actions secrets or variables. These facts do not prove organization/environment credentials exist or do not exist; signed execution still needs an explicit input audit.

Android/OHOS application jobs consume tracked prebuilt native libraries. Windows/Linux/macOS/iOS app jobs compile native source. Use same-source native job outputs or in-job builds for mobile and validate the source SHA, manifest hashes, ABI inventory and exports. Existing package ELF and asset-byte checks must remain intact.

Current outputs are debug-key APKs, unsigned IPA/HAP, Windows ZIP, Linux tar.gz and macOS tar.gz containing an ad-hoc-signed non-notarized app. There are no Setup/MSI/MSIX, DEB/RPM/AppImage, DMG/PKG, signed-release/provisioning or GitHub Release workflows. Artifacts expire after 14 days. Existing success proves build/structural validation only.

Pinned inputs include Go 1.27.1, Flutter-OH tag/commit/tooling/engine, native OHOS SDK checksum/custom Go and repackaged app OHOS SDK checksum. Native Android NDK is 28.2.13676358; app Android does not explicitly pin NDK. Windows MSYS2 uses update=true. Prior Android registrant and macOS download failures were fixed/recovered in H; do not regress them.

Source: CI researcher w5V:p4, corroborated by current workflow/helper/docs inspection. No workflow was dispatched in planning and no binary artifact was downloaded.

## 5. Source graph and target coordination

pubspec.yaml:13-14 and :22-23 (also pubspec.lock) use ../qfli_studio_core and its vendor/re_editor. Current CI intentionally checks the pinned core into qfli_studio_core. The new physical target sibling is named qflistudio-core. No sibling repository was edited. Core coordinator w63:p1 confirmed canonical repository azurekiln2333/qflistudio-core, target sibling E:/MyNewProjects/QFLIProjects/qflistudio-core, and Go paths ../qflistudio-core plus ../qflistudio-core/vendor/re_editor. Package/import remains qfli_studio_core. No alias or junction is needed. Tested baseline 476a30acee21dc486ee2849dd8064a7be665e4d5 with core-check run 45656065902; final migration SHA is pending.

Go app CI currently pins core 573d1b6eecf1c2b392ad753264a5a09f62f8335e. Do not silently upgrade the pin based only on another repository's latest main. Any path or revision transition needs matching checkout/helper/lock updates and cloud validation.

Target w6K:p1 explicitly acknowledged its cwd E:/MyNewProjects/QFLIProjects/qflistudio-go and relayed the cloud-only/hold notice to all four target Pi panes. All four acknowledged and stood by. No target tasks, source changes, builds/tests, installs, SDK setup or artifact downloads were performed by that coordination. This is an interim hold, not the final cutover acknowledgment.

Target directory and inspected parents were ordinary directories; the target had zero immediate children including hidden files. It is not yet a Git repository. Capacity and permissions still need an implementation-time check. Recheck emptiness and live GitHub ref immediately before clone.

## 6. Storage inventory and cleanup holds

A targeted scan at 18:21:26-18:21:28 +08:00 measured 23 selected paths, skipped 15 reparse points and reported zero scan errors. Total logical file lengths: 7,797,485,678 bytes (~7.26 GiB). This is a partial inventory, not allocated space or a guaranteed reclaim amount.

| Source-relative path | Logical bytes |
| --- | ---: |
| build | 2,926,586,453 |
| native/build | 2,238,486,591 |
| .dart_tool | 1,051,252,201 |
| .artifacts | 665,870,019 |
| tool/go_curriculum/.gocache | 323,309,460 |
| ohos/entry/build | 322,339,755 |
| ohos/entry/libs | 69,827,652 |
| android/app/src/main/jniLibs | 65,891,202 |
| ohos/build | 47,673,975 |
| ohos/oh_modules | 36,097,111 |
| native/go_runtime/go_runtime.exe | 29,588,992 |
| ohos/.hvigor | 13,596,448 |
| android/.gradle | 6,678,727 |
| android/build | 134,937 |
| tool/go_curriculum/__pycache__ | 129,407 |
| tool/__pycache__ | 19,897 |

Small ephemeral paths account for the remainder. Link targets were not followed, measured or classified. Global SDK/Go/Pub/Gradle caches and unrelated disks were not scanned.

Candidate generated leaves, subject to final ownership/preservation checks: .dart_tool, tool/go_curriculum/.gocache, native/build/go-cache-windows (683,430,617 bytes), native/build/go-cache-linux (177,642,406), native/build/ohos-go-cache (345,161,474), android/.gradle, android/.kotlin, android/build, ohos/.hvigor, native/go_runtime/go_runtime.exe and the two Python cache directories. They were not tracked, but ignore/untracked status alone does not establish safe deletion.

Mandatory holds:

- build/ci_watch.py (4,575 bytes) is ignored Python source. Coordinator read-back shows a GitHub Actions polling helper that writes a report and fixes the branch to ci/app-packages. Preserve/refactor its unique logic before deleting build.
- native/build/verify_linux_sdk.py (2,706 bytes) is ignored Python source. Coordinator read-back shows a Linux SDK/native test harness that creates fixtures/cache/output. Preserve its source as historical or cloud-only tooling; do not execute locally.
- No preexisting references to those two helpers were found in the searched tool/scripts/docs/workflow/Trellis text except this new migration plan.
- native/build contains evidence JSON/screenshots, SDK trees, an OHOS Go port, GOPATH and fixture source. Patches/uniqueness are not yet classified.
- .artifacts/release-integrity contains about 652.9 MB of package copies and possible unique reports/manifests/screenshots. Similar sizes are not proof of duplicate hashes. Preserve portable evidence before cleanup.
- Tracked mobile libraries, native/go_runtime/vendor (358 tracked files), testdata, curriculum source/evidence, assets, platform source, Trellis history and Codex instructions are not disposable caches.

No deletion, compaction, clone or guest execution occurred.

## 7. WSL registration evidence

All five registered distributions were Stopped, version 2. Registry BasePath establishes registration location, not exclusive data ownership.

| Distribution | Registry BasePath | Disk filename |
| --- | --- | --- |
| Ubuntu | D:/WindowsExt/Subsystem/Ubuntu/Ubuntu_2204.1.7.0_x64 | unset/unknown |
| qfli-terminal-test | D:/MyNewProjects/qflistudio/.artifacts/terminal-runtime-test/ubuntu | ext4.vhdx |
| qfli-terminal-al3-clean | D:/MyNewProjects/qflistudio/.artifacts/terminal-runtime-test/al3-clean | ext4.vhdx |
| qfli-terminal-al3-test | D:/MyNewProjects/qflistudio/.artifacts/terminal-runtime-test/al3 | ext4.vhdx |
| qfli-java-build | D:/MyNewProjects/qfli_java/build/wsl/qfli-java-build | ext4.vhdx |

No registration lies inside qfli_go. Do not delete/unregister these from the Go task. VHDX existence, allocation, guest source and shared ownership are unverified. Coordinate terminal/Java/generic Ubuntu ownership through their responsible Herdr agents before any machine-wide cleanup. Do not start/mount/export a guest merely to satisfy this source migration audit.

Source for storage/WSL/cutover evidence: researcher w5V:p5.

## 8. Implementation gates

Role-policy clarification, 2026-11-27: w5V role IDs in the follow-up below apply
only to the pre-handoff source migration. After verified Herdr handoff, target
Codex assigns its own workers and Git executor; source pane IDs do not govern
target work. Prefer gpt-6.1-sol; on model limits use bounded retries, then context
compaction/new sessions, then deepseek-v4.1-flash only as the final fallback after
those recovery options fail. Dated model/agent observations above remain history.

Planning follow-up, 2026-11-27: the user approved the final plan through Claude w5V:p6; the exact approval is recorded in ../prd.md. All implementation and Git execution now belong to Pi with gpt-6.1-sol. Coordinator w5V:p1 assigns, reviews and starts tasks without implementing. Workers report only to w5V:p1. The audit facts above remain the dated 2026-11-26 snapshot, not refreshed execution evidence. The core sibling is confirmed as ../qflistudio-core; tested baseline 476a30acee21dc486ee2849dd8064a7be665e4d5 and core-check run 45656065902 are unchanged. The core owner reconfirmed that this is still current main and that core-check 45656065902 succeeded. The final coordinated core migration SHA does not exist yet; do not invent it.

1. Activation follow-up, 2026-11-27: independent reviewer w5V:p2 issued final review PASS after the known metadata corrections. Coordinator w5V:p1 confirmed task.py start succeeded for 11-26-go-github-preservation and assigned implementation. That child is in_progress; preserve all other lifecycle states and acceptance gates. w5V:p2 alone mutates Git index/refs under explicit sequenced instructions from w5V:p1.
2. The assigned Pi signing/CI owner sanitizes tracked OHOS configuration before the preservation checkpoint or any new publication. Review all portable/ignored source before explicit-path staging by the Pi Git executor.
3. Replace tracked runtime consumers before removing libraries from tracking.
4. Fix and run cloud checks before claiming six-platform readiness.
5. Finish all progress/evidence commits before the final target equality check.
6. Obtain a final target Codex acknowledgment distinct from the hold notice.
7. Keep shared WSL and unclassified local data intact until ownership/preservation is established.
