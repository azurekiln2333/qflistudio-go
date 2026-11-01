# Independent semantics review: T121–T200

Snapshot UTC: 2026-10-25T23:27:33.839135+00:00

Status: **CHANGES REQUESTED**. Reviewed the frozen before projections against the current Chinese prose for all 80 topics. Read source samples T128, T132, T142, T144, T161, T170, T185, T187 and T200 to resolve technical meaning. No program was executed. Paired tutorial/example title, summary and concepts agree in all 80 topics.

The numeric/identifier multiset checks do not prove semantic preservation. They miss a changed noun, a lost condition, a changed warning, and mathematically wrong units that already exist in the baseline.

## Introduced findings: do not accept unchanged

### S1 — T142 tutorial.pitfalls.1: writing order replaced physical storage order

- Before: `环形存储顺序不是时间顺序，导出时必须从最旧槽位开始。`
- Current: `环形写入顺序不是时间顺序。导出时必须从最旧槽位开始。`
- `存储` and `写入` are different concepts here. The source appends a, b, c, d chronologically. Its physical slots become d, b, c; Snapshot walks b, c, d. The array layout differs from chronology. The write sequence itself remains chronological. Replacing the noun makes the warning false.
- Suggested prose: `槽位顺序不是时间顺序。导出时必须从最旧槽位开始。` Use a physical-layout term. Do not unify storage and write operations merely to satisfy a synonym rule.

### S2 — T128 tutorial.pitfalls.0: removed the no-allocation mechanism

- Before: `Buffer 的初始切片容量若已经大于业务上限，可能让较长 token 无需扩容就被接受。`
- Current: `Buffer 的初始切片容量若大于业务上限。程序就可能直接接受较长的 token。`
- Splitting leaves an incomplete condition. Replacing `无需扩容` with `直接` loses the actual reason the configured maximum can be bypassed: the existing backing buffer already suffices. The sample intentionally uses initial capacity4 and maximum12; the pitfall explains the different configuration that invalidates the budget assumption.
- Suggested prose: `Buffer 的初始切片容量若大于业务上限，较长 token 可能无需扩容就通过。` This can use the explanation limit40. If further splitting is needed, retain both the condition and `无需扩容`, and keep exactly one `可能`.

### S3 — T127/T159 tutorial.pitfalls.0: warning conditions became standalone bad instructions

- T127 current: `把两份文件相同行号直接比较。会把插入之后的所有行误报为改变。`
- T159 current: `只合并直接共享邮箱的两项而不追踪传递关系。会漏掉间接连接。`
- Both original sentences described an incorrect operation and its consequence. A full stop now isolates an apparent imperative for that incorrect operation. A warning should explicitly prohibit the operation or keep its conditional scope.
- Suggested T127: `不要按相同行号直接比较两份文件。插入行会让后续所有行误报为改变。`
- Suggested T159: `不要只合并直接共享邮箱的账号。忽略传递关系会漏掉间接连接。`

### S4 — T132 title/explain and T185 explain: majority terminology is not concept analysis

- T132 changes `人工核对编号` / `手工核对` into `人工验证编号` / `手工验证`. Manual reading/comparison is distinct from proving encode/decode behavior or validating a checksum. The source encodes foo, decodes it, and tests case normalization. It supplies no manual verification or checksum algorithm. Preserve a label such as `便于人工核对的 Base32 编号`; use verification terminology only for the actual round trip. This is a precision/terminology finding, not a claim that Base32 encryption was added.
- T185 changes error handling `先检查写入和关闭错误` into `先核对写入和关闭错误`. Checking whether Write/Close returned an error is distinct from comparing the new file content with an expectation. The source checks both error returns before Rename. Prefer `先检查写入错误。再检查关闭错误。` Keep `核对` for comparing expected content if that distinction remains useful. Do not force one word onto two concepts.

### S5 — T200 explain/pitfalls: field-name meaning became vague and in-place patching became ambiguous

- Current `返回排序后的结果键便于稳定展示` removes what the keys represent. The source returns the sorted field names supplied in the patch, even when a supplied value equals the old value. It does not return all result-object keys or detect only genuinely changed values. Prefer `返回排序后的补丁字段名，便于稳定显示。` The old `变更键` was already imprecise; renaming it to `结果键` does not resolve that issue.
- Current pitfall `逐项解码原配置时，后续字段失败会留下部分更新` sounds as though the original config is decoded. The actual risk is decoding patch fields directly into the original config. Prefer `不要把补丁字段逐项解码到原配置。后续字段失败会留下部分更新。`

## Existing technical defects retained by the rewrite

These were present before this prose pass. They are not attributed to the new authors. They still prevent a clean technical-content acceptance and require a separate intentional source-text correction.

1. **T161 tutorial.explain:** `百分之一基点为万分之一` has the wrong unit. The source parameter is `basisPoints`, with `(amount*basisPoints+5000)/10000`; one basis point is one ten-thousandth. One hundredth of a basis point is one millionth. Correct to `一个基点为万分之一。` Numeric/identifier preservation would retain this wrong claim.
2. **T170 tutorial.explain:** `MiB 为一百零二十四平方字节` is wrong. The source multiplier is `1 << 20`, which equals1024², not124². Correct to `MiB 为一千零二十四的平方字节。` Better use `MiB 为 1024×1024 字节。` if that matches the project's number style. This intentionally changes the mistaken numeric prose.
3. **T187 tutorial.exercises.0.answer:** `单文件大小*(组数-1)` confuses number of duplicate groups with number of files in the current group. Correct factor: `组内文件数-1`. A single duplicate group containing three equal files saves two file sizes; the stated formula with one group gives zero. The sample's two groups of two files accidentally conceal the distinction.
4. **T144 tutorial.explain:** `TeeWriter 写入失败会成为读取错误` names a nonexistent helper in this example. The source calls `io.TeeReader(source, digest)`; the relevant failure is its supplied Writer returning an error. Use `TeeReader 的旁路 Writer 写入失败会成为读取错误。` Split further if the sentence-length rule requires it.

## One-action rule remains partly unmet

The specifically authorized common-hint fix is complete: exactly160 topic JSON literals and160 matching after-projection literals changed from `先保持现有输入的结果，再为新边界增加独立输入。` to `先保持现有输入的结果。再为新边界增加独立输入。`. Exact UTF-8 byte replacement preserved every other byte of each file during that operation.

A zero mechanical-lint result does not check the one-action rule. Concrete remaining examples:

| Topic / field | Current sentence | Distinct actions |
|---|---|---|
| T122 explain | `它保留各语言字母和数字，并把字母转小写。` | Preserve characters; lowercase letters. |
| T123 exercise answer | `保留行首或空白前缀，并加入 phone=123 headphone=ok 的测试。` | Preserve boundary; add a test. |
| T124 explain | `它统一小写后累加计数。` | Lowercase; count. |
| T137 explain | `先读取表头并建立索引，确认 quantity 与 cents 都存在，再逐行读取。` | Read header; index columns; check names; read rows. |
| T139 explain | `它记录修改数量后 Marshal，再解码确认库存不变。` | Record count; marshal; decode/check. |
| T152 explain | `Pop 清除底层引用并将 Index 设为负一。` | Clear reference; change index. |
| T160 explain | `查询先走到前缀节点，再递归收集后缀。` | Traverse prefix; collect suffixes. |
| T161 exercise answer | `再对绝对值舍入并恢复符号。` | Round magnitude; restore sign. |
| T168 explain | `先验证并汇总所有非负数量。` | Validate; aggregate. |
| T185 explain | `之后读回新内容并确认替代名已不存在。` | Read content; check old name. |
| T188 exercise answer | `再调用 Rel 生成新链接后验证为 true。` | Generate link; verify result. |
| T191 explain | `每次调用建立独立 FlagSet 并使用 ContinueOnError。` | Create FlagSet; configure policy. |
| T193 exercise prompt | `遍历全部配置来源并收集各层错误。` | Traverse sources; collect diagnostics. |

These examples are not a claim that every use of `并` or `后` is wrong. Conditional guards, coordinated noun phrases and a single atomic result should not be mechanically split. Authors should review the actions and preserve causality, conditions and actors.

## Verification and limits

- Compared before/current prose for T121–T200; no literal text was hidden in newly added code fences or backticks in the observed edits.
- Tutorial/example title, summary and concepts match in80/80 topics.
- Actual source samples were read for the nine topics listed above.
- The frozen immutable/sample/modality audit was re-run after the authorized common-hint correction:160 immutable hashes,160 sample hashes and2272 per-field modality records match.
- After-projection contents match current JSON throughout160 topics. T161–T200 have one cosmetic extra final blank line.
- Linter max40: zero findings, exit0 across160 projections.
- Linter strict max25:113 findings, exit1 across160 projections. All113 are in T201–T280 and outside exercise fields. T121–T200 have zero strict25 findings. These findings are not automatically violations because explanations may use40.
- No Go/native/runtime test, compiler, SDK, WSL, device, channel or Git action ran. No semantic topic JSON was edited. Only the exact authorized common hint and its projections were changed.
- Source hashes below identify the reviewed snapshot. Later author corrections require fresh review.

## Reviewed topic SHA-256

| Topic | SHA-256 |
|---|---|
| T121 | `589f316caae8107370489d560d0eb5ae311714a515e9fd5fb8fa474beeb91927` |
| T122 | `a0fc7ebebe8e608187f1e68e16fa58b2a97b3c415d34b1f572d57170e4fc4a47` |
| T123 | `084152a643d2e4f9149160cfa01dfdc5c3d9b7a39db8ec77cc777839104d4a50` |
| T124 | `019c6d07724a415bb824b8ce2dd90624e04cf648bbcbfe4a9bba1e0054d2ca0e` |
| T125 | `8728fd4e35ab56d56a94410237671d602b6213afbbb956795fc2b3be78c8e022` |
| T126 | `f80871838aea3a2c93b6da3fbd78186e96f7d67dc01d2b865043265aaf2cc22e` |
| T127 | `cd56bd94467494bb656d171b4e3d92a06c7e49cc1e9660e61c64e72e6ec5e15c` |
| T128 | `207bdca8edd17e00d76d3458fcb9ecefa377bc3a09713c98274c0684f5c33d2a` |
| T129 | `be2d45bd8761b287c3970cbb1fe58bb19131f8611e0d41788e5eeebdb0c57946` |
| T130 | `fca9743de28324db5cc9190b3991bb11309d4fa9a41b17a1212332ef9d07158e` |
| T131 | `4ed44d2e0d0a5b445c6c99962b0f7c1b86fecbba001e31e7a1a89c6a9bfd0ccd` |
| T132 | `66357f1bbb5a881fdb5a7eaa68c08ca3d6cd501a96392431849c885dfa0fc2dd` |
| T133 | `71c6a85cae897a8056e07eb560c726858c501aed0e77f068da2fb5b61d974781` |
| T134 | `580040f8b1617054f19c6e24b14b3ed00effaf30f1809f1f93f32aecdf75290f` |
| T135 | `34ec452ad466329f20db7101c91d17866bb6a4e5284739970413d96fee776a0a` |
| T136 | `1257cb65cf697591dabfdf34d298ef5113cc2fcaa6819987b716651f03d427ed` |
| T137 | `98456d1e7dd49685ba0221bab297ad73abdf982bff93665dae543b17554f29c9` |
| T138 | `408e04d7a0ccb07de2efc1c7370d44eda6d65f1ac33849a1d47062963fdd1930` |
| T139 | `e0c185549fbd9b5361de4d0efe3edeb8b0947d4c6c000cccc469a2acceb6dbf5` |
| T140 | `2cb7e0308e2879ef761974cf83bcd0787357a6588e258fce392b39ce5b90602e` |
| T141 | `f2861038b2d06e650615b245227aaf6229ec6ce6b090e8cd0b568f7642360acf` |
| T142 | `fa52810779dda19d59e1d98a22d83be03e7bf4f61e00eb73e1f778ac344c347c` |
| T143 | `1adb2a4cdad52332d436817e6c5f57c3f555f7896721578f84f3e5d1b7387746` |
| T144 | `a0d151e1fc51c9fd08d25f2961c643591e2c57d31bd31a7a9541de1af41a2904` |
| T145 | `a3e801d4f0769e7ea803cbdb5f3c3d89e44ddb92efaf8320070c5cf873243149` |
| T146 | `14f2819f586b02b4bea59bd1bde6eb819a2eabdf23de0eca1cfe54b84cf08730` |
| T147 | `44409c87c92c5d1afd4bb3f290e826a67ebcc6c32c7f298f8cab9c2c33c48264` |
| T148 | `31c4f7dd06023948a21570155aaa9ceb95ea1188d657259cc5d2b86bea9f3e90` |
| T149 | `11846fafaaf1174c2f57116b304fe43b47d0a876afc884b02bc592bc94645c7f` |
| T150 | `215212efe36ec0316ba70041b10e6be3c240a7440c67637774eb7390b2bbc909` |
| T151 | `dd6519ceaa6f67a04814ba594ae9ea9c3f470521e1b72201f6804774e56f4e0e` |
| T152 | `af5d3ed8de2e42e1eb08aece933a0c432d6fd4b251f0916dab14ed35f0cf5c7e` |
| T153 | `22a430fea531611db71ad4231ea10e586a70dba99caba14d637ef3ab247469b2` |
| T154 | `fb588be228530c2aed13c30e6e6eff12c238cb855b0cb54282e7b976aad7efda` |
| T155 | `e25daf2f437dfde3fbd630c4b42ff446c5e487873e335454083c9a1ea39a4429` |
| T156 | `1ce76f3a0e6c117dc902c04a463d51476b6ffc371f8f7bdd5972819065030bc5` |
| T157 | `8d17f2c0964e0a6238a0a6157e5df751d19e48dbdc76015432e2ac209c5928fa` |
| T158 | `09793220a9b37f22a24d4a9048ea83299cecd2ef835244040489ea627ecf821c` |
| T159 | `5d829c5985dc9e2d85f5091fb4540f44a3aa0a6f5947bdeab19187375406b944` |
| T160 | `609efccc34afe14464ea05c384542d4ecd07ff7c25a0fe919c99d68ccab1eee2` |
| T161 | `a9579b0a7e1746c56065d9e1e04c115d9be6581b6af4cf4f4c791c6393b5301c` |
| T162 | `73cec05f5c181bd1cc430175a5c1846f9a22d0611de70cd5404ccceddfdb7cb3` |
| T163 | `fa828190c0ff1814186fc2514cad32125bcfee89486e9c0a7ca6804eccec7dba` |
| T164 | `c86ae7abb00d7590284cdb9532bbd6fb4e79f052498a3a7df4f864cca767db7c` |
| T165 | `054fc4de7e7c80dc611525dee882ae87f48527c3d1017ce2569d38e7d5c692b7` |
| T166 | `dbe59fdb788c7d1eaada908fe0abe694f9487675b4a327a98f9da6342b6bced9` |
| T167 | `bb5f9945775ccb983d484c160b13472a6e6e2588a8e653047df1b30e4c3d10ad` |
| T168 | `c44afe68d8efe51b1039fc92605d65acf5674cbef9a3c251864a704f98454ff5` |
| T169 | `7ee5f0427966853b2d94a9384dcea5beee5c76d17585f84f54604139877ae9ef` |
| T170 | `5a87a08896cc4bd33a44bd736c931655cd22c1dabd84e6de14a9743bc1aa86af` |
| T171 | `9031b60a769ae13811c205f5ade4ba2490abc5821759a7222ae99e31e884c96c` |
| T172 | `4ee83b3b5b56a5786954857c69fff7a06609c60632a1e187791206369d6a887d` |
| T173 | `fae754662ca184def5777ed6da4391f5999ae444905ba2dfc9911a19d5b9ac2b` |
| T174 | `8a148e49a5b815a225466acaf36b090c8b05d6787a2ed2b58a95228b535a6f35` |
| T175 | `43ef45080380bca61ed50a529002b3af188d1eadfe1ed0bbf9985a85378ec308` |
| T176 | `3b7a34c169ae4bc8acb89463a9061ddcf1578aa5d3df34fd8f51303737f7dcc0` |
| T177 | `72c805861ad9f07d575a0e7de244c3493c34d780ed59a16fd7b80cf7ba79a962` |
| T178 | `2f2a449a11e0e348a64cfab449ad06723b1763c61b006c66a59dbd59b652cf65` |
| T179 | `19326c9c39c84cbae05d2e0aeef1c8f46cf4ad84b063bf48486c73b926ed36c5` |
| T180 | `bdd70eb25bcc2d49c3896806abdd7afb053da211ce08a2478ffd3eca552d1665` |
| T181 | `131f0fec2fb2742e674e47d32cdd3bcf7fba3a8d29d7e614b259fbbb5220afb1` |
| T182 | `14286594ca3204a4aea1e2ada394f7e865f3bc9e2b07a94ca6c623a990ee654f` |
| T183 | `7deddd95a10404c87512f64b55708f8d2309028162852da92cf6a859d5dd28e0` |
| T184 | `c2d8a0d6c5e823b35549d0d46b095711b37e25cc3f915aab8b42e634fdad838f` |
| T185 | `5f1c91fc80105d97f50d63a6930891439200257c6413b06ee4239e731d4d1b59` |
| T186 | `ca3b2739fd599376450e522c175c899e0d1cc1a8e2c6aae0b0184f5e21632560` |
| T187 | `14362910b3c6dbf812841a851de0e5dd30c8d77beb90f3574b11e0398b744204` |
| T188 | `f4ac9d563e146ad837053cd5cab4e34bd39214c7857474d9ef0ad783303ba79b` |
| T189 | `d62edb3d489cff1ef56efc5177a71857e6370dc5c3a264e4392077bca782ab09` |
| T190 | `0b37cc94345a28c65116d7ac642a105a510fa6ab9916b83d2930ec23dffd9591` |
| T191 | `6c6a425172bdeca0b7248be920df0866eca83e6bb1eacdba84e2b093152fa130` |
| T192 | `466ff582dbc73a8daaaece441838976d003489990b0fd22635552baa1e987785` |
| T193 | `9a2474c0ba89db29ddaeff553da898ea946e84f433f0b98dd552d2579f594c30` |
| T194 | `c43cd10f21d7b0157bc1506fff1e69870532278e3648c716b81a9b4e39a9f91f` |
| T195 | `8d4820c8e016b0167a597d67afdc49c67efd7d3425011a6fdcfaf9b638b2bcc6` |
| T196 | `b8fecc05c4469b88fd60d45befe9f9c2785b8476545e7bf48323513c35bde331` |
| T197 | `112784a97751c88bdade1b8eaf58fc9e7319d55d2d77e515123e8886f8f5943f` |
| T198 | `40ede3fda02cc55fcd274d37c7f956eb70eaf4c88b686f13718653027af4eac0` |
| T199 | `d647ab81d4131bcce4e6053cd01f16736b1930aa557fd670c98d3fc4cd26f422` |
| T200 | `6d559b0dd395910c01284fb9deb1bae8e4162e7cc2e9da8dbc77081c67ee5b25` |
