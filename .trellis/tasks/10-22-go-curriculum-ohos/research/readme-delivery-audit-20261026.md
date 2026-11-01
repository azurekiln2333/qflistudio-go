# README 交付核对报告（2026-10-26）

角色：check 复核者。范围：交付提交的范围、三语一致性、受控中文、链接与命令。
约束：只读。未运行产品测试、构建、设备与运行时。未改动 README。未做任何 git 写操作。
本报告为私有核对记录，不属于三文件发布提交。

## 1. 提交范围

提交：`e5eb5d631639a65c31da0e8fad964ec631de7771`。
标题：`docs(readme): rewrite guides in three languages`。
父提交：`82e17af4233e3aa2c6dd8eac2cb3f808f0f20a4f`。
分支：`feat/go-offline-ide`。该提交是当前 HEAD。

变更文件（相对父提交）：

| 状态 | 文件 |
| --- | --- |
| A | `README.en.md` |
| M | `README.md` |
| A | `README.zh-TW.md` |

差异统计：3 个文件，529 行新增，18 行删除。
结论：提交只含三份 README。没有其他文件。

## 2. 工作区与提交一致性

- 三份 README 的工作区状态干净（`git status --porcelain` 无输出）。
- 三份的提交 blob 与工作区对象哈希一致：

| 文件 | blob 前缀 | 一致 |
| --- | --- | --- |
| `README.md` | `6d1a56d57b` | 是 |
| `README.zh-TW.md` | `e9ab07beef` | 是 |
| `README.en.md` | `8fff9bfb5e` | 是 |

结论：核对的内容等于提交内容。

## 3. 结构一致性

对提交 blob 计数：

| 文件 | 二级标题 | 平台行 | 围栏行 | 代码块 | Markdown 链接 |
| --- | --- | --- | --- | --- | --- |
| `README.md` | 10 | 7 | 18 | 9 | 11 |
| `README.zh-TW.md` | 10 | 7 | 18 | 9 | 11 |
| `README.en.md` | 10 | 7 | 18 | 9 | 11 |

二级标题按顺序一一对应：

1. 基础功能／基本功能／Core features
2. 开发中的功能／開發中的功能／Features in development
3. 平台与运行后端／平台與執行後端／Platforms and execution backends
4. 离线边界／離線邊界／Offline boundary
5. 开发前提／開發前置條件／Development prerequisites
6. 开发命令／開發指令／Development commands
7. 原生库与安装包／原生程式庫與安裝套件／Native libraries and packages
8. 课程与验证状态／課程與驗證狀態／Curriculum and verification status
9. 深入文档／延伸文件／Further documentation
10. 第三方声明／第三方聲明／Third-party notices

## 4. 受控中文规则

命令：`python scripts/ste-lint-zh.py README.md README.zh-TW.md`。

- 默认句长上限 40：`README.md` 硬违规 0，`README.zh-TW.md` 硬违规 0，退出码 0。
- 严格句长上限 25：`README.md` 硬违规 0，`README.zh-TW.md` 硬违规 0，退出码 0。
- 合计 2642 字，每 100 字 0.0 处。
- 脚本不标记情态词（可能、maybe、may）。

脚本支持多文件参数（`files` 为 `nargs='*'`）。

## 5. 链接与本地目标

三份 README 无外部链接。

本地链接目标共 10 个。全部在提交树中存在：

- `README.md`
- `README.zh-TW.md`
- `README.en.md`
- `native/go_runtime/README.md`
- `tool/go_curriculum/README.md`
- `tool/go_curriculum/GUIDE.md`
- `tool/go_curriculum/schema.md`
- `tool/go_curriculum/mobile_check/README.md`
- `assets/licenses/go.txt`
- `assets/licenses/yaegi.txt`

无未跟踪目标。无 `LICENSE`、`.trellis/`、未跟踪脚本等引用。

## 6. 命令一致性

三份代码块内的命令行完全相同，逐行比对无差异：

- `flutter pub get`
- `flutter run`
- `flutter analyze --no-pub`
- `$env:QFLI_GO_TEST_EXECUTABLE = "C:\path\to\go.exe"`
- `flutter test --no-pub --concurrency 1`
- `python tool/go_curriculum/assemble.py`
- `python tool/go_curriculum/verify.py --go "C:\path\to\go.exe"`
- `python tool/go_curriculum/dedup.py`
- `./tool/build_ohos_go_toolchain.ps1 -BootstrapGoExecutable "C:\path\to\go.exe"`
- `./tool/build_go_runtime.ps1 -GoExecutable -OhosGoExecutable -AndroidNdk -OhosSdk`
- `flutter build hap --debug --no-pub`

脚本参数与源码一致：

- `tool/build_go_runtime.ps1:1-6` 四个参数名匹配。
- `tool/build_ohos_go_toolchain.ps1:1` 参数名匹配。
- HAP 命令匹配 `.trellis/spec/frontend/native-startup.md:79` 的记录。

## 7. 远程分支一致性

根提供独立证据（本次未重复发起网络请求）：

- 命令：`git ls-remote --exit-code <remote> refs/heads/feat/go-offline-ide`。
- 远端：origin、github、gitcode、cnb、gitlab。
- 结果：五个远端退出码均为 0。
- 返回 ref 均为 `e5eb5d631639a65c31da0e8fad964ec631de7771`。

结论：五个远端的分支尖端与本地 HEAD 相同。交付提交已在远端可见。

## 8. 结论

交付提交核对通过。范围只含三份 README。三语结构一致。本地链接全部可解析。受控中文规则在默认与严格句长下均为 0 违规。五个远端指向同一提交。

## 9. 剩余全产品门禁（未完成）

本节不声明完成。三份 README 已如实标注这些限制。

1. OHOS 全产品验收：原始 120 主题的设备运行仍未完成。需要真实连接目标。
2. 当前原生改动：尚未通过完整编译与运行。
3. 当前界面改动：尚未验证。
4. 共享课程聚合集成：由指定的核心集成者单独完成，不属于本次提交。
5. Go 诊断与调试器：属于姊妹任务 `10-22-go-offline-ide`，仍是未发布开发功能。
6. 全量 Go 测试、构建与导入门禁：尚未在本提交范围内运行。
7. Apple 构建与设备验证：需要在 Mac 与 Xcode 环境完成。
8. Linux Flutter 界面与 Windows 界面打包：尚未验证。

README 的表述与上述门禁一致。发布提交只覆盖文档，不覆盖产品验收。