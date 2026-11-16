# GitHub 原生库构建

工作流名称是 `Native runtime`。
工作流构建 Android、OHOS、macOS 和 iOS 原生库。
产物用于应用链接或打包。
产物不包含 APK、HAP、IPA 或桌面安装包。

## 运行与下载

1. 打开 GitHub 仓库的 **Actions**。
2. 打开 **Native runtime**。
3. 打开对应提交的运行记录。
4. 在 **Artifacts** 中下载目标平台的 ZIP。

推送原生源码或构建脚本会触发工作流。
首次推送工作流也会触发运行。
默认分支包含工作流后，可点击 **Run workflow**。
手动运行时选择源码分支。
下载需要登录 GitHub。
产物保留 14 天。
过期后重新运行工作流。

每个产物名称带有完整提交 SHA。
请下载与应用源码对应的产物。

| 产物名称前缀 | 架构 | ZIP 内容 |
| --- | --- | --- |
| `native-android-` | arm64-v8a、armeabi-v7a、x86_64 | 各 ABI 的 `.so` 和 `.h` |
| `native-ohos-` | arm64-v8a、x86_64 | 各 ABI 的 `.so` 和 `.h` |
| `native-macos-universal-` | arm64、x86_64 | 通用 `.dylib` 和各架构头文件 |
| `native-ios-device-` | arm64 | 真机 `.a` 和 `.h` |
| `native-ios-simulator-` | arm64、x86_64 | 模拟器通用 `.a` 和 `.h` |

各 ZIP 还包含 `manifest.json`、`SHA256SUMS` 和许可证。
Android 和 OHOS 另含 `bundled-go-runtime-build.json`。
清单记录源码摘要、提交、文件大小和 SHA-256。
运行日志显示下载、编译和检查结果。
构建成功不能证明设备运行通过。
源码测试和原生编译分别报告结果。
测试失败时，编译任务仍会尝试生成产物。
请检查清单中的 `sourceChecksConclusion`。
测试失败的产物仅供排查。

## 构建环境

Android 和 OHOS 使用独立的 Windows runner。
Apple 产物使用 macOS runner。
Linux runner 只运行源码测试。
本工作流不上传 Windows 或 Linux 原生库。

工作流使用官方 Go 1.27.1。
Android 使用 NDK 28.2.13676358。
OHOS 使用固定提交的 OHOS Go 移植版。
默认 OHOS SDK 来自官方 5.0.0 发布包。
工作流检查下载包的 SHA-256。
首次运行无需填写 SDK 下载地址。

覆盖 SDK 时，同时设置 URL 和 SHA-256。
手动输入名称为 `ohos_sdk_url` 和 `ohos_sdk_sha256`。
仓库变量名称为 `OHOS_SDK_URL` 和 `OHOS_SDK_SHA256`。
压缩包必须包含 Windows 原生 SDK。
SDK 必须提供 `native/llvm` 和 `native/sysroot`。

macOS dylib 使用临时签名。
iOS 静态库无需开发者证书。
应用分发仍需完成各平台的签名步骤。

## 使用下载产物

先检查 ZIP 中的提交 SHA。
再按平台复制对应文件。

| 产物 | 本地目标位置 |
| --- | --- |
| Android 各 ABI 的 `.so` | `android/app/src/main/jniLibs/<abi>/` |
| OHOS 各 ABI 的 `.so` | `ohos/entry/libs/<abi>/` |
| macOS `.dylib` | 应用的 `Contents/Frameworks/` |
| iOS `.a`、`.h` | 对应真机或模拟器的链接输入 |

Android 和 OHOS 可在打包前替换原生库。
请保留 ABI 子目录。
请勿混用 iOS 真机库和模拟器库。

当前 Apple 构建阶段仍会从源码编译原生库。
本任务未增加 Apple 预编译库导入开关。
直接运行 Flutter 或 Xcode 仍会生成本地缓存。

Windows、Linux、macOS 用官方 SDK 运行用户代码。
桌面诊断和调试仍需项目自己的原生库。
现有桌面构建步骤会编译该库。
官方 Go SDK 不包含 `qfli_go_runtime`。

## 本地空间

GitHub 构建不会自动删除本地文件。
停止构建后，再清理可重建目录。
先保留仍需安装的包和验证证据。

| 目录 | 内容 | 清理影响 |
| --- | --- | --- |
| `build/` | Flutter 编译产物 | 下次应用构建重新生成 |
| `.dart_tool/` | Dart 状态和缓存 | 需重新获取依赖并构建 |
| `native/build/` | Go SDK、OHOS Go、缓存和探测输出 | 本地原生构建需重新准备工具链 |
| `.artifacts/` | 安装包、截图和验证证据 | 删除后会失去本地证据副本 |
| `ohos/build/`、`ohos/entry/build/` | OHOS 编译产物 | 下次 HAP 构建重新生成 |
| `ohos/.hvigor/` | OHOS 构建缓存 | 下次构建重新生成 |
| `ohos/node_modules/`、`ohos/oh_modules/` | OHOS 工具依赖 | 需重新安装依赖 |

请保留 `native/go_runtime/` 源码和 `vendor/`。
`ohos/entry/libs/` 保存打包需要的原生库。
清理这些库后，应先恢复下载产物。
清理整个 `ohos/` 会删除工程源码。

2026 年 11 月 17 日的审查记录如下。
以下数值使用 GiB。
目录总量不等于可直接删除的容量。

| 目录 | 当时占用 |
| --- | ---: |
| `build/` | 2.73 GiB |
| `native/build/` | 2.05 GiB |
| `.dart_tool/` | 0.98 GiB |
| `.artifacts/` | 0.61 GiB |
| 整个 `ohos/` | 0.47 GiB |

远程构建可减少本地原生工具链和缓存增长。
本地 Flutter 开发仍需 Flutter SDK 和构建缓存。
