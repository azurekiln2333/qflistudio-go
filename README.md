# QFLIGoShift

[简体中文](README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md)

QFLIGoShift 是基于 Flutter 的 Go 学习与编辑应用。
本仓库通过本地路径依赖共享内核 `qfli_studio_core`。

## 基础功能

- 编辑器提供语法高亮和文件导航。
- 教程与示例支持复制代码和导入项目。
- 桌面端通过官方 Go SDK 运行程序。
- 桌面端支持构建、测试、格式化和模块命令。
- 移动端通过内置 Yaegi 解释器运行程序。
- 内置终端按平台选择运行后端。
- 移动端终端只支持 `go run` 形式的命令。

## 开发中的功能

以下功能来自尚未发布的开发改动。
这些改动可能存在问题。

- 语法诊断与编辑器波浪线。
- 格式化、导入、符号和本地模块工具。
- JSON 转 Go 结构体工具。
- 断点、单步、调用栈和变量查看。
- 命名工作区与多根项目恢复。

这些功能尚未通过当前版本的完整验证。
源码存在不代表安装包已经包含该能力。

## 平台与运行后端

下表区分后端设计和历史检查。
历史结果只适用于当时的源码与安装包。

| 平台 | 运行后端 | 前提 | 历史检查与限制 |
| --- | --- | --- | --- |
| Android | Yaegi，经 C ABI 与 Flutter FFI | 对应 ABI 的原生库 | x86_64 曾通过，ARM 设备未验证 |
| OpenHarmony | Yaegi，经 C ABI 与 Flutter FFI | OHOS Go 移植版构建的原生库 | x86_64 有历史证据，arm64 未验证 |
| iOS | Yaegi，经静态库与进程符号 | Mac、Xcode、Go SDK | 未完成 Apple 构建与设备验证 |
| Windows | 官方 Go SDK | 应用能在 `PATH` 找到 `go` | 工具链有历史证据，界面未打包验证 |
| Linux | 官方 Go SDK | 应用能在 `PATH` 找到 `go` | 后端有历史证据，Flutter 界面未验证 |
| macOS | 官方 Go SDK | 应用能在 `PATH` 找到 `go` | 未在 macOS 主机验证 |
| Web／其他平台 | 不可用 | 无 | 不提供原生 Go 运行 |

`lib/go_platform.dart` 定义平台映射。
移动端报告 `embedded-go-runtime`。
桌面端报告 `official-go-sdk`。

## 离线边界

独立版的应用功能以离线使用为目标。
内置课程不要求下载 Go 依赖包。
移动端解释器不等于完整 Go SDK。
移动端不提供官方 SDK 的构建和模块下载命令。
本应用不提供通用网络沙箱。
自定义 Go 程序可能访问网络或主机文件。
开发时获取 Flutter 依赖可能需要联网。
离线开发前需备齐依赖和工具链。

## 开发前提

- Flutter SDK 必须满足 Dart `>=3.11.5 <4.0.0`。
- 桌面运行需要本机安装 Go SDK。
- 本项目需要同级的共享内核仓库。
- OpenHarmony 构建需要 OHOS 版 Flutter SDK。

共享编辑器来自 `../qfli_studio_core/vendor/re_editor`。
目录布局如下：

```text
checkout-parent/
  qfli_studio_core/
  qfli_go/
```

## 开发命令

请在 `qfli_go` 目录操作。
下列命令是开发步骤，不是本次检查结果。

获取依赖：

```powershell
flutter pub get
```

运行应用：

```powershell
flutter run
```

检查 Dart 源码：

```powershell
flutter analyze --no-pub
```

请把 SDK 路径替换为本机路径。
运行测试：

```powershell
$env:QFLI_GO_TEST_EXECUTABLE = "C:\path\to\go.exe"
flutter test --no-pub --concurrency 1
```

课程工具使用 `tool/go_curriculum/` 的源文件。
主机检查不能替代设备检查。

```powershell
python tool/go_curriculum/assemble.py
python tool/go_curriculum/verify.py --go "C:\path\to\go.exe"
python tool/go_curriculum/dedup.py
```

## 原生库与安装包

Android 构建需要 Android NDK。
OpenHarmony 构建需要 OHOS SDK。
OpenHarmony 使用固定的 OHOS Go 移植版。
版本与源码说明见[原生运行说明](native/go_runtime/README.md)。

先构建 OHOS Go 主机工具链：

```powershell
./tool/build_ohos_go_toolchain.ps1 -BootstrapGoExecutable "C:\path\to\go.exe"
```

请使用脚本输出的 OHOS Go 路径。
构建五个 Android／OpenHarmony 原生库：

```powershell
./tool/build_go_runtime.ps1 `
  -GoExecutable "C:\path\to\go.exe" `
  -OhosGoExecutable "C:\path\to\ohos-go.exe" `
  -AndroidNdk "C:\path\to\ndk" `
  -OhosSdk "C:\path\to\ohos-sdk"
```

脚本覆盖三个 Android ABI 和两个 OpenHarmony ABI。
iOS 的 Xcode 构建阶段调用 `tool/build_ios_go_runtime.sh`。
修改原生源码后需重建对应安装包的原生库。
旧库不会自动获得源码修复。

使用 OHOS 版 Flutter 构建调试包：

```powershell
flutter build hap --debug --no-pub
```

安装包构建不能证明设备上的运行结果。

## 课程与验证状态

- 现有课程包含 120 个 Go 主题。
- 每个主题对应一篇教程和一个示例。
- 共享内核提供当前课程展示。
- 开发工作区另有 160 个草稿主题。
- 草稿尚未进入正式课程。
- 主机检查已有历史结果。
- 原始示例的 OHOS 全量检查仍未完成。
- 当前原生改动尚未通过完整检查。
- 当前界面改动尚未验证。

本仓库不声明当前版本的 OHOS 全量通过。
设备证据必须对应实际源码和安装包。

## 深入文档

- [原生运行、构建与平台证据](native/go_runtime/README.md)
- [课程工具](tool/go_curriculum/README.md)
- [学习路线](tool/go_curriculum/GUIDE.md)
- [课程内容格式](tool/go_curriculum/schema.md)
- [主机探测说明](tool/go_curriculum/mobile_check/README.md)

## 第三方声明

- [Go 标准库声明](assets/licenses/go.txt)
- [Yaegi 声明](assets/licenses/yaegi.txt)
