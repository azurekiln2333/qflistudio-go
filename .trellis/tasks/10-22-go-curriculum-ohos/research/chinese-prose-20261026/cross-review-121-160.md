# Independent cross-review: T121–T160 (owner 121–160)

Reviewer: prose worker for T161–T200. This is a read-only cross-review of another
owner's range. I wrote no topic JSON, no projection and no shared artifact. The
only file I created is this report.

Snapshot UTC: 2026-10-26T02:15Z (local file times cited below are the workspace
clock and are used only as integrity evidence).

**Verdict: qualified source PASS for T121–T160.**

Every defect and factual correction reported in
`independent-semantics-121-200.md` for this range is resolved. All four
structural invariants hold 40/40. All 40 sample programs were read and the prose
matches them. Nothing blocking remains. Section 7 lists non-blocking wording
observations, so the pass is qualified rather than unconditional.

Nothing was executed: no Go, no package runtime, no FFI, no device, no test, no
WSL, no channel, no git. Programs were read as text. Claims about Windows API
behaviour, containment or executable correctness remain unproven and are out of
scope for this review.

## 1. Inputs and method

| Input | Use |
| --- | --- |
| `chinese-prose-20261026/baseline.json` | `mutablePaths`, `modalities`, `immutableSha256`, `samples` |
| `chinese-prose-20261026/before/T121.md … T160.md` | frozen original prose (as reviewed) |
| `chinese-prose-20261026/after/T121.md … T160.md` | current prose under review |
| `expansion-draft/topics/T121.json … T160.json` | current source of truth |
| `expansion-draft/samples/T121/main.go … T160/main.go` | actual programs, 40 files, 40 363 B |
| `independent-semantics-121-200.md` | findings S1–S5, retained defects, one-action table |
| `scripts/ste-lint-zh.py` | supporting evidence only |

Method: masked-hash invariant recomputation, field-by-field diff of all 40 topics
(790 diff lines), independent sentence-length measurement, token-multiset
comparison, Latin-identifier cross-check against each program, full read of every
sample program, and a before/after census of passive, vague and nominalisation
markers.

I did not treat a zero linter result as acceptance. The linter cannot see a
changed noun, a lost condition, a false warning or a wrong unit, and it never
reports the one-action rule. Sections 3–6 rest on reading the programs and the
prose, not on the linter.

## 2. Reported findings that this range had to fix

`independent-semantics-121-200.md` listed 13 topics in this range as requiring
change. Exactly those 13 topics differ from the reviewed snapshot hashes, and no
other topic in the range changed:

`T122 T123 T124 T127 T128 T132 T137 T139 T142 T144 T152 T159 T160`

The remaining 27 topics are byte-identical to the reviewed snapshot.

## 3. Finding-by-finding verification

### S1 — T142 `tutorial.pitfalls.1`: physical layout restored

Current: `槽位顺序不是时间顺序。导出时必须从最旧槽位开始。`

Matches the suggested wording. Verified against `samples/T142/main.go`: capacity
3, records added chronologically a, b, c, d, so the fourth write lands in slot 0.
Physical slots become `[d, b, c]`; `Snapshot` computes
`start = (next-count+len)%len` and walks b, c, d. Array layout therefore differs
from chronology while the write sequence stays chronological. The noun is now a
physical-layout term, as required, and the warning is true. **Resolved.**

### S2 — T128 `tutorial.pitfalls.0`: mechanism and condition restored

Current: `Buffer 初始容量若大于业务上限，较长 token 可能无需扩容就通过。`

The condition is one complete clause again, `无需扩容` is back, and exactly one
`可能` remains, matching the recorded modality for this field. Verified against
`samples/T128/main.go`, which calls `scanner.Buffer(make([]byte, 4), 12)`: a token
is only rejected once the buffer would have to exceed the maximum, so a starting
capacity above the business limit lets a longer token pass without growth. The
stated cause is the real cause. **Resolved** (one wording note in section 7.1).

### S3 — T127 and T159 `tutorial.pitfalls.0`: warnings prohibit, not instruct

- T127 current: `不要按相同行号直接比较两份文件。插入行会让后续所有行误报为改变。`
- T159 current: `不要只合并直接共享邮箱的账号。忽略传递关系会漏掉间接连接。`

Both match the suggested wording: an explicit prohibition plus its consequence,
not a bare imperative for the incorrect operation. T127 is true for
`samples/T127/main.go`, whose LCS backtracking renumbers lines, so equal-index
comparison misreports every line after an insertion. T159 is true for
`samples/T159/main.go`, a union-find over shared e-mail that necessarily captures
transitive membership. **Resolved for both.**

### S4 — T132 title and explain: comparison is not verification

- `tutorial.title` and `example.title`: `便于人工比对的 Base32 编号`
- `tutorial.explain`: `…适合展示和手工比对。…解码器会拒绝原始小写输入。面向人工输入的包装层可以先转成大写，再解码。`
- `验证` is kept for what the program actually proves: `验证解码往返` in the
  summaries and `先验证校验码再解码` in the exercise.

The finding's substance is that manual reading is not proof of encode/decode or
checksum behaviour. That separation is intact: manual work is described with a
comparison verb, machine checks keep the verification verb. The owner chose 比对
where the review suggested 核对; both are comparison verbs and neither is the
verification verb the finding objected to, so the finding is satisfied without
the synonym clash that 核对 would have created (see section 5).

Verified against `samples/T132/main.go`: standard alphabet with `NoPadding`,
`Encoding.EncodeToString([]byte("foo"))`, decode roundtrip, lowercase input
rejected, `strings.ToUpper` then decode accepted. `MZXW6` in the prose is the
correct base32 encoding of `foo`; the literal is not in the source, which is
expected. **Resolved.**

### Retained defect 4 — T144 `tutorial.explain`: nonexistent helper removed

Current: `TeeReader 的旁路 Writer 写入失败会成为读取错误。因此 Copy 返回的错误必须处理。`

Matches the suggested wording. `TeeWriter` no longer appears anywhere in
T121–T160, which is the only identifier-level change in the whole range (see
section 4.4). Verified against `samples/T144/main.go`, which calls
`io.Copy(&copy, io.TeeReader(source, digest))`, so the failure that can surface as
a read error is the supplied writer, exactly as now written. **Resolved.**

### One-action table — all seven rows for this range

| Topic / field | Current sentence | Result |
| --- | --- | --- |
| T122 explain | `它保留各语言字母和数字。它还会把字母转成小写。` | split, one action each |
| T123 exercise answer | `保留行首或空白前缀。然后为 phone=123 headphone=ok 增加测试。` | split |
| T124 explain | `它先把字母转为小写。再累加计数。` | split |
| T137 explain | `先读取表头。再按列名建立索引。确认 quantity 与 cents 都存在。然后逐行读取。` | split into four |
| T139 explain | `它先记录修改数量。然后 Marshal。再解码。最后确认库存不变。` | split into four |
| T152 explain | `Pop 先清除底层引用。再把 Index 设为负一。` | split |
| T160 explain | `查询先走到前缀节点。再递归收集后缀。` | split |

Every row now carries one action per sentence with the actor and the causal order
preserved. **Resolved for all seven.**

## 4. Independent measurements

### 4.1 Structural invariants — 40/40 on each

| Invariant | Result |
| --- | --- |
| Immutable masked canonical hash equals `immutableSha256` | 40/40 |
| Per-field 可能 / 也许 counts equal `modalities` | 40/40 |
| `after` projection equals baseline path order and JSON values | 40/40 |
| Sample-file `sha256` equals baseline | 40/40 |

The masked hash sets every `mutablePaths` leaf to
`<MUTABLE_CHINESE_PROSE>` and hashes the whole document, so every non-mutable leaf
and the entire structure are covered. No field or list item was added, removed or
reordered in this range. Sample programs are unmodified, which the mtime survey in
section 6.3 independently confirms.

Per-field modalities: 22 fields in this range carry modality, 23 tokens total
(`T128.tutorial.pitfalls.1` carries `可能` twice). Each equals its recorded count,
including the S2 field above, so no confidence statement was strengthened or
weakened.

### 4.2 Sentence length and punctuation (measured, not inferred)

| Measure | Result |
| --- | --- |
| Longest sentence in T121–T160 | 25 characters (`T126.tutorial.summary`) |
| Sentences over 25 characters | 0 |
| Sentences over 40 characters | 0 |
| Semicolons (`；`) in prose | 0 |
| Halfwidth `, ; : ! ?` after a CJK character | 0 |
| Empty mutable values | 0 |

Instructions meet ≤25 and explanations meet ≤40. Because the longest sentence in
the whole range is 25, the stricter ≤25 preference is also met everywhere,
explanations included.

### 4.3 Tutorial/example pairing

`tutorial.title = example.title`, `tutorial.summary = example.summary` and the
concept lists agree in 40/40 topics. No prose is hidden in code fences or
backticks: the count of backticks in the after projections is zero.

### 4.4 Token multiset versus the frozen original

Comparing numeric and identifier token multisets, before against after, across all
40 topics, produces exactly one difference:

| Topic | Added | Removed |
| --- | --- | --- |
| T144 | `TeeReader` ×1, `Writer` ×1 | `TeeWriter` ×1 |

That is the intended correction of retained defect 4. No number changed anywhere
in T121–T160, and no other identifier was introduced or dropped.

### 4.5 Passive, vague and nominalisation census

Across the range the owner removed `被` 19 times (T125, T128, T129, T130, T132,
T133, T134 ×2, T135, T139, T142, T146, T147 ×3, T148, T150, T151, T154, T157,
T158, T159) and `进行` once (T135). The differences for `收到`, `得到`, `由`,
`相关`, `若干` and `一些` are all zero: nothing of that kind was introduced.

Remaining scan hits are compound words or legitimate result and agent verbs, not
passive voice or vague reference. Each class, with an example:

| Marker | Class | Example | Assessment |
| --- | --- | --- | --- |
| `受` | inside `接受` | T124 `让 top 接受 N 后…` | not passive |
| `受` | inside `可接受` | T128 `区分可接受的长行与超预算输入。` | not passive |
| `受` | inside `受控` / `受限` | T139 `适用于受控协议`, T147 title `受限读取防超量` | not passive |
| `受` | `不受…影响` | T159 `结果不受 map 遍历影响。` | not passive |
| `收到` | none | — | absent |
| `得到` | yields / produces | T145 `第一个窗口得到 2345。`, T122 `会得到空字符串。` | result verb, not a hedge |
| `由` | agent or composition | T138 `再由 csv.Writer 处理格式。`, T143 `十四字节由…组成。` | active, not agentless |
| `由` | inside `由于` | T148 `由于包装器禁用快路径…` | causal, not agent |
| `进行` | light verb, pre-existing | T133 `在验证 offset 与 limit 后进行` (field unchanged) | pre-existing, not introduced |

None of these is a defect. They are recorded because a mechanical scan reports
them and the review requires each false positive to be named.

### 4.6 Term consistency per document

The review warns that unifying terminology must not destroy concept distinctions.
Within each of the 40 topics I checked the groups 检查/校验/核对/核查,
错误/报错, 配置/设置, 修改/变更 and 显示/展示. No topic contains two members of the
same group, so no document rotates synonyms and none has an accidental
mixed-meaning term. T132 keeps manual comparison distinct from machine
verification, which is the boundary S4 asked for.

## 5. Technical meaning against the actual programs

All 40 sample programs were read. For each topic I checked the claims the prose
makes about behaviour: the operation performed, the numbers in the sample, the
failure paths exercised, and which mechanism causes which result. Selected
confirmations, one per topic group:

- T121: `records` replaces CRLF then CR, drops exactly one trailing empty record,
  and returns no records for empty input. Prose matches, including the warning not
  to `TrimSpace` every line.
- T122: a hyphen is written only when `pending` and the output is non-empty, so no
  leading, trailing or consecutive hyphens. Prose matches.
- T123: the pattern anchors the key at line start or after whitespace, so
  `nottoken` is untouched; the replacement keeps the leading separator. Prose
  matches.
- T124: `ScanWords`, lowercase, count, then sort by count desc and word asc; the
  sample makes alpha and gamma tie so the tie-break is observable. Prose matches.
- T125: the `escaped` state skips backslash-protected characters, `strconv.Unquote`
  handles escapes, a non-separator after a quoted value is rejected, and duplicate
  keys take the later value. Prose matches.
- T126: prefix and suffix are computed independently and may overlap on short
  input; zero names return two empty strings. Prose matches.
- T127: LCS table, tie broken toward delete, adjacent delete plus add shown as one
  change while keeping both line numbers. Prose matches.
- T128: initial buffer 4, maximum token 12, a 9-byte line fits, a 14-byte line
  errors, and the maximum must also carry the line separator. Prose matches.
- T129: `NewReplacer` consumes the original input only, so generated backslashes
  are not re-matched, and the earlier pattern wins on overlap. Prose matches.
- T130: index built from non-letter/non-number splits, intersection over the first
  word's documents, sorted output, empty result for a missing word and for zero
  words. Prose matches.
- T131: `Fields` then `DecodeString`; odd length and non-hex characters both fail;
  canonical output is lowercase. Prose matches.
- T132: standard alphabet, no padding, `foo` → `MZXW6`, lowercase rejected,
  uppercased input accepted. Prose matches.
- T133: JSON cursor, `RawURLEncoding`, structural validation before slicing, page
  `c`,`d` with next offset 4, damaged encoding and negative offset both rejected.
  Prose matches.
- T134: defaults installed before decode, explicit `false` overwrites `true`,
  `DisallowUnknownFields` rejects a misspelled field, and a second `Decode` must
  return `io.EOF`. Prose matches, including the ordering claim in the answer.
- T135: envelope plus `RawMessage`, second decode per kind, unknown kind rejected,
  numeric field sent as a string rejected. Prose matches.
- T136: missing key keeps the value, `null` clears the pointer, a string sets it, a
  number is rejected without damage. Prose matches.
- T137: header-indexed columns, required `quantity` and `cents`, bad amounts
  counted as rejected, structural CSV error fails the whole read. The sample
  includes a quoted comma and a bad amount. Prose matches.
- T138: quoting decided by the writer, inner quotes doubled, embedded newline kept
  inside one record. Prose matches.
- T139: `sku` attribute, `quantity` child, `items>item` nesting, restock below five,
  marshal and decode verify, bad stock text errors, unmapped XML content may be
  lost. Prose matches.
- T140: field-name matching, old snapshot decodes into the wider struct, the new
  field stays zero, truncated input errors. Prose matches.
- T141: two-byte big-endian length, `ReadFull` for header and payload, an 8-byte
  budget checked before allocation, oversized header and short payload both fail.
  Prose matches.
- T142: see S1. Slot layout and export order confirmed.
- T143: `MultiReader` over empty and non-empty fragments with a 3-byte buffer; the
  14 bytes are 4 + 3 + 7; `n` handled before `err`. Prose matches.
- T144: see retained defect 4. Source consumption of 7 bytes and the digest
  comparison both confirmed.
- T145: windows `[2,4)` → `2345` and `[7,8)` → `789`, `ReadAll` treats EOF as
  success, window `ReadAt` does not move the source cursor, overrun yields a
  partial read with `io.EOF`. Prose matches.
- T146: empty input → `EOF`, `ab` → `ErrUnexpectedEOF`, `abcd` → 4 bytes and nil.
  Prose matches.
- T147: `max+1` probe, overrun error only past `max`, a 4-byte input at `max` 4
  succeeds, zero budget accepts only empty input, budget capped at 1024. Prose
  matches.
- T148: wrapper exposes only `Read`/`Write` so the fast path is bypassed; 10 bytes
  through a 3-byte buffer. Prose matches.
- T149: `Peek` does not advance, the full record including `LOG|` is still read,
  unknown prefix is a business error, the peeked slice is only valid until the next
  read. Prose matches.
- T150: 32-byte buffer, 11 bytes buffered with the destination still empty, second
  `Flush` neither duplicates nor errors. Prose matches.
- T151: list front is most recent, hit and update both move to front, insert evicts
  the back and deletes the map entry; the sample shows `b` evicted and `a` updated
  without growth. Prose matches.
- T152: `Swap` maintains `Index`, `Pop` clears and sets `Index` to -1, `Fix` after a
  due-date change, `Seq` breaks due-date ties. Prose matches.
- T153: the root holds the worst retained order, ties prefer the smaller ID at
  selection while the heap treats the larger ID as worse, and the final output is
  amount desc then ID asc. Prose matches.
- T154: BFS marks visited at enqueue, so no node is queued twice; hop count is
  `len(path)-1`; an unreachable target returns nil. Prose matches.
- T155: white/grey/black classification, a grey neighbour forms a cycle, the stack
  plus positions slice out the concrete cycle, sorted roots and neighbours make the
  first cycle stable. Prose matches.
- T156: lazy-deletion heap, stale entries skipped by comparing with `dist`, the
  sample improves both B and D so two stale entries are observable, negative edges
  rejected before the search. Prose matches.
- T157: input copied and validated (`Start >= End` rejected), sorted by start then
  end, overlapping or touching intervals extended. Prose matches.
- T158: exclusive cursor via `Search`, the cursor value need not exist, page size
  checked, range clamped by remaining count, result copied. Prose matches.
- T159: see S3. Union attaches to the smaller root, buckets keyed by root, roots and
  members sorted, transitive membership expressed. Prose matches.
- T160: `End` collected before children, child keys sorted, recursion stops at the
  limit, non-positive limit and missing prefix return empty. Prose matches.

Additional independent check: for every topic I extracted the Latin identifiers used
in prose and confirmed each one is either present in the program, a standard-library
name that the tokenizer splits at the dot (`strings.TrimSpace`, `utf8.RuneCountInString`,
`hex.DecodeString`, `math.MaxInt64`, `errors.Is`), a public acronym (CRLF, JSON, CSV,
BFS, DFS, ID, AND, LRU, Dijkstra, Gob, Base32, Base64), or an identifier the exercise
proposes (`Delete`, `Update`, `Top K`, `K`, `CRC`, `phone`, `headphone`, `remaining`,
`subtotal`, `candidate`, `cursor`). No prose names a helper that the program does not
have, which is the exact class of the `TeeWriter` defect.

## 6. Integrity of the reviewed state

### 6.1 Hash inventory, current topic files

`changed` means the file differs from the reviewed snapshot hash in
`independent-semantics-121-200.md`; those 13 topics are the ones the review
required to change. `unchanged` means byte-identical to the reviewed snapshot.

| Topic | SHA-256 | vs review |
| --- | --- | --- |
| T121 | `589f316caae8107370489d560d0eb5ae311714a515e9fd5fb8fa474beeb91927` | unchanged |
| T122 | `3d19ca655766f72ca50727f2fa16cf8d166acc6f712158b985959d775486115e` | changed |
| T123 | `b3c841f8be4375a4665f984dea74ccf30ccd615ac603d7cf00fc03f496bdf15e` | changed |
| T124 | `b3e4bdfe41527129a356f0b09104f614bd47a2622980106a61603c89a4012b38` | changed |
| T125 | `8728fd4e35ab56d56a94410237671d602b6213afbbb956795fc2b3be78c8e022` | unchanged |
| T126 | `f80871838aea3a2c93b6da3fbd78186e96f7d67dc01d2b865043265aaf2cc22e` | unchanged |
| T127 | `05a8d025fabad640f8c624eaf2b48b1a48409032ea1d4e819cb582e2324ee0a4` | changed |
| T128 | `207fc86a39d190630affe9316ca6d3343bd8b0bfae06fa85201b4431eaafcdfd` | changed |
| T129 | `be2d45bd8761b287c3970cbb1fe58bb19131f8611e0d41788e5eeebdb0c57946` | unchanged |
| T130 | `fca9743de28324db5cc9190b3991bb11309d4fa9a41b17a1212332ef9d07158e` | unchanged |
| T131 | `4ed44d2e0d0a5b445c6c99962b0f7c1b86fecbba001e31e7a1a89c6a9bfd0ccd` | unchanged |
| T132 | `6d4203d3710427167a365a051c3861b58193456ff912f8e52e9e9a1b26801446` | changed |
| T133 | `71c6a85cae897a8056e07eb560c726858c501aed0e77f068da2fb5b61d974781` | unchanged |
| T134 | `580040f8b1617054f19c6e24b14b3ed00effaf30f1809f1f93f32aecdf75290f` | unchanged |
| T135 | `34ec452ad466329f20db7101c91d17866bb6a4e5284739970413d96fee776a0a` | unchanged |
| T136 | `1257cb65cf697591dabfdf34d298ef5113cc2fcaa6819987b716651f03d427ed` | unchanged |
| T137 | `3129da05160ccbdd02d6a66e9970e472c67fd165396c7e998ff4a5fe0d87d753` | changed |
| T138 | `408e04d7a0ccb07de2efc1c7370d44eda6d65f1ac33849a1d47062963fdd1930` | unchanged |
| T139 | `7a1b23f93fc68aee6d97df65dd3d3ffb4f3439036b20adb6a772d7b755cc5f15` | changed |
| T140 | `2cb7e0308e2879ef761974cf83bcd0787357a6588e258fce392b39ce5b90602e` | unchanged |
| T141 | `f2861038b2d06e650615b245227aaf6229ec6ce6b090e8cd0b568f7642360acf` | unchanged |
| T142 | `1221c2e8e1c8deee7290c1c68a8e7411fe8919edd13d8727e67cb4c1a32eb8d2` | changed |
| T143 | `1adb2a4cdad52332d436817e6c5f57c3f555f7896721578f84f3e5d1b7387746` | unchanged |
| T144 | `7e756dacc93bda87fce794f7b6ecd7e58dacc2609fea066311373ef629a818d6` | changed |
| T145 | `a3e801d4f0769e7ea803cbdb5f3c3d89e44ddb92efaf8320070c5cf873243149` | unchanged |
| T146 | `14f2819f586b02b4bea59bd1bde6eb819a2eabdf23de0eca1cfe54b84cf08730` | unchanged |
| T147 | `44409c87c92c5d1afd4bb3f290e826a67ebcc6c32c7f298f8cab9c2c33c48264` | unchanged |
| T148 | `31c4f7dd06023948a21570155aaa9ceb95ea1188d657259cc5d2b86bea9f3e90` | unchanged |
| T149 | `11846fafaaf1174c2f57116b304fe43b47d0a876afc884b02bc592bc94645c7f` | unchanged |
| T150 | `215212efe36ec0316ba70041b10e6be3c240a7440c67637774eb7390b2bbc909` | unchanged |
| T151 | `dd6519ceaa6f67a04814ba594ae9ea9c3f470521e1b72201f6804774e56f4e0e` | unchanged |
| T152 | `728b299769d84681e0a0eb3fcf3bcce0e60b705f029c236a2e97f7ea8d7d3471` | changed |
| T153 | `22a430fea531611db71ad4231ea10e586a70dba99caba14d637ef3ab247469b2` | unchanged |
| T154 | `fb588be228530c2aed13c30e6e6eff12c238cb855b0cb54282e7b976aad7efda` | unchanged |
| T155 | `e25daf2f437dfde3fbd630c4b42ff446c5e487873e335454083c9a1ea39a4429` | unchanged |
| T156 | `1ce76f3a0e6c117dc902c04a463d51476b6ffc371f8f7bdd5972819065030bc5` | unchanged |
| T157 | `8d17f2c0964e0a6238a0a6157e5df751d19e48dbdc76015432e2ac209c5928fa` | unchanged |
| T158 | `09793220a9b37f22a24d4a9048ea83299cecd2ef835244040489ea627ecf821c` | unchanged |
| T159 | `22529d59236093c14da8ef9c1389388b3ca1969e6483d30c9cd7bc4bcf181d09` | changed |
| T160 | `86f851eff2575cc2edea7310df787b5f3fddecc1699ea6578da92c81d0e1e8f9` | changed |

Total: 40 topics, 13 changed, 27 unchanged.

### 6.2 Linter evidence (supporting only)

`scripts/ste-lint-zh.py` over `after/T121.md … T160.md`: 0 findings, 0 hard
violations, 15 948 characters, exit 0, at both the default threshold and
`--max-chars 25`; `--json` returns an empty list, so there is no advisory residue
either. This agrees with my own independent measurement in section 4.2 but is not
the basis of the pass.

### 6.3 Workspace integrity

| Evidence | Observation |
| --- | --- |
| `before/T*.md` (160 files) | last write 2026-10-26 05:01:03–04, before any prose edit; frozen originals intact |
| `samples/T121…T160/main.go` | last write 2026-10-23 03:54:20; programs unmodified, consistent with the sample `sha256` invariant |
| `after/` | 160 files, all four owner ranges present; 40 in this range |
| Writes in 07:30–08:10 (this owner plus the T161–T200 batch) | 80 after-projections and 53 topic files, i.e. this range's 40 projections plus the T161–T200 batch's 40, and this range's 13 changed topics plus the T161–T200 batch's 40; the only root-level files are the two owner handoffs (`owner-161-200.md` 07:42, `owner-121-160.md` 07:53); no code, spec, runtime or third-owner file appears in that window |
| Root-level files after this owner's range | `independent-invariants.md/json` (09:58) from a later coordinator run; not part of this owner's range |

I changed no file in this review except this report.

## 7. Non-blocking observations

None of these changes a technical claim, breaks an invariant, violates the length
or one-action rule in a way the review asked to fix, or contradicts a program. I
record them so the pass is qualified and so the owner or coordinator can decide
whether to polish them.

### 7.1 Precision reduced below the review's suggested wording

1. **T128 `tutorial.pitfalls.0`**: `Buffer 初始容量若大于业务上限…` where the review
   suggested `Buffer 的初始切片容量…`. The capacity in question is the initial
   slice capacity passed to `scanner.Buffer`. `初始容量` is still true and still
   identifies the same parameter; only the word `切片` is gone.
2. **T132 `tutorial.explain`**: `面向人工输入的包装层可以先转成大写，再解码。` The
   earlier text said `可以显式转成大写`. The action is still attributed to the
   wrapper and the sample does exactly that, but the emphasis that the uppercase
   step must be explicit (rather than expected from the decoder) is softer.
3. **T121 `tutorial.exercises.0.prompt`**: `保留一条真实空日志。` The earlier text
   said `保留其中一条`, which tied the retained record to the specific input
   `a\n\n`. The requirement is still satisfied; only the cross-sentence reference
   is gone.

### 7.2 Residual compound or fragmentary sentences

The review explicitly said not to split mechanically and these were not on its
list. Each sentence is under 25 characters and unambiguous.

| Topic / field | Sentence | Note |
| --- | --- | --- |
| T124 summary, objective, example.summary | `按次数降序、单词字典序处理并列并取前三名。` | one composite ranking action, joined by 并 |
| T129 summary, objective, example.summary | `验证新生成文本不会二次替换，并比较重叠模式顺序。` | two checks joined by 并 |
| T136 explain | `先把新值成功解码到局部变量再修改资料。` | two steps joined by 再 |
| T138 explain | `它逐字段对比，并单独检查双引号和换行是否保留。` | two checks joined by 并 |
| T141 summary, objective, example.summary | `编码两帧消息，逐帧读取。` | two steps joined by a comma |
| T124 explain | `然后 map 转成可排序的记录切片。` | agentless continuation |
| T139 explain | `然后 Marshal。` | terse agentless verb |
| T140 explain | `也不应把 Gob 当作无限制格式。` | rationale fragment |
| T143 explain | `因为 Reader 可以同时返回数据和 EOF。` | rationale fragment |

### 7.3 Pre-existing wording left unchanged

1. **T133 `tutorial.pitfalls.1`**: `切片上界计算必须在验证 offset 与 limit 后进行`
   uses `进行` as a light verb. This field is unchanged from the original and was
   not part of the review's list.

## 8. Limits of this review

- No program was executed. Everything above is a reading of source text and prose.
  Behaviour claims are verified against the code as written, not against observed
  output.
- I reviewed the frozen `before` projections as the original. Their integrity is
  supported by the timestamp and hash evidence in section 6.3, not by a signed
  manifest.
- Findings that belong to other ranges (S5 in T200, the T161, T168, T170, T185,
  T187, T188, T191, T193 and T200 items) are outside this report.
- Per the review's own note, later corrections require a fresh review; the hashes
  in section 6.1 identify the state this verdict covers.
- Runtime status remains UNRUN.
