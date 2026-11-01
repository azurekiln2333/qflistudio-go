# Go corpus verifier handoff (2026-10-23, Asia/Shanghai)

## Current boundary

The original 120 topics remain the only bundled content. All 160 additions are
drafts under `research/expansion-draft/`; this verifier owns T121–T200 and the
direct-tools agent owns T201–T280. Promotion waits for the original packaged
OHOS corpus gate. No host build or source test establishes target execution.

Root requested this checkpoint to release the agent slot while global heavy
processes are queued. There is no live verifier compiler/audit handle. Final
official/native exhaustive runs are intentionally pending a resource window
and the T106 runtime semantic repair below.

## Import and audit contract

- Displayed tutorial and example code are separate operations. The original
  manifest covers 240 displayed imports + 120 canonical programs/packages +
  four canonical support-test operations = **364 cases**.
- The actual runner starts in the selected entry's directory. Imported entries
  are `src/main.go` or `src/snippet_test.go`. Same-package helper sources and
  data, including testdata/embed inputs, accompany the entry in `src/`.
  `go.mod`, `go.sum` and complete imported-subpackage trees retain module-root
  paths. All original support files are attached as exact `inputFixtures`.
- Host-native subprocesses start from a neutral scratch directory. The overlay
  records the host process CWD before/after and rejects mutation; it never
  calls `os.Chdir`. The device audit likewise never assigns/restores
  `Directory.current` and records a change before cleanup.
- Official commands execute the entry package with `cwd=entry.dirname`, rather
  than passing only a Go filename. Every manifest/report case records
  `workingDirectory`.
- Tests require typed counts/transcripts and actual bounded execution of test,
  benchmark and registered fuzz seeds. Exit zero or a success-looking line is
  insufficient. Raw stdout/stderr and source/catalog/runtime hashes survive
  in the evidence. Assertion self-tests cover spoofed/missing counts.
- The Python fixture regression independently tests root source/embed/data
  relocation and imported-subpackage embed/data preservation, including CRLF
  bytes. The original samples contain 74 go.mod files and no non-Go fixture or
  go:embed input, so this general mapping correction did not alter their data.

## Current original catalog identity

After removing obsolete import/runtime notes from 43 original topics, all
changed Go source lines are comments and all expected results are preserved.
`legacy-note-cleanup.json` records the affected IDs and sample before/after
hashes; `cleanup_legacy_notes.py` asserts unchanged executable non-comment
lines and expectations. The real SDK-only generation/race/coverage/pprof
boundaries remain described explicitly.

Both manifest paths are byte-identical and inventory all 364 cases with zero
issues:

- `assets/curriculum/tutorials.json` SHA256:
  `a4f3d2b1a081cb89f4666f97c2f50c6623a305b058f20d6d7b74165a1ab984bc`
- `assets/curriculum/examples.json` SHA256:
  `f9674e28f6c199b15e8ff2b97a76f7f2b7c1c6f373c71d2eec1e13b5f6707ab1`
- `assets/curriculum/audit-manifest.json` and
  `tool/go_curriculum/evidence/catalog-audit-manifest.json` file SHA256:
  `c306b6bd5fa52da3aa45c3b1c4f5fe141366c5516783cd587af37c4edef79ffc`
- Manifest `inventorySha256`:
  `687f9d6e02f0d2ccdde9681e8894897261d26bf28cc2696a70b542151f3636fc`

No execution report yet binds these new comment/catalog hashes and the final
entry-directory runtime together. Regenerate this identity after further edits.

## Execution evidence and its limits

Historical original official baseline `catalog-official-import-baseline.json`
passed **364/364**. `catalog-native-neutral-cwd.json` and `.log` passed
**364/364**, with no inventory/coverage issues and `deviceExecution=false`.
That native report records source hash
`dc2a647dc6d03d69e5e32befcb4411db3b637a09d533f6b2e91e4c9f439af9c1`
and binary hash
`ac0962cd72d0ce554bafae7273112892024b1cd8e8deaba31036019ac0a4a0d3`.
It predates the latest entry-directory, loop and goroutine lifetime fixes and
the comment cleanup. Preserve it as historical evidence, not final acceptance.

T121–T200 are all authored. Earlier per-group runs cover T121–T190 native and
T121–T180 official. They do not form a current full 80-topic run. T127 exposed a
real interpreted loop-variable defect, fixed by the runtime owner with focused
regressions; its repaired text/encoding group passed 60/60. T152's initial
official 15-second compiler timeout is retained; an unchanged retry with a
45-second bound passed 3/3. T181–T190 official and T191–T200 both execution
backends remain pending, followed by fresh full-range checks. See
`expansion-draft/owner-T121-T200-status.md` for exact evidence locations.

## T106 semantic gate

Independent review identified that the embedded `t.Helper()` path does not yet
prove correct caller attribution for a failing helper assertion. Root owns the
runtime follow-up and has paused final library rebuild. The ordinary T106
successful-path case only proves its assertions can pass: **364/364 successful
corpus operations do not establish the lesson's failure-attribution behavior**.
Require a focused failing helper regression that checks the learner call-site
file/line, preserves the failure/nonzero result, and passes through the actual
embedded testing engine before the final runtime/package is accepted. Retain
this gate independently of the exhaustive successful corpus report.

## Checks completed at this checkpoint

- Original assemble: 120 tutorials and 120 examples; no draft promotion.
- Original inventory: 364 cases, zero issues; both manifests regenerated.
- Isolated T121–T200 assemble/inventory: 80 paired topics / 240 cases, zero
  issues; 80-topic substantive dedup passed.
- Original 120-topic substantive dedup passed.
- `audit_native.py --self-test`: **8 passed**, including CWD and data layout.
- `test_verify_race.py`: **5 passed** using injected gate outcomes. These are
  verifier regressions, not proof of running samples under `-race`.
- Earlier Flutter audit/content tests: **16 passed**; Dart analyze of the
  integration audit and both tests was clean. Those checks predate the final
  documentation-only catalog rewrite; current-tree rerun is pending root's
  resource schedule.
- Focused `git diff --check`: clean; Git emitted line-ending conversion notices.

## Resume commands after root grants a resource slot

Use the pinned local SDK. Native compilation previously hit Windows error1455;
retain `GOMEMLIMIT=512MiB`, `GOGC=20`, `GOMAXPROCS=2` and `GOFLAGS=-p=1`.
The harness sets local/offline toolchain behavior and captures hashes.

```powershell
$env:GOMEMLIMIT='512MiB'
$env:GOGC='20'
python tool/go_curriculum/audit_native.py --backend official --timeout 45 --manifest-out .trellis/tasks/10-22-go-curriculum-ohos/research/catalog-final-official-manifest.json --out .trellis/tasks/10-22-go-curriculum-ohos/research/catalog-final-official.json
python tool/go_curriculum/audit_native.py --backend native --timeout 45 --manifest-out .trellis/tasks/10-22-go-curriculum-ohos/research/catalog-final-native-manifest.json --out .trellis/tasks/10-22-go-curriculum-ohos/research/catalog-final-native.json
python .trellis/tasks/10-22-go-curriculum-ohos/research/expansion-draft/check_owner.py --first 121 --last 200 --tag owner80-final-official --backend official --timeout 45
python .trellis/tasks/10-22-go-curriculum-ohos/research/expansion-draft/check_owner.py --first 121 --last 200 --tag owner80-final-native --backend native --timeout 45
```

Run sequentially, preserve stdout/stderr logs, and use fresh tags if source
changes require another pass. The direct-tools agent is independently checking
combined draft/original dedup in isolated snapshots. Root coordinates final
five-ABI rebuild, packaged manifests/native hashes and actual OHOS FFI run.

No commits, shared-core asset writes, destructive Git changes or `go mod vendor`
were performed by this verifier continuation.
