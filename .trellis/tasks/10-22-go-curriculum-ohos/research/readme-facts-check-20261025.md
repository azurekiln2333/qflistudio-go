# README 事实核对报告（2026-10-25）

角色：check 复核者。范围：三份 README 的事实、三语一致性与受控中文。
状态：最终复核通过（PASS）。
本报告只读源码与文档。未运行 SDK、测试、构建、WSL、设备与运行时。未改动 README。

## 1. 核对快照

- `README.md` 简体中文
- `README.zh-TW.md` 繁体中文
- `README.en.md` 英文

三份已由根统一冻结。本报告只记录最终状态。

## 2. 结论

PASS。无阻断项。无事实错误。
上一轮 4 条阻断项、3 条事实错误已全部修复。

## 3. 结构与一致性核对

| 项目 | 结果 | 证据 |
| --- | --- | --- |
| 章节数 | 三份各 10 节，一一对应 | `## ` 标题逐条对齐 |
| 平台行数 | 三份各 7 行 | `Select-String '^\| (Android\|OpenHarmony\|iOS\|Windows\|Linux\|macOS\|Web)'` 各 7 |
| 代码块数 | 三份各 9 个 | 围栏行各 18 |
| 受控中文机械规则 | 两个中文文件退出码 0 | `python scripts/ste-lint-zh.py` |
| 繁体字形 | 程式庫、專案、檔案、指令碼、呼叫堆疊、中斷點、偵錯、倉庫、層 | 逐词核对 |
| 情态保留 | 可能存在问题、可能访问网络、`may be incorrect`、`may access` | 逐句核对 |

## 4. 事实核对通过项

| 主张 | 锚点 | 结果 |
| --- | --- | --- |
| 产品名 QFLIGoShift | `pubspec.yaml:2`、`AndroidManifest.xml:3`、`ohos/AppScope/resources/base/element/string.json:5`、`ios/Runner/Info.plist:10`、`windows/runner/main.cpp:30` | 一致 |
| Dart 约束 `>=3.11.5 <4.0.0` | `pubspec.yaml:7`（`^3.11.5` 等价） | 一致 |
| 同级共享内核 | `pubspec.yaml:13-14`、`pubspec.yaml:22-23` | 一致 |
| 共享编辑器来自 `vendor/re_editor` | `pubspec.yaml` 的 `dependency_overrides` | 一致 |
| 移动端后端为内嵌 Yaegi | `lib/go_platform.dart:15` | 一致 |
| 桌面端后端为官方 SDK | `lib/go_platform.dart:16` | 一致 |
| 后端代号 | `lib/go_platform.dart:3-5` | 一致 |
| 移动端终端只支持 `go run` | `lib/go_terminal_delegate.dart:149-150` | 一致 |
| 移动端不含构建与模块下载 | `lib/go_terminal_delegate.dart:27-30` | 一致 |
| 桌面动作含格式化与模块 | `lib/go_runner.dart:14` | 一致 |
| 不提供通用网络沙箱 | `.trellis/spec/frontend/native-startup.md:92` | 一致 |
| 自定义程序可能访问网络 | `.trellis/spec/frontend/native-startup.md:89-90` | 一致 |
| 五个原生库（3 Android + 2 OHOS） | `native/go_runtime/README.md:26-28` | 一致 |
| `build_go_runtime.ps1` 四参数 | `tool/build_go_runtime.ps1:1-6` | 一致 |
| `build_ohos_go_toolchain.ps1` 参数 | `tool/build_ohos_go_toolchain.ps1:1` | 一致 |
| OHOS Go 移植版 `v1.27.1-ohos` | `tool/build_ohos_go_toolchain.ps1:11`、`native/go_runtime/README.md:40-42` | 一致 |
| 调试包签名 `flutter build hap --debug --no-pub` | `.trellis/spec/frontend/native-startup.md:79` | 一致 |
| 平台历史证据 | `native/go_runtime/README.md:90-95` | 一致，且已标注历史 |
| 课程 120 主题 | `git ls-files tool/go_curriculum/topics` 计 120 | 一致 |
| 共享内核提供课程展示 | `git -C ../qfli_studio_core show HEAD:assets/content/tutorials.json` 的 Go 条目 120 | 一致 |
| 160 草稿属开发工作区 | 草稿 160 个文件，任务目录未跟踪 | 一致，且已标注开发工作区 |
| Go 声明 BSD 风格 | `assets/licenses/go.txt:1-3` | 一致 |
| Yaegi 声明 Apache-2.0 | `assets/licenses/yaegi.txt:1-3` | 一致 |

## 5. 链接可解析性

全部链接目标均已跟踪，干净检出中存在：

- `native/go_runtime/README.md`
- `tool/go_curriculum/README.md`
- `tool/go_curriculum/GUIDE.md`
- `tool/go_curriculum/schema.md`
- `tool/go_curriculum/mobile_check/README.md`
- `assets/licenses/go.txt`
- `assets/licenses/yaegi.txt`

三份 README 互相链接。`README.md` 已跟踪。`README.zh-TW.md` 与 `README.en.md` 为新文件，随本次文档提交加入。

无未跟踪文件引用。已确认三份中不含 `LICENSE`、`.trellis/`、`build_desktop_go_runtime.ps1`、`build_macos_go_runtime.sh`、`ste-lint-zh.py`、`go_catalog_test.dart` 等引用。

## 6. 已修复项

- 绝对离线声明改为范围限定，并声明不提供网络沙箱。
- 终端不再声明拒绝 `go mod download`。
- 删除长按运行按钮的声明。
- 平台表统一为历史口径。
- 开发中能力移入独立小节，并写明未发布、未验证。
- 删除 GPL 声明与未跟踪 `LICENSE` 链接，只保留第三方声明。
- 删除未跟踪脚本命令。
- 删除 `.trellis/spec/` 链接。
- HAP 构建命令改为已记录的 `--debug --no-pub`。
- Dart 约束写明 `>=3.11.5 <4.0.0`。
- 复合指令拆成独立步骤与独立代码块。

## 7. 非阻断观察（可保留）

1. 繁体版沿用「教程」。台湾习惯多用「教學」。两词均正确，且与简体版一词一义一致，保留不影响事实。
2. 三份均写「构建、测试、格式化和模块命令」，未列 `vet`。`vet` 在 `lib/go_runner.dart:14` 存在。三份写法一致，属省略，不构成错误。
3. 平台表只列 `embedded-go-runtime` 与 `official-go-sdk`。`unavailable` 由 Web 行覆盖。若需完整对应 `lib/go_platform.dart:5`，可补一行，非必需。

## 8. 机械规则核对

`python scripts/ste-lint-zh.py README.md` 退出码 0。
`python scripts/ste-lint-zh.py README.zh-TW.md` 退出码 0。
`README.en.md` 非中文，脚本不适用。
