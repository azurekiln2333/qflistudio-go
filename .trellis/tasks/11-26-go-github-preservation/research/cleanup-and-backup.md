# Scoped cleanup and backup research

Date: 2026-11-27. Scope: `D:/MyNewProjects/qfli_go`. Ownership: this report only. The user authorized one bounded relocation and private held-original copies under the exact backup root below. No project tool or archived code ran. No WSL distribution was started. No Git state or target workspace was changed.

## Decision summary

- The user explicitly authorized `D:/MyNewProjects/_migration-backup/qflistudio-go-20261127/` as a private local backup root. The root was absent at preflight and was created only after collision, volume, and access checks.
- Eight ignored, wholly generated leaves passed bounded preflight checks and were relocated by same-volume native directory moves. Two generated leaves were retained because Git does not classify them as ignored.
- The relocated batch was 2,601,206,270 logical bytes across 18,352 files. Each leaf's inventory matched before and after relocation. The backup remains on D:, so it does not protect against D: drive failure.
- Two raw curriculum originals were copied, not moved, to the private `held-originals/` subfolder. Source files remain in place. No contents or secret values were disclosed.
- The existing reviewed archive at `.trellis/tasks/11-26-go-github-preservation/research/ignored-source/` already contains 49 snapshots totaling 6,817,493 bytes (47 exact snapshots and two redacted derivatives). Its manifest and hashes are the preservation record; do not make a redundant second copy. Raw curriculum originals, unreviewed device/CI data, SDK trees, binary packages, and unlisted artifact content remain on HOLD.

## Bounded relocation batch

The table records the ten-cache preflight list. Eight leaves moved after checks. Two leaves remain in place because Git did not classify them as ignored. Sizes below are refreshed logical file lengths, not allocated disk usage. Relative paths are preserved beneath the backup root.

| Source path | Logical bytes | Disposition |
| --- | ---: | --- |
| `.dart_tool/` | 1,051,252,201 | 320 files; **moved**. Ignored; no matching process path, reparse point, or nested repository. |
| `tool/go_curriculum/.gocache/` | 323,309,460 | 3,771 files; **moved**. Ignored; no matching process path, reparse point, or nested repository. |
| `native/build/go-cache-windows/` | 683,430,617 | 7,436 files; **moved**. Ignored; no matching process path, reparse point, or nested repository. |
| `native/build/go-cache-linux/` | 177,642,406 | 3,621 files; **moved**. Ignored; no matching process path, reparse point, or nested repository. |
| `native/build/ohos-go-cache/` | 345,161,474 | 3,154 files; **moved**. Ignored; no matching process path, reparse point, or nested repository. |
| `ohos/.hvigor/` | 13,596,448 | 33 files; **moved**. Ignored; no matching process path, reparse point, or nested repository. |
| `android/.gradle/` | 6,678,727 | 16 files; **moved**. Ignored; no matching process path, reparse point, or nested repository. |
| `android/build/` | 134,937 | 1 file; **moved**. Ignored; no matching process path, reparse point, or nested repository. |
| `tool/__pycache__/` | 19,897 | 1 file; **HOLD**. Not ignored by Git; retained in place. |
| `tool/go_curriculum/__pycache__/` | 129,407 | 6 files; **HOLD**. Not ignored by Git; retained in place. |
| **Moved total** | **2,601,206,270** | **18,352 files across eight leaves; 2.423 GiB** |

The eight moved leaves remain available under the private backup root. The two HOLD leaves remain at their original paths. The move used directory renames on the same volume. No destination existed before the move, and no destination was replaced. A matching path name does not prove that generated content is complete or regenerable.

### Separate hold: generated outputs and workspace dependencies

Do not add these to the first batch without path-owner review. The audit measured the following additional leaves:

| Source path | Logical bytes | Reason to hold |
| --- | ---: | --- |
| `ohos/entry/build/` | 322,339,755 | Platform build output; local rebuild and consumption state is unknown. |
| `ohos/build/` | 47,673,975 | Build tree may include locally meaningful content. |
| `ohos/oh_modules/` | 36,097,111 | Installed dependencies; removal can disrupt the local workspace. |
| `ohos/entry/libs/` | 69,827,652 | Contents and consumer relationship were not resolved. |
| `android/app/src/main/jniLibs/` | 65,891,202 | Tracked runtime libraries; retain until cloud source-built consumers replace them and the Git owner approves a tracking change. |
| `native/go_runtime/go_runtime.exe` | 29,588,992 | Runtime binary; its live consumers and replacement path are unresolved. |
| `.artifacts/` | 665,870,019 | Unique research, package, report, or device evidence may be present; the ignored-source disposition defaults unlisted content to HOLD. |
| `build/` | 2,926,586,453 | Contains the unique `build/ci_watch.py` helper and unclassified output. Never remove this parent tree as a unit. |
| `native/build/` | 2,238,486,591 | Contains `native/build/verify_linux_sdk.py`, SDK trees, source/evidence, and caches. Never remove this parent tree as a unit. |

The 15 reparse points skipped by the earlier bounded scan were not traversed or measured. Their targets remain out of scope. The scan total of 7,797,485,678 bytes across 23 selected paths is a partial logical-size inventory, not a complete tree size or reclaim estimate.

## Existing backup and disposition evidence

`research/ignored-source/provenance.json` records 49 explicit source/destination pairs, byte counts, hashes, review scope, and copy status. `dispositions.json` records three duplicates already present in inspected reachable local Git history, 27 individual HOLDs, five grouped scope holds, exclusions, and `cleanupAuthorized: false`. The archive README says all source originals remain at their source paths and nothing there authorizes cleanup.

Already-preserved ignored helpers are inert text snapshots:

- `build/ci_watch.py` → `research/ignored-source/historical/build/ci_watch.py.txt` (4,575 bytes; hash recorded in `provenance.json`).
- `native/build/verify_linux_sdk.py` → `research/ignored-source/historical/native/build/verify_linux_sdk.py.txt` (2,706 bytes; hash recorded in `provenance.json`).

Do not execute these helpers. The exact historical copies preserve source while the originals remain in place. The archive does not clear the rest of either parent directory.

Keep the following on HOLD and do not copy them to a general backup or publish them based on this report:

- `.artifacts/release-integrity/go-content-backup/original-examples.json` and `original-tutorials.json`: raw curriculum originals. Only reviewed redacted derivatives are in the task archive.
- Unreviewed `.artifacts/` originals, raw logs/screenshots/UI XML, raw CI/API records, device selectors, and unlisted files. Their individual dispositions are in `research/ignored-source/dispositions.json`; unlisted content stays held by default.
- `native/build/go-sdk-1.27.1/`, `native/build/go-linux-1.27.1/`, and `native/build/ohos-go-f2cb44316b789bc12d0b5fd562d853f6fec3ab28/`: upstream SDK/local modification status is incomplete or requires owner review.
- Signing credentials, keystores, local machine signing paths, `.env`/credential material, `.trellis/.developer` identity file, `.trellis/.runtime/`, `.trellis/.current-task`, `.trellis/.ralph-state.json`, `.git/`, caches not listed above, and reparse targets. Do not inspect secret values or include them in a backup manifest.
- Tracked native libraries, vendored source, test data, task history, curriculum source, assets, and platform source. They are not disposable caches.

## Runtime and registered WSL distributions

At this report's metadata check, a process-name/path query found no Go, Dart/Flutter, Java, Gradle, Hvigor, or OHPM process and no process executable rooted under this repository. A separate `wsl.exe --list --verbose` query showed all five registered distributions as **Stopped**, WSL version 2. No guest was started, mounted, exported, or inspected. This is a point-in-time observation; it does not establish that an editor, watcher, file handle, service, or external process is absent. Treat the Go workspace as live and preserve all source paths unless their owner authorizes cleanup.

The registered BasePaths below come from the prior audit. They are registration locations, not proof of exclusive ownership or proof that the VHDX exists. Distribution owners were not identified in the available records.

| Registered name | Registered BasePath | Disk filename in audit | Owner known? |
| --- | --- | --- | --- |
| `Ubuntu` | `D:/WindowsExt/Subsystem/Ubuntu/Ubuntu_2204.1.7.0_x64` | Unknown | No; general distribution. |
| `qfli-terminal-test` | `D:/MyNewProjects/qflistudio/.artifacts/terminal-runtime-test/ubuntu` | `ext4.vhdx` | No; coordinate with the terminal workspace owner. |
| `qfli-terminal-al3-clean` | `D:/MyNewProjects/qflistudio/.artifacts/terminal-runtime-test/al3-clean` | `ext4.vhdx` | No; coordinate with the terminal workspace owner. |
| `qfli-terminal-al3-test` | `D:/MyNewProjects/qflistudio/.artifacts/terminal-runtime-test/al3` | `ext4.vhdx` | No; coordinate with the terminal workspace owner. |
| `qfli-java-build` | `D:/MyNewProjects/qfli_java/build/wsl/qfli-java-build` | `ext4.vhdx` | No; coordinate with the Java workspace owner. |

None of these BasePaths is inside `qfli_go`. Do not back up, unregister, compact, move, or delete these distributions or their VHDX files as part of Go cleanup. Their guest data, allocated sizes, actual owners, and any shared-use relationship remain unknown. Do not infer ownership from the registration name or directory path.

## Reviewable procedure and completed operation

1. **Authorize the exact root.** The user authorized `D:/MyNewProjects/_migration-backup/qflistudio-go-20261127/`. The root was absent before the operation. Its parent and the source were on D:, so same-volume renames were possible.
2. **Preflight source leaves.** Each candidate had zero tracked entries, zero nested repositories, and zero reparse points. Process command lines and executable paths showed no reference to the ten leaves. Native open-file inspection was unavailable, so the operation treated any move failure as a HOLD. The two non-ignored leaves were held before moving.
3. **Secure the destination.** The new root was created with inheritance disabled and access restricted to the current execution identity. Broad inherited access was absent in the post-create check. The report omits identity and ACL principal literals.
4. **Relocate only approved leaves.** The eight ignored leaves moved with absolute-source and absolute-destination native directory renames. Parents were created under the new root. No destination existed before each move. No source leaf was copied over, deleted separately, or replaced.
5. **Copy held originals only.** The two raw curriculum originals were copied to the private nonpublished `held-originals/` subtree. Their source paths remain unchanged. Source and destination sizes and hashes matched. Contents were not printed or included in this report.
6. **Verify inventories.** Pre- and post-move file counts and logical byte totals matched for every moved leaf. The destination root contains only the eight moved relative paths and the two held-original copies. The two non-ignored cache leaves remain at their source paths.
7. **Do not perform further cleanup.** No deletion is authorized by this report. Keep tracked paths, parent trees, unclassified output, SDKs, dependency installs, runtime state, credentials, reparse points, WSL data, and all other HOLDs in place.

## Unknowns and limits

- The native open-file inspection utility was unavailable. No candidate move failed, but an external handle that permits rename cannot be ruled out from metadata alone.
- The process query found no candidate reference. It cannot rule out an editor, watcher, scheduled task, or external runtime that does not expose a matching path.
- The eight moved leaves had no reparse points or nested repositories. The earlier 15 reparse points elsewhere in the workspace remain untraversed and unresolved.
- The moved cache contents were not printed or committed. The private backup root is local and nonpublished. No credentials were copied.
- WSL VHDX size, guest contents, and owners remain unknown. No WSL guest was started or traversed.

## Evidence and handoff

- Primary audit: `.trellis/tasks/11-26-github-workspace-migration/research/audit.md`, especially storage, WSL, and cleanup-hold sections.
- Existing dispositions: `.trellis/tasks/11-26-go-github-preservation/research/ignored-source/{README.md,dispositions.json,provenance.json,FILES.sha256}`.
- Preservation checkpoint `3783588ba6779950a7ee5da89600976255149021` was historical report context, not a before/after relocation measurement. The coordinator observed main at `db831aebebfb3ede327ab7bd12a62a119b298f2e` during relocation. This worker performed no Git mutations.
- Backup root: `D:/MyNewProjects/_migration-backup/qflistudio-go-20261127/`. The eight moved leaves and two held-original copies are local, private, and not published by this task.
- This report records bounded native file metadata, ACL/access checks without principal literals, and the authorized relocation. No project, build, test, install, archived-code execution, or local lint command ran.
