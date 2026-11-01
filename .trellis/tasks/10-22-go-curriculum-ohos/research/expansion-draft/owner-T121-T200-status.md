# T121–T200 draft status (2026-10-23)

All **80 substantive topics** are authored as isolated drafts. Each has a
canonical program, paired tutorial/example, Chinese explanation, objective,
concepts, at least two pitfalls, an exercise/answer and independently specified
expected stdout. Inputs are deterministic and offline. The topics cover text,
encodings, streams, collections, numerics, time, files and CLI/configuration.
No addition has been published to the bundled original120 catalog. Runtime
metadata remains desktop pending actual target evidence.

## Per-group historical checks

Paths below are relative to this directory. Each ten-topic group has 30 actual
displayed/canonical operations; each 20-topic group has 60.

| Topics | Official compiler | Host-native runtime |
| --- | --- | --- |
| T121–T140 | `020-official.json`: 60/60 | `checks/text-encoding-fixed-native/native.json`: 60/60 |
| T141–T150 | `streams-official.json`: 30/30 | `streams-native.json`: 30/30 |
| T151–T160 | `checks/collections-official/official.json`: 29/30; unchanged T152 retry `checks/collections-152-official-retry/official.json`: 3/3 | `checks/collections-native/native.json`: 30/30 |
| T161–T170 | `checks/numeric-official/official.json`: 30/30 | `checks/numeric-native/native.json`: 30/30 |
| T171–T180 | `checks/time-official/official.json`: 30/30 | `checks/time-native/native.json`: 30/30 |
| T181–T190 | Pending resource slot | `checks/files-native/native.json`: 30/30 |
| T191–T200 | Pending resource slot | Pending resource slot |

The T152 historical failure was a 15-second compiler timeout under resource
pressure; the source was unchanged for the successful45-second retry. T127
exposed a real interpreter loop-variable bug, repaired by the runtime owner;
its fixed run is retained separately. Do not erase historical failures.

Earlier runs predate the final selected-entry-directory contract and latest
runtime fixes. A fresh full **240/240 official and native** audit remains
required, using `check_owner.py` and new evidence tags. The current isolated
inventory snapshot is `checks/owner80-entry-cwd-final-inventory/`, with 80 paired
topics, 240 cases and zero inventory issues. It does not execute Go programs.

## Authoring and review

`author_common.py` writes only this draft tree. Group scripts are
`author_text_encoding.py`, `author_streams.py`, `author_collections.py`,
`author_numeric.py`, `author_time.py`, `author_files.py` and `author_cli.py`.
`check_owner.py` snapshots an exact topic range and writes isolated catalogs,
manifest and evidence to avoid races with the T201–T280 author.

The final CLI review corrected two exercise descriptions: T193 now asks for
aggregating layer errors while continuing later valid sources; T195 asks to
reject repeated section declarations, rather than requesting behavior already
implemented by the base parser. Source programs and expected stdout are
unchanged by those exercise edits.

Per-owner dedup80 passes. The other author owns isolated combined160/280 dedup
review; no shared aggregate generation is needed for that check. Actual OHOS
execution and substantive independent review remain separate acceptance gates.
The original T106 Helper failure-attribution gate is documented in
`../verifier-runtime-handoff.md` and must be resolved before final acceptance.
