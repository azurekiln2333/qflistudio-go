# 打包绑定证据链源码审计（2026-10-26）

角色：独立审计者。范围：源码/HAP/证据三方绑定与缺失原生退出码处理。
活动任务：`10-22-go-curriculum-ohos`。依赖任务：`10-22-go-offline-ide`。
状态：源码审计完成。源码阻断项 0 条。runtime 闸门全部 UNRUN。

本报告只做静态阅读。手段限于 AST 解析、PowerShell 语法解析与文本比对。
未导入任何脚本。未执行任何脚本。未执行测试、构建、SDK、原生与设备。
未改动共享内核。未做 git 操作。他人编辑全部保留。

## 1. 本轮校准与撤回

根复核给出四条校准。本报告据此修正前版判定。

- 校准一：记录证据滞后属已知 UNRUN 闸门，不是当前源码阻断项。据此 G1 降级。
- 校准二：120/364 冻结属有意设计。草稿提升在 OHOS baseline 通过前禁止。据此 G2 降级，且本轮不提议改动。
- 校准三：构建、归档、签名、设备为四条有意分离的闸门。`archiveInspected = false` 属设计，不是缺口。据此 G3 降级。
- 校准四：前版称 inspector 无法发现陈旧源，属错误。据此撤回 B3。

### 撤回 B3 的确切理由

前版把「wrapper 复用旧 HAP」列为最严重项。该判定错误。

inspector 第 193-199 行按当前 Dart 源字节逐份比对 kernel。
字段为 `payload_present = bool(data) and data in kernel`。`data` 取自当前磁盘源。
若 HAP 陈旧，kernel 内为旧字节，比对失败并追加错误。inspector 不会静默接受源码变更。

HAP 未变且源也未变时，复用同一 HAP 字节并通过属正确接受。
校准明确指出：字节复用本身不构成失败理由。

关于 runtime 侧同一问句的复核结论：
第 137-164 行先把打包 SO 绑定到暂存 SO 或 SDK strip 变换。
第 164 行再把暂存 SO 绑定到 openharmony 构建记录。
第 75-97 行把构建记录绑定到当前原生源哈希。
因此陈旧 runtime 在原生源变更时会失败。在原生源未变时通过属正确。

结论：未找到陈旧 HAP 或陈旧 runtime 的可执行绕过路径。B3 撤回。

## 2. 结论

在受审范围内未发现源码阻断项。三条前版阻断项降级为意图性闸门或延迟项。
两条非阻断观察保留为维护性风险。两条低危标注与覆盖缺口保留。
所有 runtime 闸门状态为 UNRUN。本报告不主张任何运行时结论。

覆盖方向说明：本审计只找「错误接受」。不接受「错误拒绝」作为阻断项。

## 3. 受审文件与当前哈希

| 文件 | SHA-256 | 写入时间 |
| --- | --- | --- |
| `tool/build_go_catalog_audit.ps1` | `fe792511b0f9fe4329c13ae75c9613768ad79ef5bad13fbf1d66fea5e954d21b` | 2026-10-25 23:55 |
| `tool/inspect_go_catalog_hap.py` | `f8cb0e5af02ca2bc700d759e70c7795b56696334803c51d6400430350148c3a8` | 2026-10-25 23:59 |
| `.trellis/tasks/10-22-go-offline-ide/research/fixtures/inspector_binding_review.py` | `b6e65a11d4fb423877607ad79ca634f2bf8d318e131013e7a813f1ebcbcd84af` | 2026-10-26 00:09 |
| `.trellis/tasks/10-22-go-offline-ide/research/fixtures/profile_lock_review.py` | `bc0216d2506fd32d91d8b8274291723be644248d737bf2f3adb417f2caa8f749` | 2026-10-26 00:18 |

解析结果：三份 Python 文件 AST 解析通过。PowerShell 文件语法解析 0 错误。
解析工具为 `ast.parse` 与 `System.Management.Automation.Language.Parser.ParseFile`。
两者只读文本，不执行目标脚本。

## 4. 三方绑定的实际形状

链条分三段。每段各有守卫。守卫都失败即拒绝。

1. 源码 → 构建记录。wrapper 第 37 行取三份 Dart 源哈希。第 97-101 行在构建后重取并比对。
2. 构建记录 → HAP。wrapper 第 106 行取 HAP 哈希。第 116 行写入 `hapSha256`。
3. HAP 字节 → 源码字节。inspector 第 60-72 行、第 193-199 行完成。校验内容为 kernel 内的源码字面字节与路径。

另有独立证据段。inspector 第 75-97 行校验原生构建出处与五个 ABI。
第 137-164 行校验打包 SO 与暂存 SO、SDK strip 变换与构建记录的三方一致。
第 107 行校验打包资源与当前源资源逐字节相等。

四处二次比对有效。第 207-209 行原生源哈希。第 210-211 行源码。
第 213 行 HAP。第 215 行构建记录。第 157 行 strip 工具哈希。

口径标注一致。wrapper 第 121-123 行与 inspector 第 230-231 行都写 `false`。
三项为 `signatureVerified`、`archiveInspected`、`deviceExecution`。
这些字段与 spec 第 356-359 行的分离要求一致。

## 5. 意图性闸门与延迟项

以下三项不属当前源码阻断。它们记录闸门状态与验收契约。

### G1 记录证据滞后（UNRUN，已知闸门）

磁盘上的两份证据早于当前源码。

- `inspector-binding-review-20261023.json` 记 `inspectorSha256` = `fd8837c0…b655c`。当前为 `f8cb0e5a…c3a8`。
- `profile-lock-review-20261023.json` 记 `wrapperSha256` = `462894fc…9c40f`。当前为 `fe792511…d21b`。
- 两份证据写入时间为 2026-10-23 05:15 与 05:26。当前源码写入时间为 2026-10-25 与 10-26。
- 旧证据缺少当前 fixture 新增的用例。缺 `missingNativeExit`、`syntheticSourceBinding`、`syntheticSourceDrift`。缺 `negative/audit-build-*`、`negative/stale-source/*`、缺失操作项与 IDE/UI 标记项。

历史记录还显示同一文件哈希多次漂移。`16a1db6f…`、`fd8837c0…`、`19377bbf…`、`5dccdad8…` 均指向 `tool/inspect_go_catalog_hap.py`。
出处为 `offline-host-review-20261023.md:56`、`independent-packaging-review-20261023.md:171`、`go-target-ide-acceptance-source-handoff-20261024.md:137`、`go-target-ide-acceptance-source-check-20261024.md:180`。

本条属已知 UNRUN 闸门。不是源码缺陷。本轮不改动任何脚本。

### G2 覆盖率闸门冻结 120/364（现在禁止提升草稿）

inspector 第 54 行固定默认值 `expected_topic_count=120, expected_case_count=364`。
第 112-114 行按 `T001..T{n}` 连续区间与精确案例数双重校验。

当前实际值与默认值一致。`assets/curriculum/audit-manifest.json` 为 120 题、364 案例。
扩写草稿已备 160 题，编号 T121–T280 连续。位置在 `research/expansion-draft`。
`tool/go_curriculum/topics` 仍为 120 题。

该冻结属有意设计。OHOS baseline 通过前禁止提升草稿。
本轮不提议改动默认值，也不提议改动 fixture。

提升时机的验收契约见第 8 节 A2。fixture 第 131 行未传计数，继承默认值。
fixture 第 176 行的负向期望串由 f-string 插值生成，随默认值自洽。

前序审计已记录同一前置条件。`independent-packaging-review-20261023.md` 要求扩写后刻意更新该闸门。
该前置条件尚未到期。草稿提升后案例数由 `build_manifest` 逐课时展开计数。
该数值在静态审计下不可得，记为 UNRUN。

### G3 四条闸门有意分离（`archiveInspected = false` 为设计）

wrapper 第 121-123 行写 `signatureVerified = false`、`archiveInspected = false`、`deviceExecution = false`。
inspector 第 230-231 行写 `signatureVerified = false`、`deviceExecution = false`。

这是设计选择，不是缺口。四段为构建、归档、签名、设备。
`build_go_catalog_audit.ps1` 只负责构建段。它不调用 inspector 属分段边界。

全仓只有 fixture 通过 `importlib` 加载 inspector。位置 `inspector_binding_review.py:30-33`。
`build_go_catalog_audit.ps1` 第 122 行的 `archiveInspected = false` 如实声明归档段未跑。

后果是归档段由人工触发。这是编排归属问题，不是源码缺陷。
归档段闸门与验收契约见第 8 节 A3。

## 6. 非阻断观察

### O1 两份源清单一致性（维护性，失败即拒绝）

wrapper 第 18-24 行硬编码三份 Dart 源。inspector 第 29-33 行另写一份。
两侧只靠注释互指。wrapper 第 19 行与 inspector 第 28 行各有一条注释。

是否构成错误接受？否。两侧差异经构建记录交叉校验后失败。
inspector 第 71-72 行比较 `audit_build.get("auditSources")` 与由自身清单算出的 `source_hashes`。
两侧清单不等时，两边字典必不相等，inspector 拒绝。
两侧清单相等时才继续 kernel 逐份校验。

因此本条只属维护性风险。它失败即拒绝。未发现具体错误接受路径。
本条不作为阻断项，也不要求本轮改动。

### O2 外部进程所有权（政策缺位，不推荐通用超时）

第 147 行 `subprocess.run` 未设 `timeout`。第 167-168 行 `check_output` 未设 `timeout`。
`readelf` 与 `llvm-strip` 挂起时，校验会长时间等待。

对照 `tool/go_curriculum/audit_native.py` 的 `bounded_run`。该处有超时、进程树终止与句柄兜底。
两处标准不一致。

本轮不推荐给 inspector 补通用 `timeout` 或进程树终止。
理由：本仓无统一 kill/reset 政策。通用超时会掩盖所有权归属。
正确归属是进程生命周期闸门，由该闸门所有者定义政策。
本条记为 UNRUN，等待政策，不做代码建议。

### O3 字段标注歧义（低危，失败即拒绝）

第 139-146 行存在字段歧义。当 `data != staged` 且 `llvm_strip` 为 `None` 时：
`transform` 仍写 `identity`，`verified` 为 `false`。

第 159-161 行随后追加错误。因此本条失败即拒绝，不构成错误接受。
风险只在读证据者的标注理解。`transform: identity` 与 `verified: false` 并列时，
读证据者可能误判为「已按恒等变换校验失败」。
实际含义是「未尝试变换」。验收契约见第 8 节 A4。

### O4 inspector 退出码覆盖缺口（低危，失败即拒绝）

第 167-177 行若 `readelf` 返回 0 且输出为空，导出集为空集。
随后九符号全缺，报 `missing Go ABI exports`。逻辑上等价拒绝。
该行为正确。但没有 fixture 固定它。
`inspector_binding_review.py` 的负向用例全部针对 ELF 头、ABI 集合、符号之外的因素。
覆盖契约见第 8 节 A5。

## 7. 缺失原生退出码处理

分两侧结论。

### 7.1 wrapper 侧：已处理，且有覆盖

第 91 行先置 `$LASTEXITCODE = $null`。第 94-95 行判空后抛错。
`profile_lock_review.py:184-190` 用 `.ps1` 假 flutter 覆盖此路径。
该假命令不产生原生退出码，wrapper 必须拒绝。用例名为 `missingNativeExit`。

同一 fixture 第 112 行用 `.cmd` 假命令覆盖正常非零退出。断言串为 `build failed: 7`。
两侧合起来，退出码缺失与退出码非零都有守卫。

`ErrorActionPreference = 'Stop'` 对原生非零退出不抛错。这就是显式判空存在的原因。
该组合正确。

一处值得记录的边界。第 91 行重置到第 92 行调用之间没有其他语句。
若将来插入语句，重置点会失效。这一点无 fixture 保护。属维护性提示，非阻断项。

失败方向复核：若 `$FlutterExecutable` 解析为 PowerShell 脚本或函数，
PowerShell 不设 `$LASTEXITCODE`。此时变量保持 `$null`，第 94-95 行拒绝。
失败方向正确。

### 7.2 inspector 侧：结构已处理，覆盖不足

`readelf` 非零退出抛 `CalledProcessError`。第 256 行捕获 `subprocess.SubprocessError`，报 `success: false`。
`llvm-strip` 第 147 行带 `check=True`，非零同样进入失败路径。

零退出但输出错误的路径同样失败。细节见 O4。
因此 inspector 对缺失原生退出码是失败即拒绝。本条不是阻断项。
唯一缺口是用例覆盖。契约见 A5。

## 8. 可执行验收契约

每条契约给出可执行判据与闸门状态。

| 编号 | 契约 | 可执行判据 | 状态 |
| --- | --- | --- | --- |
| A1 | 证据现行性 | 重跑两份 fixture。新证据记 `inspectorSha256` 等于 `f8cb0e5a…c3a8`。记 `wrapperSha256` 等于 `fe792511…d21b`。两份都 `success: true` | UNRUN |
| A2 | 扩写闸门提升 | OHOS baseline 通过后才提升草稿。提升时把默认值与 fixture 计数改为传参。断言 `audit-manifest.json` 的题数/案例数等于传入参数 | FORBIDDEN 现在 |
| A3 | 归档段闸门 | 用真实 `readelf` 与 `llvm-strip` 对保留 HAP 跑 inspector。报告 `success: true`。`archiveInspected` 由该闸门所有者翻转 | UNRUN |
| A4 | 字段标注 | `transform` 仅在恒等比对成功时写 `identity`。未尝试变换时写 `untried` 或同类标记 | UNRUN |
| A5 | inspector 退出码覆盖 | 增补两条负向用例：`readelf` 恒定非零、`readelf` 恒定空输出。两者都必须失败 | UNRUN |
| A6 | wrapper 退出码 | 复用 `missingNativeExit` 与 `build failed: 7` 两用例。保持通过 | 已有覆盖 |

契约边界：A3 与签名校验、设备执行保持分离。本报告不合并四段。
本报告不主张 A3 通过就等于签名或设备通过。

## 9. runtime 闸门（全部 UNRUN）

| 闸门 | 状态 | 说明 |
| --- | --- | --- |
| `build_go_catalog_audit.ps1` 执行 | UNRUN | 需 flutter 与 OHOS 构建环境 |
| `inspect_go_catalog_hap.py` 执行 | UNRUN | 需真实 HAP、`readelf`、`llvm-strip` |
| `inspector_binding_review.py` 执行 | UNRUN | 需 `--readelf` 与 `--strip` 真实工具 |
| `profile_lock_review.py` 执行 | UNRUN | 需 `pwsh`、dart、java、node |
| 原生构建出处 `native/build/bundled-go-runtime-build.json` | 缺失 | inspector 默认路径不存在 |
| HAP 签名校验 | UNRUN | 两处都硬写 `false`，属分离设计 |
| 设备执行 | UNRUN | 两处都硬写 `false`，属分离设计 |
| 扩写后案例数 | UNRUN | 需 `build_manifest` 实算 |
| 真实原生源哈希 | UNRUN | 需 `native_source_hash()` 执行 |

`native/build` 目录存在但无 `bundled-go-runtime-build.json`。
该文件是 inspector 第 239-240 行的默认出处路径。缺失时 inspector 必然失败。
该文件只能由原生构建产出。审计者不得代造。

## 10. 与 spec 的对照

`.trellis/spec/backend/native-go-runtime.md:356-359` 要求两件事。
wrapper 必须在失败时还原入口 profile 原始字节，并拒绝并发改写。
inspector 必须校验资源、runtime 字节、ELF ABI 与九个导出。

本次校验结论：源码层面两条都已实现。
第 127-137 行的 `finally` 先判并发改写，再还原，再复验哈希。
第 106-177 行覆盖资源、runtime 字节、ABI 与九个导出。
spec 未要求的前置条件有三条：A1 证据现行性、A2 扩写闸门、A3 归档段闸门。
三条都属闸门归属，不属源码缺陷。

## 11. 明确未做的事

- 未执行 `build_go_catalog_audit.ps1`。未调用 flutter。
- 未执行 `inspect_go_catalog_hap.py`。未读任何真实 HAP。
- 未执行两份 fixture。未造合成 HAP。
- 未执行 `native_source_hash()` 或 `build_manifest()`。
- 未打开设备。未做签名校验。
- 未改动 `tool/`、`assets/`、`native/`、`ohos/` 与共享内核。
- 未做 git 暂存、提交或推送。