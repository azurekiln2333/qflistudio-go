# 项目进度总览

更新日期：2026 年 11 月 25 日
仓库：`azurekiln2333/qflistudio-go`
基线提交：`f279134`（分支 `ci/app-packages`）

五种口径分别记录，不混用：
代码已写 / 已提交 / GitHub 已收录 / CI 已通过 / 真机已验收。

---

## 一、已完成并已进入 GitHub

应用包构建工作流已落地。
文件是 `.github/workflows/app-packages.yml`，提交 `ca8b5a4`。
原生库构建工作流已落地。
文件是 `.github/workflows/native-runtime.yml`，提交 `0cb91fd`。
辅助脚本在 `tool/ci/`，共 6 个文件。
Flutter 下载重试与 Android 插件注册表修复见提交 `f279134`。

Go 课程内容已入库。
240 余个样例与主题文件位于 `.trellis/tasks/10-22-go-curriculum-ohos/research/`。
证据：`git ls-tree -r github/main -- .trellis/tasks/10-22-go-curriculum-ohos` 输出 280 项。

---

## 二、GitHub CI 已验证

### 2.1 应用包（run 45484027345，提交 `f279134`）

工作流整体成功，七个任务全部成功。

| 任务 | job 编号 | 产物 | 字节 |
| --- | --- | --- | --- |
| App / android / universal | 138764482749 | `app-android-universal` | 145571224 |
| App / ohos / arm64-v8a | 138764482681 | `app-ohos-arm64-v8a` | 62790840 |
| App / linux / x86_64 | 138764482355 | `app-linux-x86_64` | 43001776 |
| App / windows / x86_64 | 138764482857 | `app-windows-x86_64` | 36461904 |
| App / macos / x86_64 | 138764482957 | `app-macos-x86_64` | 23075224 |
| App / macos / arm64 | 138764482914 | `app-macos-arm64` | 21111652 |
| App / ios / arm64 | 138764482821 | `app-ios-arm64` | 19885100 |

### 2.2 原生库（run 45484027361，提交 `f279134`）

五个构建任务成功。

| 任务 | job 编号 | 产物 | 字节 |
| --- | --- | --- | --- |
| Android (3 ABIs) | 138765011512 | `native-android-<sha>` | 66137049 |
| OpenHarmony (2 ABIs) | 138765011696 | `native-ohos-<sha>` | 44740951 |
| macos-universal | 138765011672 | `native-macos-universal-<sha>` | 43631585 |
| ios-device | 138765011762 | `native-ios-device-<sha>` | 53386190 |
| ios-simulator | 138765011748 | `native-ios-simulator-<sha>` | 104584243 |

工作流整体结论为失败，唯一失败任务是 `Native source tests`（job 138764481895）。
详见第四节已知缺陷。

---

## 三、仅本地验证

以下结论来自本机，GitHub 上无法复核。

- `tool/ci/test_app_build.py` 44 项单元测试通过。记录时间早于提交 `ca8b5a4`。
- `go vet` 通过。
- 11 项产物检查通过。
- 早期 Android、OHOS 产物做过本地 SHA-256 摘要比对。

本轮约束禁止本机跑测试，以上数字不再复现。

---

## 四、未验证与已知缺陷

### 已知缺陷：调试器源码测试失败

`Test vendored runtime` 步骤失败。
这是代码缺陷，不是环境限制。
同一任务内 `Vet vendored runtime` 与产物校验步骤成功，说明失败只出在测试本身。
证据：run 45484027361，job 138764481895。

影响：
`10-22-go-offline-ide` 要求的「真实嵌入式调试」未达成。
`11-17-github-native-build` 的「native test 通过」验收项保持未勾选。

### 未验证事项

- 任何 OHOS 真机运行。`hdc list targets` 曾返回空。
- 任何 APK、IPA、HAP 的安装与启动。
- 手动触发工作流的入口。两次运行都由推送触发。
- iOS 产物的本地下载。曾遇 TLS 连接中断。
- 界面测试与设备端交互。

---

## 五、签名与分发状态

| 平台 | 签名状态 |
| --- | --- |
| Android | 调试密钥 |
| iOS | 未签名（IPA 为 unsigned） |
| OHOS | 未签名（HAP 为 unsigned） |
| macOS | ad hoc 签名，未公证 |
| Windows | 未签名 |
| Linux | 未签名 |

CI 不持有任何发布证书。
CI 只在临时检出中移除 OHOS 签名配置，不改动仓库内的 `ohos/build-profile.json5`。

---

## 六、分支与远端现状

GitHub 只有两个分支。

| 分支 | 提交 |
| --- | --- |
| `main` | `c5cab3d` |
| `ci/app-packages` | `f279134` |

gitee、gitlab、gitcode、cnb 四个远端停在 `82e17af` 与 `e5eb5d6`。
两者都是 `github/main` 的祖先，内容完整包含在 GitHub 上。
`feat/go-offline-ide` 与 `fix/go-release-integrity` 只在非 GitHub 远端存在。

---

## 七、Trellis 任务状态

| 任务 | 状态 | 说明 |
| --- | --- | --- |
| `00-bootstrap-guidelines` | 已归档 | spec 已写满 22 个文件 |
| `10-22-standalone-ide-completeness` | in_progress | 三个子任务，零个完成 |
| `10-22-go-curriculum-ohos` | in_progress | 内容已入库，OHOS 真机未验收 |
| `10-22-go-offline-ide` | in_progress | 调试器测试失败 |
| `10-22-standalone-integration` | planning | 依赖未满足，需跨仓库收证 |
| `11-17-github-native-build` | in_progress | 构建全绿，源码测试失败 |
| `11-17-app-package-ci` | 已归档 | 七个任务全绿 |

---

## 八、后续检查

先修调试器源码测试，再谈 Go 离线调试完成度。
真机验收需要一台可连的 OHOS 设备。
手动触发入口需要默认分支包含工作流后才能实测。
