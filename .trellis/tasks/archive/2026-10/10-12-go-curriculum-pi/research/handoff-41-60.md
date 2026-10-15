# Handoff — T041–T060 to w8:p3 (B)

Date: 2026-10-12. From: Pi w8:p2 (T001–T040). To: Pi w8:p3 (B).

## Status at handoff

- T041–T060: **no topic JSON and no sample content authored by w8:p2.** Only
  empty `tool/go_curriculum/samples/T041..T060/` directories existed (created
  early during scaffolding); B may use or recreate them freely.
- w8:p2 scope is now **T001–T040** + shared tools/aggregate.
- Contract: `tool/go_curriculum/schema.md` (authoritative). Notes:
  - Each `samples/T<NNN>/` needs a `go.mod` (`module qfli.example/tNNN`).
  - `tutorial.code` must be byte-identical to the sample file.
  - `verify.py` asserts tutorial sample and, if the example differs, the
    example against its own `expectedOutput`.
  - Trailing-newline/trim behavior: `verify.py` trims stdout and expected before
    comparing; a trailing newline in `verification.expected` is fine. No schema
    change needed (agreed with B).

## Tools / baseline (shared, owned by w8:p2)

- `assemble.py`, `verify.py`, `dedup.py`, `patch.py`, `author.py`, `README.md`,
  `schema.md`.
- `baseline/{tutorials,examples}.json` + `baseline/shared-sha256.json`.
- SDK: `native/build/go-sdk-1.27.1/go/bin/go.exe`.

## Leftover scripts

`gen_a.py`, `gen_a2.py`, `gen_a3.py`, `gen_a4.py`, `gen_t001.py` only generate
T001–T040 topic JSON; safe and irrelevant to T041–T060.
