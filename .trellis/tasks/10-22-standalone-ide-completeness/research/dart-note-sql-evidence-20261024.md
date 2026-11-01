# Dart, Note and SQL evidence audit — 2026-10-24

Active task: `.trellis/tasks/10-22-go-curriculum-ohos`.

This Go-owned report records a read-only audit of existing Dart, Note and SQL source and evidence. It does not change sibling products, shared core, `acceptance.md` or their acceptance decisions. Artifact SHA256 values below were recomputed during the audit; recorded executions are historical evidence, not new executions performed by this auditor. Persistence changes only this report. Host/device reservation: none; the coordinator owns execution and grants.

## Findings

None of these three products has captured exhaustive current installed-OHOS acceptance. Host runtime, host renderer, package cryptographic verification and installed target execution remain separate evidence scopes.

| Product | Verified original coverage | More than 100 substantive additions | Published core `2f9039a3ba95449679b17257b0313c1ee3644a2c` consumption |
| --- | --- | --- | --- |
| Dart | Windows production-portable original 240/240 tutorial/example programs; this is not an OHOS run or proof that every original exercise was executed. | 180 paired topic drafts, IDs 121–300, remain unpromoted. A's 60 topics and C's 62 topics have complete lesson/example/exercise execution on both host engines. B's 58 topics have complete paired tutorial/example evidence but an incomplete exercise gate. | No named-workspace test or debugger registration was found in the inspected current Dart tests/profile. A historical audit HAP uses older core `daddce27eed1f9389efed0360a0ca954af422da8`. Inheriting a shared capability default does not establish tested consumption. |
| Note | Windows full renderer audit 244/244: 2 baseline cases, 220 examples and 22 lessons, with independent per-item parity clean. | The 220 examples and 22 lessons have exhaustive host renderer evidence. Rendering does not execute fenced programming languages. | Confirmed by the newer actual Note Home named-workspace test 1/1 and full suite 285/285. Before, checked and after core revisions all equal the published revision, with source drift zero. The overall gate still failed analysis and Android compilation. |
| SQL | Original production denominator is 126 topics/372 scripts: SQLite 120 topics/360 scripts and MySQL 6 topics/12 scripts. Actual bundled Windows SQLite passed the original 360; no fresh MySQL 12-script pass or full current OHOS 372-script report was found. | Unshipped 180-topic expansion, IDs 127–306, passed 180 examples plus 360 exercises, 540 scripts total, on actual bundled host SQLite. | Unproven. The last workspace execution used frozen older core `e025805b60435fdedafd33e60082dc660afebe5a` and failed both tests. The corrected fixture remains READY/UNRUN and exercises legacy ProjectHistory multi-root behavior, not a named SavedWorkspace. |

## Dart

The original production-portable report identifies `tom_d4rt 1.229.0+qfli.1; product offline policy and supervisor`, explicitly scopes itself to the host engine rather than OHOS device execution, and records 240 checked/zero failures. Its first and last records are `dart-lesson-001` and `dart-example-120`. It has no top-level execution timestamp; no date is inferred from filesystem metadata.

The new authoring remains outside production aggregation, which is still 120 lessons/120 examples pending the original installed-OHOS gate:

- A, IDs 121–180: 60 substantive topics; 180 separate lesson/example/exercise program slots pass the installed Windows SDK and production portable runner, 360 successful executions in total. The raw report preserves source and actual SDK/portable output for each slot.
- B, IDs 181–238: 58 substantive topics; all 116 tutorial/example entries passed both engines. Four paired reports cover 12/12/22/12 unique programs and 24/24/44/24 paired entries, with zero failures and `targetDeviceVerified:false`. Full standalone exercise solutions are authored. The later all-three-kind run passed IDs 181–198, then SDK processes for 199/exercise and 200/lesson failed with VM out-of-memory; a truncated error stream aborted that run. This does not satisfy the full 58-exercise gate.
- C, IDs 239–300: all 62 topics have six true checks each: lesson, example and exercise on both SDK and production portable engine. The final report contains 62 records, all `ok:true`: 186 SDK plus 186 portable executions, zero failures. This is host evidence.

The current C report supersedes the older `progress.md` statement that lesson 273's async-prefix ordering repair was still in progress. The correct lesson and SDK expectation were retained; synchronous async-prefix/await-order repairs now let lesson 273 pass unchanged. Lesson 282's direct awaited iterable also passes unchanged in the final C matrix. The root still owns combined final asset generation, all-content checks and app integration; batch host passes do not prove a promoted expanded target corpus.

The historical OHOS x64 package build succeeded from `tool/dart_catalog_ohos_audit.dart`, expectedTopics 120, core `daddce27eed1f9389efed0360a0ca954af422da8`, between 2026-10-22T17:15:32.7204166Z and 2026-10-22T17:16:11.4758195Z. The later signature report, verified at 2026-10-23T02:09:49.2046943+00:00, explicitly sets both `signatureVerified:true` and `profileVerified:true`. This supersedes the earlier package inspection's false verification fields for cryptographic verification only. The verified HAP remains `deviceVerified:false`.

Verified HAP: `D:/MyNewProjects/qfli_dart/build/dart-audit/dart-catalog-x64-700336efe21b71ac.hap`; SHA256 `700336efe21b71acee178e6f7ad7949e7623f0f7c423fad9d7b930d241307589`; bundle `com.azurekiln.qfli.dart`. SDK signature/profile validity is not installed OS trust or current shared-core consumption.

Open Dart gates: original installed-OHOS baseline; B's complete exercise rerun; combined expanded generation/runtime/app checks; fresh current-source package and device execution; actual named-workspace consumption; final debugger capability/requirement disposition. No current debugger backend registration was found in the inspected profile.

## Note

The exhaustive host renderer report records 244 expected/reported/checkpoint/passed cases, zero failures, 16/16 host audit tests and clean independent per-item parity. Its core revision is older `43d145d1ae649cfa2c8db576cf7a42729cfdcde8`. Platform is Windows; the report's `targetPlatform:android` field is a host configuration and does not prove Android execution. Its expected global rejections include non-OHOS runtime and build/runtime identity mismatch; `accepted:false` and `deviceExecuted:false` are deliberate scope limits.

The newer gate at `build/note-audit/final-20261024T031025Z-5ac8ad2d/` supersedes earlier failure-only workspace/full-suite records:

- Started 2026-10-24T03:10:25.229506+00:00; completed 2026-10-24T03:11:39.301157+00:00; elapsed 74.072916 seconds.
- Exact core before/resolution/format/checked/after: `2f9039a3ba95449679b17257b0313c1ee3644a2c`; source drift zero.
- Actual Note Home named-workspace test: 1/1 PASS. It saves and reopens both document owners after app reconstruction, checking cursor and root expansion restoration and legacy dirty-buffer isolation.
- Full suite: 285/285 PASS. Content validation: 220 examples, 22 lessons, 4 tutorials, no issues.
- Analysis: exit 1 with only four `curly_braces_in_flow_control_structures` infos at `lib/workspace/markdown_workspace.dart:325,342,383` and `lib/workspace/workspace_layout.dart:168` in the captured source.
- Android: exit 1 during actual Android source compilation; stderr points to `tool/verify_android_offline_bridge.ps1:65` and `build/note-android-offline/compile.log`. This is a compilation failure, not a successful Android runtime check. Later source repairs have no fresh captured pass in this report.
- All owned jobs and publisher are terminal/active zero; overall `FAIL_OR_INCOMPLETE`, `accepted:false`, `deviceExecuted:false`.

The named test source remains `D:/MyNewProjects/qfli_note/test/note_named_workspace_test.dart`, SHA256 `7b2f854b8cc6f14a2c6aa7e949f56548cfcbb1f1df94ef3e25ec02869ef68913`.

Open Note gates: fresh clean analysis and Android compiled-handler positive/restored-online negative controls; fresh audit HAP, SDK signature and inspection; actual current OHOS all-244 baseline-first content run; normal production native document IO and persisted grants; physical ARM64 and all-product acceptance. The older host report's workspace/full-suite open items are superseded by the newer 1/1 and 285/285 evidence, while its target/native gates remain open. Note is a Markdown renderer/preview product; its host rendering and fenced-code styling are not executable language runtime or breakpoint-debugger evidence.

## SQL

The corrected original denominator is 372 scripts, not 378: the six MySQL topics each have one exercise, so SQLite contributes 360 and MySQL contributes 12. The original native baseline note records `sqliteExamples=120 sqliteScripts=360 mysqlNotExecuted=6`. It uses the actual Windows bundled SQLite 3.50.0 DLL, SHA256 `12bb8326b9ab400472d4b95596cb343512a10ab2ac6e40620e09df2da2c59f93`. CLI checks and bundled-host checks remain distinct from OHOS bridge/runtime execution.

The expansion machine report was created 2026-10-22T09:04:50.287308+00:00 and explicitly scopes itself to unshipped drafts, host only, not OHOS acceptance. It records 180 examples plus 360 exercises passed, 540 cases, zero failures, using the same bundled SQLite 3.50.0 DLL. Promotion would yield 306 topics/912 scripts, but remains blocked by the required original OHOS gate. Historical signed audit HAP evidence predates the native offline-policy/INTERNET-removal changes and needs replacement; signature/build evidence does not prove installed target execution or production trust.

Three serialized workspace attempts failed both tests. The final actual attempt was handle 40310/PID 12368, exit 1, zero passed/two failed/zero skipped; that historical handle was already released. It used older frozen core `e025805b60435fdedafd33e60082dc660afebe5a`. Real SQLite ownership/Run/current-file assertions in the second case reached the final exception assertion, but the case still failed on a shared defunct focus Element error; reaching those assertions is not a test pass. C's later focused focus-disposal regression passed, but SQL has not captured a fresh corrected-core consumer run.

The corrected fixture remains `D:/MyNewProjects/qfli_sql/test/sql_workspace_integration_test.dart`, SHA256 `60c73c73c062153fb590951d6f7197a5b3cbcc73bc3c5e0f1441cbbe48b110fd`, READY/UNRUN. It retains actual native database/save/isolation assertions and checks A's restored nested file plus B's independently collapsed root after drawer reopen and page reconstruction. The fixture's own report explicitly says it covers the actual SQL profile's legacy ProjectHistory membership branch and does not attach a main-studio SavedWorkspace. No named/saved-workspace references were found in the inspected current SQL tests/profile. This is a separate gap from the older focus fix.

Open SQL gates: fresh exact-current-core consumer run preserving all failure assertions; actual named-workspace coverage; original current OHOS 372-script run including real MySQL 12; native stop/root cleanup; fresh source-bound signed/installable artifact and target trust; only then draft promotion and full expanded target execution. SQL query output and plans are real product behavior, but are not breakpoint-debugger evidence; no fake debugger requirement is inferred.

## Artifact identities

All paths are absolute. SHA256 values identify the inspected bytes, not a publication freeze or a new acceptance run.

| Evidence | Path | SHA256 |
| --- | --- | --- |
| Dart original 240 | `D:/MyNewProjects/qfli_dart/.trellis/tasks/10-22-offline-ide-completeness/research/portable-production-baseline.json` | `29dd1e0359b38349ce20c8c9012ee1b03f384f083b7208fedb731ff150ad631a` |
| Dart A 180 program slots | `D:/MyNewProjects/qfli_dart/.dart_tool/expansion-a/results.json` | `671d0233195ea188baef75d5c0d7ff368bd729e8eb89679559b5a43118118c69` |
| Dart B incomplete exercise status | `D:/MyNewProjects/qfli_dart/.trellis/tasks/10-22-offline-ide-completeness/research/expansion-b.md` | `03956366be4ab7ca8770534cc10fda7d7348d3a2d7174f9a5fc6836a93f2def4` |
| Dart C 62 topics, 186 programs per engine | `D:/MyNewProjects/qfli_dart/.dart_tool/expansion_c/final-all.json` | `ff25d8aceb758baa8996bb7036f9ac9e70a46e0021787690c9da65318cdd1a58` |
| Dart historical OHOS x64 build | `D:/MyNewProjects/qfli_dart/build/dart-audit/build-20261022T171532720.json` | `9370d2b88a7ad9988662c0447221dfb4e97197881109078147586a6d2497cff5` |
| Dart later HAP signature/profile verification | `D:/MyNewProjects/qfli_dart/build/dart-audit/verify-20261023T020947782/signature-report.json` | `16061383e03e323e16767328a984493245a361ed804c333e6a1fa9d59d955b17` |
| Note newer named 1/full 285 gate | `D:/MyNewProjects/qfli_note/build/note-audit/final-20261024T031025Z-5ac8ad2d/process-handle-report.json` | `e5850a7f882d39cb237be55e78f27efccd6c01e093db43d10fdc66b54d5e2956` |
| Note newer gate host process log | `D:/MyNewProjects/qfli_note/build/note-audit/final-20261024T031025Z-5ac8ad2d/host-report.json` | `d52c3f0075702c8486287aa9c2e564db26c0ed3d8f9fb0d4c6daec8f167d176c` |
| Note exhaustive 244 host renderer/parity | `D:/MyNewProjects/qfli_note/.trellis/tasks/10-22-offline-note-completeness/research/note-host-audit-evidence-20261024.json` | `33958862b2674779ffc39c2504ff4138c918363c8830c43617d2c9146562bc43` |
| SQL original native baseline record | `D:/MyNewProjects/qfli_sql/.trellis/tasks/10-22-offline-ide-completeness/research/curriculum-native-audit.md` | `8e540acac3a37f3cdb2bb3693abd39250a59cd3162f7033af160c71ba0726737` |
| SQL expanded 540 machine report | `D:/MyNewProjects/qfli_sql/.trellis/tasks/10-22-offline-ide-completeness/research/curriculum-drafts/bundled-host-results.json` | `b023084d0a92f9ab72cf22571432dec12b700fb259d97aa7a79bcdfcb8adf984` |
| SQL failed attempts/current UNRUN status | `D:/MyNewProjects/qfli_sql/.trellis/tasks/10-22-offline-ide-completeness/research/sql-workspace-consumer-check.md` | `9550548f190bab2a7f83c7b87e63a8e36f05d042c9cd7b4e4ba36f081d4e516e` |

## Verification boundary

The audit used existing file/source reads and SHA256 inspection. The documentation step creates only this new Go-owned report. No product runtime, test, SDK, build, format, native, WSL, device, kill/reset, Git mutation or channel-post command was used for this report. Static text verification checks the artifact hashes written here, required scope/correction statements and absence of malformed Markdown/trailing whitespace; it is not application validation.
