# GitHub 应用包构建

工作流名称是 `App packages`。
工作流文件是 `.github/workflows/app-packages.yml`。
工作流构建六个平台的应用包。
原生库由 `Native runtime` 工作流单独构建。
原生库说明见[原生库构建指南](../native/go_runtime/CI.md)。

本文档描述工作流的设计。
各任务的实际结果以运行记录为准。

## 构建任务

工作流包含七个任务。
每个任务上传一个独立产物。

| 平台 | 架构 | Runner | 应用包文件 | 产物名称 |
| --- | --- | --- | --- | --- |
| Android | universal | `ubuntu-24.04` | `qfligoshift-android-<abi>.apk`，共三个 | `app-android-universal` |
| iOS | arm64 | `macos-15-intel` | `qfligoshift-ios-arm64-unsigned.ipa` | `app-ios-arm64` |
| OHOS | arm64-v8a | `ubuntu-24.04` | `qfligoshift-ohos-arm64-v8a-unsigned.hap` | `app-ohos-arm64-v8a` |
| Linux | x86_64 | `ubuntu-24.04` | `qfligoshift-linux-x86_64.tar.gz` | `app-linux-x86_64` |
| Windows | x86_64 | `windows-2025` | `qfligoshift-windows-x86_64.zip` | `app-windows-x86_64` |
| macOS | arm64 | `macos-26` | `qfligoshift-macos-arm64.tar.gz` | `app-macos-arm64` |
| macOS | x86_64 | `macos-15-intel` | `qfligoshift-macos-x86_64.tar.gz` | `app-macos-x86_64` |

Android 任务输出三个 ABI 的 APK。
三个 ABI 是 arm64-v8a、armeabi-v7a 和 x86_64。
Windows 应用包是便携 ZIP。
Linux 应用包是便携 tar.gz。
每个 macOS tar.gz 包含 `QFLIGoShift.app`。

## 触发方式

手动运行的步骤：

1. 打开 GitHub 仓库的 **Actions**。
2. 打开 **App packages**。
3. 点击 **Run workflow**。
4. 选择源码分支。

默认分支包含工作流后，页面才提供 **Run workflow**。

推送下列路径的改动也会触发工作流。
推送触发不限制分支。

- `.github/workflows/app-packages.yml`
- `tool/ci/app_build.py` 和 `tool/ci/test_app_build.py`
- `tool/inspect_go_catalog_hap.py` 和 `tool/go_curriculum/audit_native.py`
- `tool/build_ios_go_runtime.sh` 和 `tool/build_macos_go_runtime.sh`
- `lib/**`、`assets/**` 和 `native/go_runtime/**`
- 各平台的工程目录
- `pubspec.*`

完整路径以工作流文件的 `paths` 为准。

## 下载产物

1. 打开 **App packages** 的运行记录。
2. 在 **Artifacts** 中找到目标产物。
3. 下载产物 ZIP。
4. 解压 ZIP。
5. 从 `packages/` 取出应用包。

产物名称的格式是 `app-<平台>-<架构>`。
下载需要登录 GitHub。
GitHub 保留产物 14 天。
过期后重新运行工作流。
工作流不发布 GitHub Release。

## 产物内容

| 路径 | 内容 |
| --- | --- |
| `packages/` | 通过全部检查的应用包 |
| `reports/` | 命令日志、`package-inspection.json` 和失败记录 |
| `licenses/` | 许可证文件 |
| `manifest.json` | 清单 |
| `SHA256SUMS` | 产物文件的 SHA-256 摘要 |

全部检查通过后，任务才写入 `packages/`。
任一步骤失败时，任务移除 `packages/`。
清单把该任务标记为失败。
失败任务的产物不包含 `packages/`。
失败任务的产物只用于查看报告。

清单记录签名状态和检查范围。
清单的 `signing` 记录签名状态。
清单的 `goRuntime` 记录 Go 原生库的来源。
清单的 `deviceTests` 和 `runtimeTests` 都是 `not_run`。

## 签名状态

仓库没有配置签名密钥。
工作流不提供商店发布签名和公证。

| 平台 | 签名状态 | 清单的 `signing` | 使用限制 |
| --- | --- | --- | --- |
| Android | APK 使用调试密钥签名 | `debug_key_for_testing_not_store_release` | 只用于测试安装。不能用于商店发布 |
| iOS | IPA 未签名 | `unsigned_requires_signing_before_device_installation` | 安装到设备前必须重新签名 |
| OHOS | HAP 未签名 | `unsigned_requires_signing_before_device_installation` | 安装到设备前必须签名 |
| macOS | 应用使用临时签名，未公证 | `ad_hoc_not_notarized` | Gatekeeper 会发出警告 |
| Windows | EXE 未签名 | `unsigned_executable` | 无 |
| Linux | 不适用 | `not_applicable` | 无 |

## 使用桌面应用包

Windows：

1. 解压 `qfligoshift-windows-x86_64.zip`。
2. 运行 `qfli_go.exe`。

Linux：

1. 解压 `qfligoshift-linux-x86_64.tar.gz`。
2. 运行 `qfli_go`。

macOS：

1. 解压与本机架构对应的 tar.gz。
2. 打开解压得到的 `QFLIGoShift.app`。

Windows 和 Linux 的主程序依赖同目录的库和资源。
请保留解压后的完整目录。
桌面应用通过官方 Go SDK 运行 Go 程序。
本机需要安装 Go SDK。

## 上传前的检查

任务在写入 `packages/` 前检查应用包。
所有平台都检查九个 C ABI 导出符号。
所有平台都比较包内 Flutter 资源与源码资源的字节。
资源范围来自 `pubspec.yaml` 的声明。

| 平台 | 其他检查 |
| --- | --- |
| Android | APK 的 ABI 等于目标 ABI。包内有 `libflutter.so`、`libapp.so` 和 `libqfli_go_runtime.so`。ELF 类型和机器架构正确。64 位 ABI 的 LOAD 对齐不小于 16 KiB。包内有 `AndroidManifest.xml`。`zipalign` 和 `apksigner` 检查通过 |
| OHOS | `libs/arm64-v8a/` 有同一组库。ELF 类型和机器架构正确。包内有 `module.json` |
| Linux | 包内有 `qfli_go`、Flutter 库、`libapp.so` 和 `libqfli_go_runtime.so`。包内有 `data/icudtl.dat`。ELF 类型和机器架构正确 |
| Windows | 包内有 `qfli_go.exe`、`flutter_windows.dll` 和 `qfli_go_runtime.dll`。包内有 `data/app.so` 和 `data/icudtl.dat`。主程序和 DLL 是 x64 PE。包内有每个导入的 `lib*.dll` |
| macOS | 包内有 `QFLIGoShift.app`。主程序架构等于任务架构。框架和 `libqfli_go_runtime.dylib` 包含该架构。`codesign` 深度检查通过 |
| iOS | 包内有 `Runner.app`。主程序架构是 arm64。包内有所需框架。导出符号检查针对主程序 |

## 工作流不做的事

- 不把应用包安装到设备。
- 不运行设备测试。
- 不运行界面测试。
- 不提供商店发布签名、公证和上架。
- 不制作安装程序，例如 Inno Setup、dmg 和 deb。
- 不输出 Android App Bundle。
- 不发布 GitHub Release。
- 不重建 Android 和 OHOS 的 Go 原生库。

Android 和 OHOS 任务使用仓库已提交的 Go 原生库。
`Native runtime` 工作流负责构建原生库。
其余五个任务从源码编译 Go 原生库。
清单的 `goRuntime` 记录这一区别。

Android 和 OHOS 的报告记录两个摘要。
一个摘要属于已提交的库。
另一个摘要属于包内的库。
打包工具可能裁剪库文件。
报告记录两个库是否逐字节相同。

构建通过不能证明设备运行通过。

## 固定输入

| 输入 | 固定值 |
| --- | --- |
| 共享内核 | `azurekiln2333/qflistudio-core@573d1b6eecf1c2b392ad753264a5a09f62f8335e` |
| Flutter-OH | 标签 `3.41.9+ohos-1.0.2`，提交 `62357a93d653bf844f730bb1f4b7cc9e2139d14e`，Dart 3.11.5 |
| Go | 1.27.1 |
| OHOS SDK | API 26 命令行工具 `26.0.0.821` |
| Java | Temurin 17，用于 Android 和 OHOS |
| Windows 的 C 编译器 | MSYS2 UCRT64 的 `mingw-w64-ucrt-x86_64-gcc` |

CI 在应用目录旁检出共享内核。
检出目录的名称是 `qfli_studio_core`。
Flutter-OH 来自 `https://gitcode.com/CPF-Flutter/flutter_flutter.git`。
OHOS SDK 来自 `ErBWs/ohos-sdk` 镜像。
OHOS SDK 分为两个下载包。
任务检查每个下载包的 SHA-256。
工作流使用的 Actions 固定到提交 SHA。
仓库不提交 SDK、工具链和缓存。

## OHOS 签名配置

已提交的 `ohos/build-profile.json5` 含本机签名配置。
CI 只在临时检出中移除签名配置。
CI 不修改已提交的 `ohos/build-profile.json5`。
辅助脚本拒绝在 GitHub Actions 之外移除签名配置。
CI 不使用本机密钥、证书或密码。

## 本地测试

辅助脚本是 `tool/ci/app_build.py`。
运行 `tool/ci/` 下的单元测试：

```powershell
python -m unittest discover -s tool/ci -p "test_*.py"
```

该命令不构建应用包。
