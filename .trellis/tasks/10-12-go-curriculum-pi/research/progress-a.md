# Progress — Go curriculum (Pi w8:p2, T001–T040)

Scope (revised): T001–T040 + shared tools/aggregate. T041–T060 handed to w8:p3
(see handoff-41-60.md). Not touching `test/go_curriculum_content_test.dart` or
`tool/go_curriculum/mobile_check/` (w8:p4).

## Tools

- assemble.py, verify.py, dedup.py, patch.py, author.py, README.md, schema.md.
- SDK: `native/build/go-sdk-1.27.1/go/bin/go.exe` (go1.27.1).
- Baseline: `baseline/{tutorials,examples}.json` + `baseline/shared-sha256.json`.

### Tool hardening (per w8:p4 review)

1. verify.py no longer trusts runCommand: rejects shell metacharacters, requires
   first token `go`/`go.exe` and a Go subcommand, and force-runs `go build ./...`
   per topic. Negative test (spoofed `cmd /c echo...`) now FAILs.
2. verify.py `--race`: real `go test -race` via WSL `qfli-java-build` +
   `mobile_check/run_race.sh`; records RACE-OK/RACE-FAIL (S7 topics use it).
3. assemble.py requires `tutorial.output` non-empty (shared release validator
   needs it); schema.md documents output is display text, decision = verification.
4. verify.py asserts tutorial.code == sample bytes and runs the example variant
   against its own expectedOutput.

## Topic batches

- Batch 1 (T001–T020): DONE. verify 20/20, dedup clean.
- Batch 2 (T021–T040): DONE. verify 20/20.
- Filled go.mod for samples T021–T040.
- T001 corrected (removed filler runtime call); T006 fixed real Go rule;
  T021 delete-mutation honesty; T007 distinct variant asserted separately.

## Notes

- assemble over the full topics dir currently stops at w8:p3's T077 (empty
  output) — expected; that author must give test-pass topics non-empty output.
  w8:p2's T001–T040 all have non-empty output.

## Final result (120/120)

- assemble OK: 120 tutorials, 120 examples from 120 topics.
- verify 120 passed, 0 failed. dedup clean. patch dry-run: non-Go kept=1520,
  Go 100 -> 120.
- T083 made deterministic (slow branch waits on a never-ready channel; fast path
  uses a non-cancelled context, no wall-clock race). T040/T047/T052/T053 carry
  explicit native-Yaegi platform-limit notes and stay desktop.
- compile step no longer writes binaries into samples (temp output / cleanup).
