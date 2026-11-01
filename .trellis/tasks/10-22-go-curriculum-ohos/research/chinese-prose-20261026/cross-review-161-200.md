# Independent cross-review — controlled-Chinese prose, topics T161–T200

Reviewer: independent cross-review worker (not the author of T161–T200).
Task: `.trellis/tasks/10-22-go-curriculum-ohos`.
Date: 2026-10-26.
Writable scope: this file only
(`research/chinese-prose-20261026/cross-review-161-200.md`).

Read-only everywhere else. No topic JSON was edited. No git, runtime, test, SDK,
Go, native, build, WSL, device or channel action ran. Every other owner's file
was left byte-identical. All checks below are static: Python 3 stdlib JSON,
hashing and text comparison over files on disk.

## Verdict

**NOT PASS — narrow changes required.** The findings named by
`independent-semantics-121-200.md` for this range are all genuinely resolved, and
every frozen invariant, hash and length limit holds. But the repair pass
introduced **7 sentence-fragment defects** by splitting at commas, three of which
break the explicit contract clause "sentence splitting must keep a condition
attached to its consequence". They are listed in section 5 with exact text and a
minimal fix each.

A zero linter result does not detect any of them, and I did not infer pass from
it.

## 1. What was reviewed

| Item | Value |
| --- | --- |
| Topics in range | 40 (`T161`–`T200`) |
| Mutable prose fields | 624 |
| Current topic JSON SHA-256 | section 9 |
| Reference for "before" | `chinese-prose-20261026/before/T161.md` … `T200.md` |
| Author's handoff | `chinese-prose-20261026/owner-161-200.md` |
| Findings source | `chinese-prose-20261026/independent-semantics-121-200.md` |
| Rule source | `.trellis/spec/backend/go-curriculum-tooling.md` § "Controlled Chinese prose contract (2026-10-26)" |
| Programs read | `T161, T166, T168, T170, T185, T187, T188, T191, T193, T197, T200` |

## 2. Frozen invariants — all pass

| Invariant | Result |
| --- | --- |
| Masked immutable canonical hash == `baseline.immutableSha256` | **40 / 40** |
| Per-field `可能` / `也许` counts == `baseline.modalities` | **624 / 624** |
| Sample-file SHA-256 == `baseline.samples` | **40 / 40** |
| Projection content == current JSON in `mutablePaths` order | **40 / 40** |
| Author's 9 claimed post-repair topic hashes == actual | **9 / 9** |
| 31 untouched topics == reviewed snapshot hashes | **31 / 31** |
| All 9 claimed-changed topics actually differ from the snapshot | confirmed |

The masked hash covers every non-mutable leaf and the whole structure, so code,
`output`, `verification`, IDs, `locale`, `runtime`, `source`, `license`,
`prerequisites`, `sampleFiles` and program bodies are provably unchanged. No
field or list item was added, removed or reordered.

## 3. Named findings — all resolved, verified against the programs

| Finding | Field | Current text | Source proof |
| --- | --- | --- | --- |
| Defect 1 unit | T161 `explain` | `一个基点为万分之一。` | `roundRate(amount,basisPoints) = (amount*basisPoints+5000)/10000`, called with `1000` → 10%. One basis point is 1/10000. Old `百分之一基点` was wrong by 10⁴. |
| Defect 2 unit | T170 `explain` | `MiB 为 1024×1024 字节。` | `factor = 1 << 20`; expected `2MiB=2097152` = 2×1024². Old `一百零二十四平方字节` read as 124². |
| Defect 3 factor | T187 `exercises.0.answer` | `单文件大小*(组内文件数-1)。` | Group of n equal files saves n−1 file sizes; the old `组数-1` gave 0 for one group of three. Literal `1` unchanged. |
| S4 error vs comparison | T185 `explain` | `先检查写入错误。再检查关闭错误。两项都通过才 Rename 到目标。` | Program: `WriteString` err → `Close()` err → `os.Rename`. Order and actors match exactly. |
| S4 term split | T185 `summary`, `objective`, `example.summary` | `比对写入的新内容…` | `比对` for content comparison, `检查` for error returns. Document counts: 检查×2, 比对×3, 核对×0, 校验×0, 核查×0 → no rotation, no concept merge. |
| S5 field meaning | T200 `explain` | `返回排序后的补丁字段名，便于稳定展示。取值与旧值相同的项也计入。` | Program returns `keys` = every supplied field name, sorted, before/independent of value equality. Expected `changed=[name port]`. |
| S5 in-place patch | T200 `pitfalls.0` | `不要把补丁字段逐项解码到原配置。后续字段失败会留下部分更新。` | Program decodes into `candidate := *cfg` and commits once. |
| S5 concept term | T200 `concepts.3` (tutorial + example) | `排序补丁字段名` | matches the returned value. |
| One-action items named by the review | T161 answer, T168 explain, T185 explain, T188 answer, T191 explain, T193 prompt | split per action | all six now carry one action per sentence |

Cross-checks on the author's own claims:

- Old-defect strings: **14 / 14 absent** (e.g. `百分之一基点为万分之一`,
  `一百零二十四平方字节`, `组数-1`, `核对写入和关闭错误`, `结果键`, `变更键`,
  `逐项解码原配置时`, and the six pre-split sentences).
- Replacement strings: **15 / 15 present**.
- Numeric/identifier multiset, whole range, before → now: the **only** delta is
  T170 `1024` ×2 added, nothing removed. The author's statement "no other
  numeric or identifier token changed" is correct.

## 4. Length limits — all pass

Measured with the linter's own metric (one count per CJK character, one per
contiguous Latin/digit token; punctuation not counted).

| Class | Limit | Result |
| --- | --- | --- |
| `objective`, exercise `prompt`, `hint` (checked separately) | ≤ 25 | **0 violations**; maximum is exactly 25 (T196, T182, T175, T164, T162 objectives) |
| all other prose (`summary`, `concepts`, `pitfalls`, `explain`, `answer`) | ≤ 40 | **0 violations** |

My first pass counted full-width punctuation and produced four false "26 > 25"
prompts (T167, T168, T183, T187). Re-measured with the contract metric they are
24 and within limit. I am not reporting them as defects.

## 5. Remaining defects — introduced by this repair pass

All seven were verified absent-before / present-now: the `before/` text kept the
clause joined, and the repair pass split it at a comma. They are **not**
pre-existing.

The contract states: "Sentence splitting must keep a condition attached to its
consequence and a warning attached to the operation it forbids."

### D1–D2 explicit contract violations (condition detached from consequence)

| ID | Topic / field | Current text | Defect |
| --- | --- | --- | --- |
| D1 | T168 `tutorial.explain` | `输入验证与聚合分开后。可以进一步加溢出、单位和重复流水 ID 的检查。` | Temporal condition `…分开后。` is a fragment; its consequence is a separate sentence. Before: `输入验证与聚合分开后，可以进一步加上…的业务检查。` |
| D2 | T200 `tutorial.explain` | `这样即使 name 已成功解析而 port 随后失败。原资料也不会改变。` | `即使…失败。` has no main clause; the `也`-consequence is in the next sentence. Before: `…随后失败，原资料也不受影响。` |

### D3–D6 sentence fragments: bare `并` as a sentence opener

`并` is a coordinating conjunction and cannot open a sentence; each of these
sentences has lost the verb it coordinates with.

| ID | Topic / field | Current text | Before |
| --- | --- | --- | --- |
| D3 | T166 `tutorial.explain` | `程序拒绝空输入、越界 p、NaN 和无穷样本。并在副本上排序以保护调用方顺序。` | `…无穷样本，并在副本上排序…` |
| D4 | T181 `tutorial.explain` | `真实写文件还需要解析父目录。并检查最终归属。` | `…解析父目录并检查最终归属，…` |
| D5 | T183 `tutorial.explain` | `递归列表则使用 WalkDir 检查文件后缀。并排序输出全部匹配项。` | `…检查文件后缀，并排序输出全部匹配项。` |
| D6 | T200 `tutorial.explain` | `再排序键列表。并在所有未知键检查通过后修改候选副本。` | `再排序键列表并在所有未知键检查通过后修改候选副本。` |

The technical content of D3–D6 is correct — I confirmed T166 sorts a copy
(`data := append([]float64(nil), input...)` then `sort.Float64s(data)`), and
T181/T183/T200 match their programs. Only the sentence boundary is wrong.

### D7 sentence fragment: bare `因为` as a sentence opener

| ID | Topic / field | Current text | Before |
| --- | --- | --- | --- |
| D7 | T200 `tutorial.exercises.0.answer` | `不要先给候选赋版本再忽略。因为调用者需要明确知道系统不接受该请求。` | `…再忽略，因为调用者需要明确知道请求未被接受。` |

A `因为`-clause alone is not a sentence. This one also paraphrases: the claim
changed from "请求未被接受" to "系统不接受该请求".

### Minimal fixes (suggestions only — I did not edit the JSON)

| ID | Suggested text |
| --- | --- |
| D1 | `输入验证与聚合分开后，可以进一步加溢出、单位和重复流水 ID 的业务检查。` |
| D2 | `即使 name 已成功解析而 port 随后失败，原资料也不会改变。` |
| D3 | `程序拒绝空输入、越界 p、NaN 和无穷样本。副本排序保护调用方顺序。` |
| D4 | `真实写文件还需要解析父目录。还要检查最终归属。` |
| D5 | `递归列表则使用 WalkDir 检查文件后缀。再排序输出全部匹配项。` |
| D6 | `再排序键列表。所有未知键检查通过后才修改候选副本。` |
| D7 | `不要先给候选赋版本再忽略。调用者需要明确知道系统不接受该请求。` |

## 6. Minor wording drift introduced by the pass

| ID | Topic / field | Change | Effect |
| --- | --- | --- | --- |
| M1 | T168 `explain` | `加上…的业务检查` → `加…的检查` | drops the `业务` qualifier; `业务检查` is broader than `检查` |
| M2 | T200 `explain` | `原资料也不受影响` → `原资料也不会改变` | `受影响` → `改变` narrows the guarantee |
| M3 | T170 `explain` vs `answer` | `1024×1024 字节` beside `一千字节` and `一千零二十四` | three number styles in one document; the spec prefers the exact numeric expression, so the answer's `一千零二十四` for the KiB multiplier is the outlier |

None of these changes a program fact.

## 7. Pre-existing one-action residuals (not introduced, not required by the review)

Twenty tight fields keep two or three actions joined by `并` / `同时` inside one
sentence. Every one is byte-identical to `before/`, so the repair pass neither
created nor fixed them. The review explicitly said it was "not a claim that every
use of `并` or `后` is wrong", and none of these appears in its finding list.

Examples: T161 prompt `支持退款负数，并明确…`; T167 prompt
`将普通桶计数转换为累计桶，并同时保留原始非累计计数。`; T170 prompt
`增加 KiB，保持 KB 的十进制定义不变，并测试两个单位不同。`; T182 prompt
`再加入测试配置子树，并用同一个 load 函数读取。`; T184 prompt
`把跳过目录名单扩展为 cache 与 vendor，并保留文件名 vendor.go。`;
T188 prompt `重新计算链接并证明旧链接不再指向新目标。`

Under the letter of "keep one action per sentence" these are gaps. Under the
review's own scope note they are out of scope. I record them so the coordinator
can decide, and I do not count them as failures of this pass.

A related observation, also not a contract violation: 17 sentences open with
`也` / `而` / `但` / `同时` and elide the subject (e.g. T163 `也避免先转浮点造成精度损失。`,
T197 `也核对表头与各行数量字段的起点一致。`). These read as acceptable
technical Chinese with subject ellipsis; I list them as style only.

## 8. Linter (informational; not used as proof)

| Run | Hard | Advisory | Exit | 字 |
| --- | --- | --- | --- | --- |
| `after/T161.md … T200.md`, default `--max-chars 40` | 0 | 0 | 0 | 15879 |
| `after/T161.md … T200.md`, strict `--max-chars 25` | 0 | 0 | 0 | 15879 |

The author's claim of 0 / 0 at both thresholds reproduces. The linter cannot see
D1–D7: `并` and `因为` openers are not rules, and a fragment is short. No prose
is hidden in backticks or fences (checked: zero occurrences of `` ` `` or ```` ``` ````
in the 40 projections).

## 9. Current topic hash inventory (this reviewed state)

| Topic | SHA-256 | Topic | SHA-256 |
| --- | --- | --- | --- |
| T161 | `12f109a530b15177b93d97507a4c9be40b7cba4efeabee8134caef8e1dd5a297` | T181 | `131f0fec2fb2742e674e47d32cdd3bcf7fba3a8d29d7e614b259fbbb5220afb1` |
| T162 | `73cec05f5c181bd1cc430175a5c1846f9a22d0611de70cd5404ccceddfdb7cb3` | T182 | `14286594ca3204a4aea1e2ada394f7e865f3bc9e2b07a94ca6c623a990ee654f` |
| T163 | `fa828190c0ff1814186fc2514cad32125bcfee89486e9c0a7ca6804eccec7dba` | T183 | `7deddd95a10404c87512f64b55708f8d2309028162852da92cf6a859d5dd28e0` |
| T164 | `c86ae7abb00d7590284cdb9532bbd6fb4e79f052498a3a7df4f864cca767db7c` | T184 | `c2d8a0d6c5e823b35549d0d46b095711b37e25cc3f915aab8b42e634fdad838f` |
| T165 | `054fc4de7e7c80dc611525dee882ae87f48527c3d1017ce2569d38e7d5c692b7` | T185 | `69447ff2828a129d43407696e677ba67a97bbac93f86f5b27c8113ef9697839b` |
| T166 | `dbe59fdb788c7d1eaada908fe0abe694f9487675b4a327a98f9da6342b6bced9` | T186 | `ca3b2739fd599376450e522c175c899e0d1cc1a8e2c6aae0b0184f5e21632560` |
| T167 | `bb5f9945775ccb983d484c160b13472a6e6e2588a8e653047df1b30e4c3d10ad` | T187 | `5beee7569e5a6ecfdd13ec46599e98ce959c0849f9ae61ecc8cf9ea822698d7e` |
| T168 | `1b955aaefe44ed543da031798c490b5bfd452e215e91e54741c1852eb9048f42` | T188 | `c795504237f99759b769d49b99fba7131069fab3f862275ea811a4e3a6d52094` |
| T169 | `7ee5f0427966853b2d94a9384dcea5beee5c76d17585f84f54604139877ae9ef` | T189 | `d62edb3d489cff1ef56efc5177a71857e6370dc5c3a264e4392077bca782ab09` |
| T170 | `f0e46ad007f337d7c416f2178a5d248528206647bf35ff1def3a6c8d9daddb55` | T190 | `0b37cc94345a28c65116d7ac642a105a510fa6ab9916b83d2930ec23dffd9591` |
| T171 | `9031b60a769ae13811c205f5ade4ba2490abc5821759a7222ae99e31e884c96c` | T191 | `06d8668dd087626e8891ca76ded5bfce2c223cf80d3a8451f3e13a9c00e2b863` |
| T172 | `4ee83b3b5b56a5786954857c69fff7a06609c60632a1e187791206369d6a887d` | T192 | `466ff582dbc73a8daaaece441838976d003489990b0fd22635552baa1e987785` |
| T173 | `fae754662ca184def5777ed6da4391f5999ae444905ba2dfc9911a19d5b9ac2b` | T193 | `437fdfdb97172921588174a42b4c53c405717a25fc66df0919c55d5e0ffa5ade` |
| T174 | `8a148e49a5b815a225466acaf36b090c8b05d6787a2ed2b58a95228b535a6f35` | T194 | `c43cd10f21d7b0157bc1506fff1e69870532278e3648c716b81a9b4e39a9f91f` |
| T175 | `43ef45080380bca61ed50a529002b3af188d1eadfe1ed0bbf9985a85378ec308` | T195 | `8d4820c8e016b0167a597d67afdc49c67efd7d3425011a6fdcfaf9b638b2bcc6` |
| T176 | `3b7a34c169ae4bc8acb89463a9061ddcf1578aa5d3df34fd8f51303737f7dcc0` | T196 | `b8fecc05c4469b88fd60d45befe9f9c2785b8476545e7bf48323513c35bde331` |
| T177 | `72c805861ad9f07d575a0e7de244c3493c34d780ed59a16fd7b80cf7ba79a962` | T197 | `112784a97751c88bdade1b8eaf58fc9e7319d55d2d77e515123e8886f8f5943f` |
| T178 | `2f2a449a11e0e348a64cfab449ad06723b1763c61b006c66a59dbd59b652cf65` | T198 | `40ede3fda02cc55fcd274d37c7f956eb70eaf4c88b686f13718653027af4eac0` |
| T179 | `19326c9c39c84cbae05d2e0aeef1c8f46cf4ad84b063bf48486c73b926ed36c5` | T199 | `d647ab81d4131bcce4e6053cd01f16736b1930aa557fd670c98d3fc4cd26f422` |
| T180 | `bdd70eb25bcc2d49c3896806abdd7afb053da211ce08a2478ffd3eca552d1665` | T200 | `f9d6a0aa4e56ec13ca4ce27816a1cec7c26244ae86ade37b1555b0a6c5308549` |

Any later correction invalidates these hashes and needs a fresh review of the
changed topics only.

## 10. Explicit non-claims

- I did not execute any program, test, compiler, SDK, native build, FFI, device,
  WSL or channel step. No behavior is asserted from execution.
- A zero linter result is not acceptance; D1–D7 prove that here.
- The invariants prove nothing about prose quality; they only prove that code,
  samples, structure and modality counts are intact.
- I did not edit, reorder or "improve" any T161–T200 JSON, projection or owner
  report. The seven defects are reported, not fixed.
- Sections 3, 5 and 6 are verified against the programs on disk, not against the
  author's handoff.
