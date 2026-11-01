# Go native readiness record — 2026-10-26

Owner: check worker, task `10-22-go-curriculum-ohos`.
Scope: record readiness and outcome state. Source-only. No runtime, no SDK, no
native build/test, no WSL, no device, no git mutation, no source edits, no
message publication.

## 1. Current status

**READY647 is CONSUMED. The slot ran, failed at link, and was released.**

- Grant: global655 `Go-native-20261026-01`.
- ACCEPT: global658.
- Final terminal RELEASE: global661, successor `c-coordinator`.
- Diagnostic clarification: global664.
- global666: READY647 retired, **no new READY**. Go is source-only with no
  reservation.

- No native pass is claimed.
- No end-to-end bounded success is claimed.
- Go holds no live validation handle, PID, Job or host slot.

## 2. Run outcome

| Phase | Result | Duration |
| --- | --- | --- |
| Controls | PASS | 0.512 s (global661) |
| gofmt | PASS | changed one file |
| Native test | FAIL at link, before any test case | 19.391 s (global661) |
| Vet | UNRUN | — |
| Wrapper (internal) | — | 19.914 s |

Wrapper-level roots, from global661:

| Phase | PID | Handle | Creation FILETIME | Exit |
| --- | --- | --- | --- | --- |
| controls | 50128 | 332 | 134374323147474401 | 0 |
| native | 57528 | 324 | 134374323152619811 | 1 |

Actual outer tool session `79718` was observed terminal with exit 1.

### Link failure

The native test root `9032` exited 1 during LINK, before any test case executed.
`test.stderr.bin` records `lld unable to find library -lgcc_eh`, twice, through
`native/go_runtime/windows-cc.cmd` (global664).

### gofmt boundary

gofmt PASS and changed only `native_callback_provenance_test.go`.
Permitted post-format frozen source digest:
`574b1478dd41ce41e23a632fb2624ec6168c209d6c38420b0e027b6ef2859298` (global664).
Source drift and tool drift are empty.

### Child Jobs (authoritative, global661)

Four exact child Jobs, all `terminal: true`, `jobActiveProcesses: 0`,
`handlesClosed: true`, `cleanupConfirmed: true`,
`assignedBeforeResume: true`:

| Phase | Job handle | PID | Exit |
| --- | --- | --- | --- |
| control-normal | 400 (`0x190`) | 52320 | 0 |
| control-root-exit-child-live | 452 (`0x1c4`) | 10656 | 0 |
| gofmt | 460 (`0x1cc`) | 70536 | 0 |
| test | 408 (`0x198`) | 9032 | 1 |

Child reports on disk:

- `.trellis/tasks/10-22-go-offline-ide/research/go-native-next-20261026-01/controls/report.json`
  — `result=PASS`, `release=RELEASE`, elapsed 0.221 s, 2 phases, 0 errors.
- `.trellis/tasks/10-22-go-offline-ide/research/go-native-next-20261026-01/native/report.json`
  — `result=FAIL_OR_INCONCLUSIVE`, `release=RELEASE`, elapsed 19.136 s,
  `vet.state=UNRUN`, `sourceDrift=[]`, `nativeDigestDrift=false`,
  `toolDrift=[]`, `testSkips=[]`.

## 3. Coordination budget: FAILED

From global664, authoritative:

- ACK658 at `20:05:14.650Z`.
- RELEASE661 at `20:09:55.009Z`.
- Actual elapsed **280.359 s** against a 180 s budget.

The wrapper's internal 19.914 s did not bound the total. Publication lag after
the outer session had already exited caused the breach.
This is a coordination-budget failure, not a native result.

## 4. Identities used by the run

| Artifact | Value |
| --- | --- |
| Wrapper `fixtures/run_native_grant.py` | `295b23b5dfc1f94b758ad6a34ba372cbbd0b6ae14b84a3d3b8c85c4280833441` |
| Frozen runner `fixtures/run_native_window.py` | `9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8` |
| Native source, pre-format (374 files) | `61c25dceaa6d7dd067410c32a493378bfef82ab9686345902b79ae2d883f68e7` |
| Native source, post-format (374 files) | `574b1478dd41ce41e23a632fb2624ec6168c209d6c38420b0e027b6ef2859298` |
| Python `D:/ProgramFiles/Python/Python313/python.exe` | `d87063e5597f257004c731b66c59c56c91038861c6877b1a3dca6b8c4e919125` |

The frozen runner was intact and tool drift was empty.

## 5. Historical: the readiness that was consumed

global647 (`go-offline-1022`, `2026-10-25T19:44:47.235Z`) requested, and not
granted, a fresh slot. It published the exact command that global655 later
authorized with `--grant Go-native-20261026-01`:

```text
D:/ProgramFiles/Python/Python313/python.exe -B -X utf8 .trellis/tasks/10-22-go-offline-ide/research/fixtures/run_native_grant.py --grant NEW_NAMED_GRANT --next-owner c-coordinator --output .trellis/tasks/10-22-go-offline-ide/research/go-native-next-20261026-01 --root D:/MyNewProjects/qfli_go --runner .trellis/tasks/10-22-go-offline-ide/research/fixtures/run_native_window.py
```

The output path is now populated and must not be reused as a fresh path.

Earlier slot `C580-Go180-20261025` was accepted at global584 and released at
global585. It is consumed. Acceptance-to-publication was 225.377 s against a
180 s budget. Native compile/test/vet never launched.

## 6. Why there is no new READY (global666)

global666 retires READY647 and requests no further grant. Two conditions must be
prepared and reviewed first:

1. A source-level fix for the Windows linker failure (`-lgcc_eh`).
2. A deterministic post-outer-terminal relay that bounds publication.

The proposed controller keeps a persistent control-plane observer. That observer
retains the original spawned validation child process, reads wrapper, native and
controls drain evidence on authoritative exit, and publishes immediately. The
controller starts no SDK work and issues no successor grant. Controller runtime
must stay distinguishable from the validation outer process.

## 7. Open gates (unchanged by this run)

1. Native host test and vet of `native/go_runtime`: NOT PASS. Test failed at
   link. Vet UNRUN.
2. Native host run of the 120-topic corpus: UNRUN.
3. Official Go SDK acceptance: UNRUN.
4. Packaged OHOS HAP verification: UNRUN.
5. Real device execution on OHOS: UNRUN, no connected target.
6. Apple build and device verification: UNRUN.
7. Full Go test, build and import gates: UNRUN.
8. Draft promotion of the 160 topics: blocked on the OHOS baseline.

## 8. Explicit non-claims

- This record grants nothing and accepts nothing.
- This record does not claim a native pass.
- This record does not claim bounded coordination success. The budget failed.
- Controls PASS proves process containment only. It proves nothing about the
  Go toolchain.
- Script-internal PASS is not end-to-end proof.

## 9. Sources read

- Global channel `qfli-core-release-sync`, `seq` 647, 655, 658, 661, 664, 666,
  read via `trellis channel messages --scope global --raw`. No remote call.
- `.trellis/tasks/10-22-go-offline-ide/research/go-native-next-20261026-01/controls/report.json`
- `.trellis/tasks/10-22-go-offline-ide/research/go-native-next-20261026-01/native/report.json`
- `.trellis/tasks/10-22-go-offline-ide/research/run-native-grant-independent-check-20261026.md`
- `.trellis/tasks/10-22-go-curriculum-ohos/research/go-coordination-checkpoint-20261026.md`
