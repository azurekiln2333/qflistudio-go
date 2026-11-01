# Integration execution plan

1. After approval/start, finalize the shared file/API owner map with the live C/Dart/Java/Python/Lua and remaining product coordinators. Record proposed/accepted ownership explicitly; never assume a silent coordinator accepted a claim.
2. Integrate shared language UI/highlighting and explorer/workspace changes under their declared owners. Review existing file-tree restore gap; require real sidebar disposal/recreation regression.
3. Integrate optional analysis/debug/panel APIs, then product adapters. Run constructor/backward-compatibility and actual widget/source-range lifecycle checks after each shared contract change.
4. Collect all product content inventories/current runtime evidence. Audit every item and requested feature against parent acceptance; request missing exact artifacts from product owners.
5. Run full affected core/product analyze/tests and builds against the final shared revision. Recheck actual OHOS target availability; coordinate device use if a target appears.
6. Review all staged changes/specs and separate pre-existing signing/icons/generated files. Commit with conventional messages and perform normal configured pushes; record resulting SHAs.
7. Archive independently proven children. Complete the umbrella only when every requirement for every applicable product is proven, otherwise keep the precise remaining work in the ledger.

Dependency order: common models before adapters; Go/native repairs before full curriculum target runs; final shared revision before final all-product suites; actual target before OHOS execution claims. Parent implementation plan supplies commands, gates and recovery rules.

## Commit sweep

Swept 201 uncommitted paths on feat/go-offline-ide, grouped by theme.

| Commit | Theme |
| --- | --- |
| `893ba6c` feat(runtime): add analysis, debugging and project environments | native/go_runtime |
| `47edbcc` feat(ide): add Go analysis, debugger and tools to the offline IDE | lib + tests |
| `bad80a7` feat(curriculum): expand the Go course samples and topics | tool/go_curriculum + assets |
| `866f67e` build(platform): link the Go runtime on every target | .so libs, platform build files, icons |
| `39635b7` test(integration): accept the Go IDE on a real device | integration_test |
| `248bacd` docs(task): archive the Go IDE research and acceptance notes | task dirs, LICENSE, scripts |

Tracked binaries committed, with sizes:

- android jniLibs: arm64-v8a 20.39 MB, armeabi-v7a 20.52 MB, x86_64 21.92 MB
- ohos entry/libs: arm64-v8a 20.44 MB, x86_64 21.99 MB
- ohos icons: app_icon.png and icon.png, 0.43 MB each

Skipped, and why:

- 26 *.log files and 3 *.pyc files under the task research
  directories. Logs and bytecode are build and run output.
- 16 *.bin files under c580-go-20261026-controls and
  go-native-next-20261026-01. They are captured stdout and stderr from
  a test run, not source. They remain staged, not committed.

