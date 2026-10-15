> 2026-10-15 SUPERSEDED: this is the historical 10-09 proposal, not a current approval request. The user explicitly authorized implementation and Conventional Commits under parent 10-15-release-integrity-audit on branch fix/go-release-integrity. Native code and rebuilt five-ABI libraries are committed as 4ace2f4; current Dart/delegate/platform evidence is recorded by the parent. Historical 68-test/device figures below are not this round's results. No additional commit approval is pending.
# 待确认的本地提交清单

实现、独立复核、68 项完整 Flutter 测试及 Android / OHOS 真机测试均已完成。正常 APK/HAP 已安装并启动。这里仅等待工作流 Phase 3.4 要求的一次 Git 提交确认。

## 提交顺序

确认后从当前 main 创建 fix/go-terminal-entry，并用 task.py set-branch 更新当前任务分支。现有未提交内容保留在工作区；不 amend、不 push、不合并其他分支。

### 1. fix(go): honor selected entries and simplify run titles

代码和回归测试（10 个文件）：

- lib/go_entry_selector.dart
- lib/go_runner.dart
- lib/native_go_bridge_ffi.dart
- lib/native_go_bridge_stub.dart
- native/go_runtime/runtime.go
- native/go_runtime/runtime_test.go
- test/go_entry_selector_test.dart
- test/go_toolchain_test.dart
- test/go_app_test.dart
- integration_test/go_native_test.dart

本次重建且已验证的运行库（5 个文件，均已被 Git 跟踪）：

- android/app/src/main/jniLibs/arm64-v8a/libqfli_go_runtime.so
- android/app/src/main/jniLibs/armeabi-v7a/libqfli_go_runtime.so
- android/app/src/main/jniLibs/x86_64/libqfli_go_runtime.so
- ohos/entry/libs/arm64-v8a/libqfli_go_runtime.so
- ohos/entry/libs/x86_64/libqfli_go_runtime.so

本任务文档：.trellis/tasks/10-09-terminal-flow-pi/ 下的 PRD、design、implement/check context、任务状态、此提交清单，以及 research/ 下的审查报告、验证报告、基线哈希、校验脚本、真实 TerminalPane 渲染用例和 5 张截图。不会包含其他任务目录。

### 2. chore(task): archive terminal-flow-pi

工作提交完成后，只归档 .trellis/tasks/10-09-terminal-flow-pi/，由 Trellis 脚本生成本任务归档提交。不归档 10-01-content-code-import 或其他任务。

### 3. 本次会话记录

按 trellis-finish-work 记录本次会话及第 1 步工作提交哈希。日志遵守当前仓库忽略规则；不为本任务更改 .gitignore 或强制加入忽略的运行状态文件。

## 本次提交排除的现有修改

以下现有源码和配置全部保留，已用哈希核对未被本次工作改变：

- lib/main.dart
- ohos/build-profile.json5
- ohos/entry/src/main/ets/entryability/EntryAbility.ets
- ohos/entry/src/main/ets/pages/Index.ets
- ohos/entry/src/main/resources/base/profile/main_pages.json
- ohos/entry/src/main/ets/pages/AgreementReader.ets
- test/content_code_import_test.dart
- test/native_startup_test.dart
- .gitattributes
- AGENTS.md

其他不纳入提交的路径：

- .artifacts/（本次原始日志/临时文件和既有任务产物）
- .codex/
- .trellis/tasks/10-01-content-code-import/
- android/app/src/main/jniLibs/arm64-v8a/libqfli_go_runtime.h
- android/app/src/main/jniLibs/armeabi-v7a/libqfli_go_runtime.h
- android/app/src/main/jniLibs/x86_64/libqfli_go_runtime.h
- linux/flutter/generated_plugin_registrant.cc
- linux/flutter/generated_plugin_registrant.h
- macos/Flutter/GeneratedPluginRegistrant.swift
- windows/flutter/generated_plugin_registrant.cc
- windows/flutter/generated_plugin_registrant.h
- 构建目录、SDK 缓存、已忽略的本地 .trellis/spec/ 规范及其他本地工具状态。

Java 和共享核心的已有改动属于其他工作区，本任务未修改或提交它们。

## 验证依据

详见 research/validation.md。完整 Flutter 68/68；Android 与 OHOS 真机各 3/3；共享终端/手势 22 项；终端渲染 5 种尺寸/主题；native test/vet/analyze 均通过。五种新库及最终 APK/HAP 内容已验证。iOS 构建/真机未在此 Windows 环境验证。

回复“提交”即可按以上范围执行；回复“我自己来”则保留当前修改由用户手动提交。
