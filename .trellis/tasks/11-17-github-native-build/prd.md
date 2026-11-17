# GitHub Actions 原生运行库构建

## 目标

让 GitHub Actions 远程构建移动端和 Apple 原生运行库。

远程构建可以减少本地缓存增长。
用户可以从 Actions 下载构建产物。

## 已确认事实

- 当前分支是 `feat/go-offline-ide`。
- 实施前工作区没有未提交代码。
- 当前分支比远端多 9 个提交。
- 实施前仓库没有 GitHub Actions 工作流。
- `tool/build_go_runtime.ps1` 构建 Android 和 OHOS 库。
- 该脚本会写入 `bundled-go-runtime-build.json`。
- `tool/build_macos_go_runtime.sh` 构建 macOS dylib。
- `tool/build_ios_go_runtime.sh` 构建 iOS archive。
- Windows 和 Linux 用官方 SDK 运行用户代码。
- 桌面诊断和调试仍依赖项目原生库。
- 本任务不重复构建 Windows 和 Linux runtime。
- Android 构建需要 Android NDK。
- OHOS 构建需要 OHOS SDK。
- OHOS 构建需要固定版本的 OHOS Go。
- Apple 构建需要 macOS runner 和 Xcode。
- Apple runtime 构建不需要开发者证书。
- 本地生成物和缓存约 6.8 GB。

## 需求

- 新增一个 GitHub Actions 工作流。
- Windows runner 构建 Android 和 OHOS。
- macOS runner 构建 macOS 和 iOS。
- 支持手动触发工作流。
- 修改 native 文件时自动触发工作流。
- 使用仓库现有构建脚本。
- 使用 vendor 依赖。
- 不提交 SDK、工具链和缓存。
- 构建 Android 三个 ABI。
- 保留 Android 16 KB 页面对齐要求。
- 构建 OHOS 两个 ABI。
- 使用固定版本的 OHOS Go。
- 构建 macOS 通用 dylib。
- 构建设备版 iOS archive。
- 构建模拟器版 iOS archive。
- 默认下载官方 OHOS SDK。
- 允许覆盖 SDK URL 和 SHA-256。
- 检查 OHOS SDK 的 SHA-256。
- 缺少 OHOS SDK 时明确失败。
- 每个平台单独上传构建产物。
- 上传构建证明和 SHA-256 清单。
- 推送任务提交到 GitHub 功能分支。
- 记录实际构建结果和下载入口。
- 在 README 说明下载位置。
- 在 README 说明产物内容。
- 在 README 说明本地清理目录。

## 验收标准

- [x] `.github/workflows/native-runtime.yml` 存在。
- [x] GitHub Actions 可以解析该文件。
- [ ] 手动触发可以构建 Android。
- [ ] 手动触发可以构建 OHOS。
- [ ] 手动触发可以构建 macOS。
- [ ] 手动触发可以构建 iOS。
- [x] Android 产物包含三个 ABI。
- [x] OHOS 产物包含两个 ABI。
- [x] macOS 产物包含通用 dylib。
- [ ] iOS 产物区分设备版和模拟器版。
- [x] OHOS job 检查 SDK SHA-256。
- [x] Apple job 不需要开发者证书。
- [x] 产物名称包含平台和提交 SHA。
- [x] README 说明 Actions 下载入口。
- [x] README 说明本地清理目录。
- [x] 本地检查通过 YAML 静态检查。
- [x] Apple shell 脚本通过语法检查。
- [ ] native test/vet 通过，或记录环境限制。

## 实跑记录

推送已触发 GitHub 构建。
Android 和 OHOS 构建成功。
两者的新产物已通过本地摘要检查。
iOS 真机库构建成功。
真机 ZIP 的本地下载遇到 TLS 连接中断。
上一轮 macOS 通用库构建成功。
新一轮 macOS 和模拟器构建成功。
具体状态见 `research/remote-validation.json`。

源码测试发现既有调试器故障。
这是测试失败，不是环境限制。
`go vet` 和 11 项产物检查通过。
产物清单保留源码检查的失败状态。

当前运行由推送触发。
本次未验证手动触发入口。
用户随后授权合并到默认分支。
GitHub `main` 已快进到 `9b7248a`。
本地 `main` 与远端提交一致。
未满足的验收项继续保留。

GPL v3 声明已对齐主项目。
三个 README 已补齐许可证说明。
提交 `b324c92` 已推送到 GitHub。

## 不在范围内

- 构建 Linux desktop runtime。
- 构建 Windows desktop runtime。
- 打包 Flutter 应用。
- 签名 Apple 应用。
- 公证 Apple 应用。
- 安装应用到设备。
- 自动发布 GitHub Release。

## 约束

- 保留 `-mod=vendor`。
- 保留 `GOTOOLCHAIN=local`。
- 保留离线依赖设置。
- 保留现有构建证明格式。
- 遵循 native runtime 规范。
- SDK 和缓存只留在 runner。

