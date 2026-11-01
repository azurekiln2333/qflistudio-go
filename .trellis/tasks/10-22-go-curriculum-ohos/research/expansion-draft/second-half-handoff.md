# T201–T280 草稿交接（2026-10-23）

本交接只覆盖 Go 扩展草稿后八十题。全部文件保留在本 `expansion-draft/` 目录，未推广到 `tool/go_curriculum/topics`、产品 catalog 或共享 assets；`runtime` 仍为 `desktop`。

## 已交付文件

- `topics/T201.json`–`T280.json`：八十个独立教学条目，每题含完整示例、中文讲解、至少两个陷阱和带答案练习。
- `samples/T201/main.go`–`T280/main.go`：八十份对应的 gofmt 源码；每题教程、示例与实际 sample 的代码逐字节相同。
- 作者脚本：`author_second_half.py` 和 `author_{crypto,archives,http,concurrency,presentation,validation,binary,applications}.py`，可以重生成本范围，不会生成其他作者 ID。
- `checks/second-half-review-final/review.json`：当前八十题的 topic/sample SHA256、八批官方历史报告 SHA256、报告与当前源码的差异、尚未通过的执行 gate。
- `checks/second-half-current-inventory/`：当前修订后八十题的独占 topic 快照、catalog 和实际导入 manifest。

## 官方 Go 历史执行证据

以下每批均执行实际显示的教程、示例、canonical sample 三种形态，三十条记录全过、无 timeout、exitCode 为零。合计 **240/240**，这些报告保留各自原始 topic 快照。

| 范围 | `checks/<tag>/official.json` | 结果 |
| --- | --- | --- |
| T201–T210 | `crypto-official` | 30/30 |
| T211–T220 | `archives-official` | 30/30 |
| T221–T230 | `http-official` | 30/30 |
| T231–T240 | `concurrency-official` | 30/30 |
| T241–T250 | `presentation-official` | 30/30 |
| T251–T260 | `validation-official` | 30/30 |
| T261–T270 | `binary-official` | 30/30 |
| T271–T280 | `applications-official` | 30/30 |

**这 240 次通过属于静态复审前的旧快照，不能作为当前完整源码的最终执行通过。** 复审后五份 topic JSON 改变，其中四份程序改变：

- **T201**：从内存 map 校验改为 `MkdirTemp`、`WriteFile`、`ReadFile` 校验真实文件，保留匹配、被修改文件、坏摘要格式三个断言；增加摘要长度检查及清理。说明明确外部清单仍需路径约束。
- **T274**：同类问题修成真实 `manifest.json` 与文件读取，实际检测缺失、长度、摘要，分开处理读取错误；只允许单级文件名并准确说明独占目录前提。
- **T229**：基准改为有末尾斜线的目录 URL，与 roadmap 一致；练习改为有、无末尾斜线的可观察区别，期望输出同步更新。
- **T257**：除十三位加权和外检查 978/979 前缀，新增拒绝“校验和正确但不是 ISBN 前缀”的 EAN13；说明不验证注册组/出版社分段。
- **T271**：只改讲解，明确输入为内存 CSV 文本；程序没有改变。

其余七十五份 topic JSON 与上述官方快照逐字节一致；七十六份 Go 程序不变。没有在此次静态修订后重新执行官方、原生或 race 全量，遵循主会话资源排队要求。

## 当前轻量检查

- `check_owner.py --first 201 --last 280 --tag second-half-current-inventory --backend inventory`：**assemble 80 教程 + 80 示例，dedup 80 通过，inventory 240 cases / 0 issues**。
- 原始 120 题 + 全部新增 160 题的隔离快照：`checks/second-half-review-final/all-topics/`，`dedup.py` **280/280 无实质重复**，输出见同目录上层 `dedup.txt`。快照在另一作者 T193/T195 最终文案修订后再次与当前全部 topic 逐字节比较，零差异。
- 当前本范围八十题：sample/tutorial/example 代码完全一致；期望输出相互一致；教学字段、答案与 desktop 标签检查通过；九个作者脚本 Python AST 解析通过。
- 人工逐组核对标题、roadmap 行为与程序/说明。HTTP Handler、归档、multipart 明确为内存协议操作；T247 明确 rune 数量不代表终端视觉宽度；T277 明确单协程内存事务；T279 明确同进程失败模拟及真实提交/检查点原子性边界，未宣称已实现持久崩溃恢复。
- `git diff --check` 通过；仓库只报告既有 LF/CRLF 转换提示。未修改另一作者 T121–T200、原始课程、native 源码或产品资源。

`dedup.py` 是文本、数字常数归一化启发式；它没有替代独立教学语义审阅。

## 主会话后续 gate

1. 在获得资源 slot、T106 Helper 修订和当前 native 源码稳定后，用新 tag 顺序执行当前两作者范围的官方与原生全量。当前八十题的 native 运行尚未开始。
2. 对并发题 T231–T240 使用实际 Linux SDK/CGO race gate；本批尚无 `-race` 证据。
3. 更新最终 native artifact 后，执行真实 FFI debugger 两项此前跳过测试，再由主会话处理原始 corpus 与实际 OHOS 包/设备全量 gate。
4. 新增草稿仍受主会话发布 gate 约束。此处没有 OHOS 执行证据、没有发布或设备通过声明。

当前没有本 agent 留下的运行中编译/审计进程；官方句柄 2163 与 56286 均已收取成功并结束。
