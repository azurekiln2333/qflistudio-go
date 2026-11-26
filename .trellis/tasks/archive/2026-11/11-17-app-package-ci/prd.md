# 应用安装包 CI 构建

## 目标

让 GitHub Actions 构建六个平台的完整应用包。
用户可以从 Actions 下载应用包。

## 已确认事实

- 仓库只有 `native-runtime.yml` 一个工作流。
- 该工作流只构建原生库，不构建应用包。
- 应用依赖同级目录 `qfli_studio_core`。
- 共享核心仓库是公开仓库 `azurekiln2333/qflistudio-core`。
- 同级项目 `qfli_lua` 的应用工作流已在 GitHub 通过。
- 该工作流使用固定版本的 Flutter-OH 构建全部平台。
- Windows 和 Linux 应用构建会编译 Go 原生库。
- macOS 和 iOS 的 Xcode 构建阶段会编译 Go 原生库。
- 这些编译需要 Go 1.27.1 和 C 编译器。
- Go 1.27 要求 macOS 13 或更高版本。
- Android 和 OHOS 的 Go 原生库已提交到仓库。
- `ohos/build-profile.json5` 含本机签名配置。
- 仓库没有配置任何签名密钥。

## 需求

- 新增一个 GitHub Actions 工作流。
- 工作流构建 Android、iOS、OHOS、Linux、Windows、macOS 应用包。
- 支持手动触发工作流。
- 修改应用源码或构建文件时自动触发工作流。
- Android 输出三个 ABI 的 APK。
- OHOS 输出 arm64-v8a 的未签名 HAP。
- iOS 输出未签名 IPA。
- Windows 输出 x86_64 便携 ZIP。
- Linux 输出 x86_64 便携 tar.gz。
- macOS 输出 arm64 和 x86_64 两个 tar.gz。
- 每个 tar.gz 包含 `QFLIGoShift.app`。
- 每个任务上传一个独立产物。
- 产物包含清单、SHA-256 摘要、许可证和构建日志。
- 清单如实记录签名状态和验证范围。
- 上传前检查包内的原生库和资源。
- 检查失败时不上传应用包，只保留报告。
- CI 只在临时检出中移除 OHOS 签名配置。
- 文档说明触发方式、下载位置和签名状态。

## 约束

- 不提交 SDK、工具链和缓存。
- 不把本机密钥、证书或密码写入 CI。
- 不修改已提交的 `ohos/build-profile.json5`。
- 不修改现有 `native-runtime.yml` 的行为。
- 工作流动作使用固定提交 SHA。
- Flutter、共享核心和 OHOS SDK 使用固定版本和 SHA-256 摘要。
- 提交信息使用规范格式，不带助手署名。
- 推送到新分支，不直接推送 `main`。

## 范围之外

- 商店发布签名、公证和上架。
- Inno Setup、dmg、deb 等安装程序。
- Android App Bundle。
- 设备安装测试和界面测试。
- 在应用任务中重建 Android 和 OHOS 的 Go 原生库。
- GitHub Release 发布。

## 验收标准

- [ ] 工作流文件通过 YAML 解析。
- [ ] 辅助脚本的单元测试在本机通过。
- [ ] 推送后 GitHub 运行七个构建任务。
- [ ] 每个成功任务上传名为 `app-<平台>-<架构>` 的产物。
- [ ] 成功产物包含 `packages/`、`manifest.json` 和 `SHA256SUMS`。
- [ ] 失败任务的产物不包含 `packages/`。
- [ ] 中文文档通过 `scripts/ste-lint-zh.py` 检查。
- [ ] 最终报告如实列出每个任务的实际结果。
