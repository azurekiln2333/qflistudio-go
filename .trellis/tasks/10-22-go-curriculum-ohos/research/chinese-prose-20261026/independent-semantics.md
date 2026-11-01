# Independent semantic review: T201-T280

Reviewed on 2026-10-26. Scope: the original `before/T201.md` through `before/T280.md` , current
topic JSON prose, and both owner reports. This is a source review. No target program, SDK, compiler,
native test, WSL, device, channel command, or git mutation was run. Only this report is owned by
this reviewer. The original workers retain JSON ownership.

## Result

Changes generally preserve the taught behavior. The corpus must not be treated as semantically
accepted yet: three concrete meaning changes need correction. Two further wording changes need
clarification. A green mechanical linter does not prove the one-action rule.

## Findings requiring correction

### S1: T247 changes the measured quantity

Paths: `tutorial.summary` , `tutorial.objective` , `tutorial.pitfalls.0` , `example.summary` .

The original refers to `显示宽度` . The current summary and objective say `rune 数不等于终端宽度。` . the pitfall
also uses `终端宽度` .

A terminal's width is its available columns. A string's rendered width is the columns consumed by
that string. These quantities are not interchangeable. The program truncates and pads by rune count.
its examples include Chinese and an emoji. Its final explanation correctly warns that this does not
produce visually equal columns. Renaming the term to silence the display/show synonym rule loses
that warning's precise subject.

Recommendation: retain a precise technical term such as `文本显示宽度` , or consistently use `文本占用的终端列数` .
For example: `rune 数不等于文本占用的终端列数。` Do not replace a technical noun because a style heuristic groups
one of its component words with a presentation verb.

### S2: T241 invents a file-overwrite guarantee

Path: `tutorial.explain` , final sentence.

Before: `可防止生成一半的报告被当成最终文件。`

Current: `这样能防止半成品报告覆盖最终文件。`

The original concerns publishing incomplete output as complete. The rewrite instead claims
protection against overwriting an existing final file. The actual program executes the template into
a `bytes.Buffer` and then calls `fmt.Print` . it neither opens a file nor implements a replacement
protocol. Buffering until execution succeeds cannot by itself prove safe file replacement.

Recommendation: `这样能避免把半成品报告作为完整结果输出。` This preserves the original publication boundary without
adding file-system behavior.

### S3: T271 drops incorrect-amount records from a warning

Path: `tutorial.pitfalls.1` .

Before: `两份账本总额相同也可能有不同的缺失或错账，不能只比较总和。`

Current: `两份账本总额相同也可能有不同缺失。不能只比较总和。`

The phrase about incorrect amounts ( `错账` ) disappeared. Two records can offset each other's amount
errors without either ledger missing a transaction. The program separately reports `mismatch` ,
missing, and duplicate records. The rewritten warning covers only missing records.

Recommendation: `两份账本总额相同，也可能存在缺失或错账。不能只比较总和。` Preserve `可能` .

## Findings needing clarification

### S4: T265 turns a response limitation into a send prohibition

Path: `tutorial.pitfalls.1` .

Before: `完整 DNS 报文包含头部与其他字段，不能只把这个名字编码发送后期待得到正常响应。`

Current: `完整 DNS 报文包含头部与其他字段。不能只把这个名字编码发送。发送后不能期待正常响应。`

The original says that sending only this encoding is insufficient to expect a normal DNS response.
The new middle sentence independently prohibits sending it. The lesson is an offline codec, and its
real boundary is that this name encoding is not a complete DNS query.

Recommendation: `完整 DNS 报文包含头部与其他字段。名字编码本身不是完整查询。只发送名字编码不能保证正常响应。` Retain the original response
limitation. do not introduce a new network action.

### S5: T277 removes the exercise's processing step

Path: `tutorial.exercises.0.answer` .

Before: `让 Change 显式区分 create 与 adjust，在 next 副本中验证存在性并处理，最终统一提交新增键。`

Current: `让 Change 显式区分 create 与 adjust。在 next 副本中验证存在性。最后统一提交新增键。`

The original explicitly requires processing the operation in the `next` copy. The rewrite retains
existence validation and final commit, but no longer tells the learner to apply create/adjust to
that copy. The base implementation checks existence, changes the copied quantity, and commits after
all changes succeed. the exercise extends that sequence to creation.

Recommendation: add an explicit action such as `在 next 副本中执行对应操作。` between validation and commit.
This is a small clarification rather than a demonstrated code defect.

## One-action rule: concrete remaining examples

These are language findings even when the sentence length scan passes:

- The shared `tutorial.exercises.0.hint` says `先保持现有输入的结果，再为新边界增加独立输入。` It combines retaining
existing results with adding input. Use `保留现有输入的结果。为新边界增加独立输入。`
- T206 `tutorial.exercises.0.answer` : `复制 signature 到新切片，再翻转一个字节。` combines copying and modifying.
Split at the comma.
- T210 `tutorial.exercises.0.answer` : `保存第一次 Sum 的结果，再调用一次 Sum。` combines saving and another call.
Split at the comma.
- T232 `tutorial.exercises.0.answer` : `进入后立即登记 defer，再执行用户任务。` combines registration and execution.
Split at the comma.
- T233 `tutorial.explain` : `首个请求创建完成通道并执行 load。` combines channel creation and loading. Use two
sentences.
- T266 `tutorial.summary` , `tutorial.objective` , and `example.summary` : `缓存半帧并输出多帧。` combines
retention and output. Use two sentences.
- T268 `tutorial.pitfalls.1` : `权限位编号一旦用于持久化协议。` is a dangling conditional fragment after mechanical
splitting. Prefer `权限位编号用于持久化协议后，重排名称会改变已有数据语义。` This describes one consequence rather than two
actions.

The list is concrete and not an exhaustive linguistic proof. The worker follow-up should inspect the
rest of the comma/and sequences rather than treating these examples as the full set.

Additional one-action finding: T250 `tutorial.exercises.0.prompt` says
`增加百分数文本，并保持零总量仍输出 n/a。` This joins adding a percentage with preserving the zero-total result.
Use `增加百分数文本。零总量仍输出 n/a。`

## Accepted judgment calls

- T218 `a;b.txt` and T242 `&amp;` are actual data literals. Code spans around those literals are
appropriate. they do not conceal prose.
- T257 changes divisibility by ten to being a multiple of ten. For the integer weighted sum shown,
these statements are equivalent. inclusion of the check digit remains explicit.
- T233 retains panic-specific cleanup separately from ordinary error results. It does not relabel
panic as an ordinary returned error.
- T229 preserves directory-base `/docs/guide/` versus file-base `/docs/guide` resolution and both
concrete result paths.
- T260 retains the conjunction `RuneError` plus a one-byte decoded size for invalid encoding. The
rewritten following sentence is interpreted in that immediately stated condition, not as a claim
that all one-byte runes are invalid.
- T220 contains literal CRLF examples. Reading the original projection with universal-newline
conversion can falsely suggest a changed string. Raw projection bytes contain the projection
writer's CRLF conversion around the embedded CRLF. Current JSON still contains `a\r\nb` and
`a=\r\nb` . This review does not report that presentation effect as a semantic change.

## Verification boundary

The parent independently owns immutable/program/sample/modalities checks and field-aware length
checks. This reviewer did not rerun product acceptance. No runtime conclusion follows from this
report. No JSON or worker projection was edited here. Final acceptance must re-read worker
corrections against the findings above.

Review snapshot recorded at 2026-10-25T22:50:37.362525+00:00.
Aggregate SHA-256 of sorted `topic SHA-256` records:
`d47a374accf3ded796a2cb74b6143c828df5eb4ace30d1d5e043cdbe6441fb6f` . Workers may continue editing
after this snapshot.
