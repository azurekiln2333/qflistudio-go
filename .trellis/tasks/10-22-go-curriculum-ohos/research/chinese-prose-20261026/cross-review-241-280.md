# 交叉评审：T241–T280（2026-10-26）

评审人：散文交叉评审者。只读评审。只写本文件。
范围：`expansion-draft/topics/T241.json` 至 `T280.json` 共 40 题。
对照物：`before/T241.md` 至 `T280.md` 原投影、`after/` 当前投影、`samples/T241..T280/main.go`、`independent-semantics.md`。
本轮没有编辑任何 JSON 与投影。没有 git 操作。
未跑程序、SDK、编译器、原生测试、WSL、设备、渠道命令。

## 1. 结论

评审项全部落实。三项不变量成立。长度上限全部通过。一句一动作未全部通过。

判定：**不是无条件通过**。给出限定结论。

- 语义纠错 5 项：全部已按建议改正，逐项与程序对得上。
- 一句一动作点名项 3 项：全部已改。
- 已接受判断 3 项：全部成立。
- 不变量、结构、长度：全部通过。
- 剩余缺陷：2 处明确，3 处轻微，另有 1 批继承项。

## 2. 不变量与结构

| 校验 | 结果 |
| --- | --- |
| 不可变掩码哈希 | 40/40 相等 |
| 逐字段情态计数 | 40/40 相等 |
| 样例文件哈希 | 40/40 相等 |
| 投影键序与 `mutablePaths` 一致 | 40/40 相等 |
| 投影内容与 JSON 一致 | 40/40 相等 |

掩码规则：逐个 `mutablePaths` 叶子替换为 `<MUTABLE_CHINESE_PROSE>`。数组下标是整数。
序列化用 `sort_keys` 与逗号冒号分隔。40 题全部复现通过。

投影内容比对先做行尾归一。本范围投影用 LF，T201–T240 用 CRLF。
两者内容一致。行尾差异不影响 JSON 语义，仅记录为观察项。

## 3. 机械扫描

| 阶段 | 发现 | 硬违规 |
| --- | --- | --- |
| `before/` 上限 25 | 有发现 | 有 |
| `after/` 上限 40 | 0 | 0 |
| `after/` 上限 25 | 0 | 0 |
| 字段级审计：指令 ≤25 | 0 | 0 |
| 字段级审计：说明 ≤40 | 0 | 0 |

对照组：`before/T241.md` 在上限 25 下报出 6 条。说明 linter 正常读取本范围。
`after/` 在 40 与 25 两档都是 0 条。本范围全部 `被` 字计数为 0。
字段级审计把 160 个指令字段与 360 个说明字段分开送检，各自 0 条。

零 linter 不等于通过。下文第 7 节列出 linter 查不到的缺陷。

## 4. 语义纠错逐条复核

| 编号 | 位置 | 现状 | 判定 |
| --- | --- | --- | --- |
| S1 | T247 四字段 | 改为「文本占用的终端列数」 | 已解决 |
| S2 | T241 `explain` 末句 | 改为「避免把半成品报告作为完整结果输出」 | 已解决 |
| S3 | T271 `pitfalls.1` | 恢复「缺失或错账」，保留「可能」 | 已解决 |
| S4 | T265 `pitfalls.1` | 改为「名字编码本身不是完整查询」 | 已解决 |
| S5 | T277 `answer` | 增补「再把对应操作应用到该副本」 | 已解决 |

程序对照：

- S1：`cell` 按 `[]rune` 截断，用 `utf8.RuneCountInString` 计算填充。确实按 rune 计数，不是显示宽度。新表述准确。
- S2：程序用 `bytes.Buffer` 加 `fmt.Print`，不打开文件，也不做替换协议。原文没有文件覆盖语义。新表述准确。
- S3：程序分别输出 `missing-left`、`missing-right`、`mismatch` 与重复标记。错账就是 `mismatch`。恢复该词后覆盖完整。
- S4：程序只有 `encode` 与 `decode`，全程离线。新表述只谈编码不完整，不引入发送动作。准确。
- S5：程序先复制 `stock` 到 `next`，逐项校验存在性，再写回。新表述补上「应用到副本」，与程序顺序一致。

## 5. 一句一动作点名项复核

| 位置 | 现状 | 判定 |
| --- | --- | --- |
| T266 三字段 | 「它能缓存半帧。也能输出多帧。」 | 已解决 |
| T268 `pitfalls.1` | 「权限位编号用于持久化协议后，重排名称就会改变数据语义。」 | 已解决 |
| T250 `prompt` | 「增加百分数文本。零总量仍输出 n/a。」 | 已解决 |

T268 只丢了一个「已有」。语义不变，因为协议已经持久化，改的必然是既有数据。
T250 与程序一致：`total <= 0` 时返回 `n/a`。
T266 与程序一致：`Pending` 缓存半帧，`frames` 一次可返回多帧。

## 6. 已接受判断项复核

| 位置 | 复核结果 |
| --- | --- |
| T242 `&amp;` | 行内代码只包数据字面量，没有藏散文。程序用 `html/template` 转义，`&` 变 `&amp;`。成立 |
| T257 十的倍数 | 整数加权和模十等于零，与 `能被十整除` 等价。校验位在求和范围内，已显式写出。成立 |
| T260 RuneError | 保留「RuneError 加大小为一」的合取。程序正是 `r == RuneError && size == 1`。成立 |

## 7. 剩余缺陷

### D1 明确缺陷：T259 三字段以「并」开头

位置：`tutorial.summary`、`tutorial.objective`、`example.summary`。

现状：「能用栈校验多类括号嵌套。并返回首个错误字节位置。」

问题：「并」是连词，不能起句。这里把原句的「，并返回」拆成「。并返回」，产生了残句。
这正是评审对 T268 指出的同一类问题。本轮改动引入，属于回退。

建议：合并为一句，或改写成「它还会返回首个错误字节位置。」

### D2 明确缺陷：T274 objective 复合动作与重复

位置：`tutorial.objective`。

现状：`能读取包文件清单并检查三项内容。三项是存在、长度和摘要。全部错误一起聚合。`

问题一：`读取并检查` 是两个动作。objective 属指令类。
问题二：「三项内容」与「三项是」重复，读起来是残句加解释。
事实无误：程序确实校验存在性、长度与 SHA256。汇总全部问题后才输出。

建议：「能读取包文件清单。逐项校验存在、长度和摘要。最后聚合全部错误。」

### D3 轻微：三处以「并」连接两个动作

| 位置 | 现状 | 建议 |
| --- | --- | --- |
| T255 `answer` | 先分离并校验构建标识。 | 先分离构建标识。再校验它。 |
| T267 `answer` | 保存 Used 并比较变化。 | 保存 Used。再比较前后变化。 |
| T247 `answer` | 再转换并填充。 | 保留。截断与填充是同一函数的两个步骤 |

前两处是两个动作，建议拆开。第三处判为可保留，因为 `cell` 一次完成转换与填充。

### D4 继承项：一句一动作的历史缺口

这些字段本轮没有改动，缺陷来自改写前。列出以便定责，不构成本轮回退。

| 类别 | 数量 | 位置 |
| --- | --- | --- |
| 指令字段含逗号加连接词 | 9 | T245 objective、T245 prompt、T248 prompt、T262 objective、T263 prompt、T265 prompt、T270 prompt、T277 prompt、T278 prompt |
| 指令字段含「并」无逗号 | 8 | T243 objective、T251 objective、T255 objective、T256 objective、T263 objective、T267 objective、T267 prompt、T268 objective |
| 指令字段含内逗号 | 45 | 见附注 |

附注：45 条内逗号句里，绝大多数是两个动作。例如 T241 objective「能注册分币格式化 FuncMap，渲染订单明细与总价」。
若按根对 T201–T240 采用的标准，这些都应拆成一动作一句。
本轮改动只涉及其中 4 条，且这 4 条都不是新增的复合动作。

## 8. 技术含义抽查

逐题读过程序并对照文本。覆盖全部点名题目，共 16 题。

| 题 | 校验点 | 结果 |
| --- | --- | --- |
| T241 | 整数分、Funcs 先注册、缓冲后输出 | 一致 |
| T242 | `html/template` 转义 | 一致 |
| T245 | `MarshalJSON` 只改输出，内存原值不变 | 一致 |
| T247 | 按 rune 截断与填充 | 一致 |
| T250 | 零总量返回 `n/a`，超额与负数归一 | 一致 |
| T255 | 核心与预发布分段，构建元数据不参与排序 | 一致 |
| T257 | 十三位、前缀 978/979、权重 1/3 交替、模十为零 | 一致 |
| T259 | `中(a]` 的错误字节偏移为五 | 一致 |
| T260 | `RuneError` 加大小为一判坏编码 | 一致 |
| T265 | 长度前缀编码，末尾零点表示根 | 一致 |
| T266 | 缓存半帧，一次可返回多帧 | 一致 |
| T267 | 位图分配与重复释放拒绝 | 一致 |
| T268 | 交集、并集、差集与撤销 | 一致 |
| T271 | 缺失、重复、金额不一致三类输出 | 一致 |
| T274 | 存在性、长度、SHA256，汇总后输出 | 一致 |
| T277 | 副本上校验与执行，最后统一提交 | 一致 |

未发现新的语义漂移。第 4 节 5 项纠错没有引入新错误。

## 9. 当前题目哈希清单

题目 JSON 与 `after/` 投影的 SHA-256。评审快照如下。

| 题 | 题目 JSON | 投影 |
| --- | --- | --- |
| T241 | `05575dfea73741867d98b64bec94c49e42d78a635cc0e2e12ecdac680e2cb253` | `ebf2486831056970c9341d508dbd49cbe687568d8b996f36b1a1a3bd862de2a5` |
| T242 | `17962ddf652d7c9da2d436290b9ce1bd62c69e3ecd765c73e73576d3059f32e1` | `05758ce341b54d2c0f84ab7eba496498407dd73f9666d6ebc947ae29560e0d66` |
| T243 | `d612c99f4182d5585f47dc73b101e9b65892efa0ccbb7611f972bd0bb11bec7d` | `781746a051c2a7e61bdbcc410b6c03d5608e03debb7aa792f5f120bbff933065` |
| T244 | `7bd23ab7d71a9c112d74dbe20a8d166f3f996b54036f3614f9ad7458f46c4d5b` | `a60cdab30deddb86e28c9091b8e8ccd0f23f3cfe88ca29c9a8bd78e3424f853b` |
| T245 | `2165280a6752ae0bd29622cfbf39f6259e8e114914a29997ed20cdc2e3f6df0b` | `ef335ebfc2b855d50c2268b1dcb0720f2122fd8f6750d16dbfffad7f768e7517` |
| T246 | `efaa4bc53beef4df680b74fe95136038a82775b2233af0803f018f1c37a7312a` | `5248beb2d7afe4c735d925565bf4c7c84bf39acdfd80995d9217581759c6fd7c` |
| T247 | `730031ce98c76ab7313627e188ca57e7f633aab5180aa15515e0196113b42c5d` | `a0cf5a7aaffce7039650644ec1629b94d5b2d67c60231e9790e13f3cf6026a3a` |
| T248 | `0cdd95cc425ac2beebc02bb004dbc5e35f78e150e85d1c5778a80e310bbe258e` | `5831433bb678d1b6b59c8b1e58bc2979b76412e316f84df306ef01ba8a2b7521` |
| T249 | `ee99fd02d7bc86ddc18fea42bb89d352f768963db845153b0435900464061837` | `3f2e660d8927b4bd933ee54ed9b10bdb3afe194f07b7f7c1a08425efb853fdc9` |
| T250 | `ab04b490335626fd452a637cc7adba5a7651fe41609d745a01696b16e2aeab6b` | `ad39cffa26897375ce1c06f91795d681f133aa0c9f16ab29236e4a449cf08cdb` |
| T251 | `0903f54f0b7709317f4c238d51e49d9b02afcb391d5afc6ce802af8513e1c8d4` | `2505162526670897128b750c75e14f89cdb57c44c5623a26e0c693439cea11ee` |
| T252 | `27e8578fec67083883ebf7fad1c3cd305e83c4d97d7cdd8bbd01cc0c06cd249e` | `08ad6eba8eea08058426ec30453c9408206d2db25567b7d5bfdb967bdb237c5d` |
| T253 | `7e6059b7b4da56fd5d9be13ce395bfd5ad8c480c1e66a5ccfc47c78bdae8e726` | `18ab8b07407dcfab47b05b2918d12d84b70bdfc5c866b3dd0a195bfab467ba5d` |
| T254 | `dd3e5d35208829075ed410b6609661bf9c6caa1221a4bd52dd835fe58c413169` | `535558c7708df984515040734387764055c0986face5ad715a61be32e9a08465` |
| T255 | `5870421dce22be92ea8463aaa573757f6a8b39edc1369fe81cc55a20049963a7` | `9af00a51af4e69e8b015ea3bd5d46e115b272c3fe94ac98bd12250ca7480c683` |
| T256 | `a8be89a00bd006b5b4bb2f0ef06e83499d9297b5d331746ddcf825ef98fd32f0` | `f372d1eea5d0527b242a78db1f19350f5266f818c3251d7aaf88f428b4d02b84` |
| T257 | `0e01ba9454a34fe2f439f478256f4b787c5bcae1b8b21efaeb7ecf74d38408dc` | `a42d21ad0e056c47e57cf9d4048ae2fb05eeab49c19f81ff3385e71f61146466` |
| T258 | `6dc4f1cbbde14d38689e0e74f1e12dc94b35e3a0e1c780e6a720ca38906a2c83` | `16548692ccb525c0a02b20eb4a3223c915fe951548d2ca3d4d63da7a50ebc0ca` |
| T259 | `811e55dd6614ae389d968104e40307a33ec6f54466e916941bea655db5608422` | `cfe82d0766cbbb4ec5007e41579246a71d2313c8183480a770889ee81b6636f1` |
| T260 | `10a0fe857b0067887169f4b95a6a98c0382cddffff309c372f130528dc9b3a9b` | `cd805a249b1e962eeb2057fe704af8de4aa6ac9c2095d3cee2ccb8cbb0c5e53a` |
| T261 | `d62f731419598eb53bb56e33ccf6a9e4b9a15f29835c8799fe0c78b9b18d9618` | `e1a4dcbb8c7bfb3c41d9f70acf04c6d23bea5c6d28221e5071c08797bb72528d` |
| T262 | `e1e229388e92ad320586a2d4dbd457e019c47845efb5d1a77ff30cbcdcfd5aea` | `c4669832329c4217cfbc07afb46fc380a79539cf7a71a36caa4d07c47d2851b3` |
| T263 | `f7076a893f6aa1283887185ce15469db206d1211fc46991d12092854c1543569` | `a77a641ae5e98cf1ffd064ba83840a6fd6f5202222169733528c411e622bb9d1` |
| T264 | `b0483f3c36a0e51dce452c75052ba4e49e7f6f64adf3e12c263391e07cf14683` | `c0a0d972325a1a6ed384855c1e37834961a6fdfcfc20b60a2305293b670aa6b0` |
| T265 | `d67de2a109ed3983af87db2debc1851cae78b61543a946cbf94d14f9ddbd1296` | `c0b6e4a829a0a47d912ac6c372c3c0ec3190af5e9c7bf98e210f4cbfbdef0211` |
| T266 | `55710adb386576a5d4c0a073dd6078ee0da7cf930948996d9fa374b37461ba6d` | `91552fc56bf2138effcaab7d5b4dd7bb69ecd1844aafc95a077bbdd5359c7e32` |
| T267 | `5c48a55b8dc305c3313b4b2bb2d62118c7e9ba8ef61231e0af68c4e688948ce0` | `f9f7a9165553c170d7d6e99224e8e115224cc8b499840ff7026c76bc08926867` |
| T268 | `c60f84a3bf58d297b463243a97a51999f4000cce05f71368f17dbdafd0e4f31d` | `37c3578a465e4ecf5e348b8eacf81d2216f10ffcd5fa4dd13dc2a305e3b5745e` |
| T269 | `c5e40e6e3d5b2da660a8331c9c02fbcc4dc3faf8e3c9f7b934cef2af0b47a321` | `3174ccec5e8c116bf09622c583761aa9523e80964a0f3185d906333b342abc19` |
| T270 | `1344d6f0ddaeeca93e62dfc0d96d4655a336bd5b2360caa92bafec06db7c4836` | `cd03b7edb2493e6b1a0c67bd79460ace956f63ade5f4635621ed2b40dc160efc` |
| T271 | `5b037eb004d7fc648c64a3e87146163f9d494230e94d46d142a4215a1425ccd3` | `582ced67b260fac1fa60f9d0fdb7081254d09b3d7eb434298342db36d640067b` |
| T272 | `ee110358141a5f0e7eba7ed5f562878d482acce6524ec9cbc34cda007b0cd352` | `74d4d3887afbbb8f200bb3b94ce5d3048af3f696c181ec5e9f67c0fa1a91c18f` |
| T273 | `94fe848ae182e98c007cf38dd163c7c8cab7a6c2979f44fbeef3dabb10993152` | `18b4bcc6942bd4d33f8a457c9f9b665f08652b382e938bbe613dc4b538788e21` |
| T274 | `982b6bc3ebe4c7702d9ea8eed7979082b2415ee59cedc519e31225d81c34157c` | `de69fbc69bf4a1fd09d0f6e7991cdd7d28c851b1ec3e1534b47a26aa22be0a07` |
| T275 | `32ec15ecc36b2e53d3868917a4a570e486975dff6afcd95aadc058e24ef284aa` | `0502eff8ccb291ef0a6fe986d11926faa833b6ef8c5f476f499b15e217bf15b1` |
| T276 | `0645535fa87e651ea870a214a3003be5b9062b94d11c3cf4bf24da3774f8ed48` | `312467d84e6e004ada98bf02c84a90a9153746472a7efddd19cb0ddcc42e2140` |
| T277 | `a714a4447bc5ecb20b3b0978ddba91862139820cce2b0cb9f0ce12033e7d6a8d` | `bf4410e1e7038ec3977207ef6163e7bf98f155206265d610055458da7d739fe8` |
| T278 | `b7a6c8824f3e4fb5dadc5ddfc744f588a926dd73c5e98139294b1b8ef096decc` | `60e2fb51c0d01e775a0265add7a6c517b636d055196ed85fce836c3fb07c1dfd` |
| T279 | `7759200de697be43a1b01e658efbf0517fe94623ff01a4b24de0c13c778205ea` | `e3a859f814b0d2b44230985422baaf6070e942d5e06d94f93bacd44f6acfc9c0` |
| T280 | `949a1c755fd8d8bb9ffcafc4e38e5bbf6fb6cf55c451d075cfca5c3fdbb16c3b` | `c9dc6e0bae0db2bc1e6e884a6cf6c720e8f60a67c8b5d48b9208b88689fa6fc6` |

题目哈希聚合值：`b6bf31a6599a1084019635800520e6c3e49c00a0becceaf51c86dd25f8ca7361`。

聚合口径：按题号排序，每行取「题号 加空格 加题目 JSON 哈希」，用换行连接，再取 SHA-256。
其他评审可据此确认评审快照。本轮之后若有人继续编辑，哈希会变。

## 10. 复现口径

不变量与结构：

```text
python <临时目录>/xr_invariants.py
python <临时目录>/xr_final.py
```

投影内容比对先做行尾归一，再与 `mutablePaths` 顺序逐字段比对。

机械扫描：

```text
python scripts/ste-lint-zh.py --max-chars 40 <40 个 after/T2xx.md>
python scripts/ste-lint-zh.py --max-chars 25 <40 个 after/T2xx.md>
python <临时目录>/xr_len.py
```

一句一动作三种口径：

```text
python <临时目录>/xr_oneaction.py
python <临时目录>/xr_classify.py
python <临时目录>/xr_bing_instr.py
```

## 11. 边界

- 只读评审。未编辑 T241–T280 的 JSON 与投影。
- 只写本文件。其他同伴的编辑全部保留。
- 未跑任何目标程序。程序对照只做源码阅读。
- 未跑 SDK、编译器、测试、构建、WSL、设备与渠道。
- 未做 git 暂存、提交或推送。
- 聚合资源、样例执行与 `audit-manifest.json` 未触及。上述闸门为 UNRUN。
- 本文不构成产品验收结论。最终验收须由责任方在修完 D1 至 D3 后重新比对。
