# One-process native grant orchestration — source handoff (2026-10-26)

Prepared by the Go implement worker. **Source only.** No grant is requested,
accepted, reserved or inferred here. No native/test/SDK/control invocation, no
runner import, no Windows API self-control, no kill and no reset was performed
while preparing this file. Nothing was published to the channel and no grant was
self-issued.

## The concrete gap this closes

C580 showed the failure mode precisely:

- The same-runner controls really **PASSed in 0.227s** (wrapper chunk `82d4f5`
  exit0; normal HANDLE380/PID69904/FILETIME134374213689519626 exit0 active0;
  held-child negative HANDLE432/PID73396/FILETIME134374213690111615 exit0
  active0 with the release gate correctly rejected while the child was live).
- The **model paused 105.262s between the two tool calls**. The native budget
  guard chunk `03a1ea` exited1 before invoking the runner/go/gofmt, because less
  than the required 150s of the 180s grant remained.
- Actual parent elapsed for that window was **225.3771807s**.

The gap is orchestration, not containment: two separate tool calls cannot
guarantee serial timing, because the model turn between them is unbounded. The
fix is to put both phases inside **one** process, so there is no model pause
between them.

## Changed file and identity

- `fixtures/run_native_grant.py` — new standalone Windows/Python 3.11+ wrapper,
  standard library only. SHA-256:
  `295b23b5dfc1f94b758ad6a34ba372cbbd0b6ae14b84a3d3b8c85c4280833441`,
  45077 bytes, 880 lines, LF, final newline, no trailing whitespace.
- This handoff.

Not modified: `fixtures/run_native_window.py` (frozen, see below), both `.args`
files, native sources, product/shared/spec files and sibling repositories.

## Frozen dependency (unchanged, asserted)

`fixtures/run_native_window.py` stays byte-identical at
`9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8`
(38484 bytes, re-hashed during preparation and unchanged). The orchestrator
records the expected and actual SHA-256 and **refuses to create any directory or
start any process** when they differ. The runner is invoked as a subprocess; it is
never imported and never edited.

## One-invocation contract

`run_native_grant.py` takes one NEW named grant and one explicit successor owner,
then in a single process:

1. Asserts the owned-go template is 36 distinct paths.
2. Asserts the frozen runner hash, the Python identity and a **fresh** evidence
   root (an existing directory is refused before any child starts).
3. Launches `run_native_window.py --control-only` with the **same**
   `sys.executable`, the **same** runner path, the **same** grant and the **same**
   successor owner. Controls keep the runner's own 15s plan
   (10s work + cleanup to 13s + evidence).
4. Retains the exact `Popen` object, records its real PID, process HANDLE
   decimal/hex, creation FILETIME and exit code, and polls `poll()` until the
   **real** terminal state. It never kills, never times out and never restarts.
5. Reads the controls `report.json` and mirrors the native phase's own acceptance
   test: mode `CONTROL_ONLY`, result `PASS`, matching grant, `RELEASE`,
   `withinPlanSeconds` true, exactly two phases passed and drained, terminal
   exit0 with zero Job processes, suspended-then-assigned-then-resumed proven,
   the root-exit/child-live negative gate observed with a live held child, and
   `toolIdentitiesAfter` equal to the current runner/Python identities.
6. Computes `remaining = 180s - monotonic_parent_elapsed` **immediately** at the
   decision point. Native work starts only when controls passed and
   `remaining >= 150s` (the native plan inside the runner). Otherwise it records
   `UNRUN_BUDGET_GUARD` and starts nothing.
7. Launches the native phase in the same process, with the same Python identity,
   grant and successor, a fresh `native/` leaf, `--controls-report` pointing at
   the just-written controls report, and the explicit 36 `--owned-go` arguments.
8. Waits for the native child's real terminal state under the same no-kill policy
   and records its own durable evidence and the child's report summary.

Because steps 3–8 run in one interpreter, there is **no model turn** between the
controls verdict and the native launch. That is the entire point of the file.

## Explicit 36-owned argument template

The 36 native `.go` paths are frozen in `OWNED_GO_PATHS`, identical to the
reviewed `c580-go-20261026-checks.args` list: the nine source-review-owned paths,
the other scoped native changes, and the vendored `interp/` files, with the
proof-only `stdlib/go1_22_sort.go` and `go1_22_net_rpc.go` excluded. There is no
glob, no git scan and no vendor walk. Ownership changes are a reviewed edit to
this constant, not a CLI override; the wrapper asserts 36 distinct entries and
passes each as its own `--owned-go`.

## Reserve and deadline accounting (revised)

The earlier `remaining >= 150` guard was too thin. The 180s named grant must also
pay for costs outside the native runner's own 150s clock, so the guard now uses an
explicit reserve.

Absolute-time model, all on `time.monotonic()` from the first line of `run()`:

```
grant(180) = run_entry(R0) + t_launch + launch(L) + native_plan(150) + final(F) + release(P)
```

| Term | Seconds | Covers |
| --- | --- | --- |
| `RUN_ENTRY_RESERVE_SECONDS` (R0) | 1.0 | interpreter + import + argparse before `started` |
| `CONTROLS_PLAN_SECONDS` | 15.0 | the runner's own controls plan (inside the 180) |
| `NATIVE_LAUNCH_RESERVE_SECONDS` (L) | 1.5 | Popen + child interpreter startup before its clock |
| `NATIVE_PLAN_SECONDS` | 150.0 | 128s work + cleanup to 140s + evidence to 150s |
| `FINAL_EVIDENCE_RESERVE_SECONDS` (F) | 2.0 | post-terminal identity capture and durable writes |
| `PARENT_RELEASE_RESERVE_SECONDS` (P) | 3.0 | coordinator publish/verify after wrapper terminal |

Derived values:

- `RESERVE_TOTAL_SECONDS = R0 + L + F + P = 7.5`
- `NATIVE_DEADLINE_SECONDS = 180 - R0 - L - 150 - F - P = 22.5`
- `NATIVE_MIN_REMAINING_SECONDS = 150 + RESERVE_TOTAL = 157.5`

Native work starts only when controls PASS and the decision point is at or before
`started + 22.5s` (equivalently `remaining >= 157.5s`). The controls plan is 15s,
so the deadline leaves 7.5s for controls overrun plus inspection before native is
refused. `report["reserveAccounting"]` records every term; `report["budget"]`
records `elapsedAtNativeDecisionSeconds`, `remainingAtNativeDecisionSeconds`,
`deadlineExceeded` and the derived thresholds.

Honest limits:

- `R0` is not measurable from inside `run()`; 1.0s is a conservative allowance,
  not a measurement.
- `L`, `F` and `P` are allowances, not measured durations. If real costs exceed
  them the wrapper can still overrun 180s; that overrun is recorded and now forces
  `FAIL_OR_INCONCLUSIVE`, never PASS.
- A native child that runs its full 150s plan is the worst case. Faster native
  runs finish earlier and leave the reserve unused.

## PASS and exit gating (repaired twice)

The first repair stopped a grant overrun or a failed write from exiting 0, but it
left self-referential and contradictory durable evidence: the persisted report and
message recorded `reportWrite`/`verdictWrite`/`complete` that could only be known
after the write, so a PASS run's files said `complete=False`, and a forced FAIL
could leave a stale PASS message. The independent review raised this as Blockers A
and B, and it is now fixed as follows:

- **No self-referential write claims.** The report no longer asserts its own write
  success. Its durable fields are `finalEvidence.messageWritten` (a fact known
  because the message is written first) and the final `result`. The presence of
  the final report with that result is the attestation; the exit code confirms it.
- **Message before report.** `release-message.md` is rendered and written first,
  then the final `report.json` is written last. The message and the report come
  from the same in-memory `report`, so they cannot disagree.
- **Forced FAIL regenerates the message.** If the message write fails, or if an
  overrun is detected, the verdict flips to `FAIL_OR_INCONCLUSIVE` and the message
  is regenerated and rewritten so no durable message can claim PASS. A final
  report-write failure also best-effort rewrites the message to FAIL before exit 1.
- **Order.** compute `withinGrantSeconds` and the per-phase verdicts; write the
  message; on any message failure or overrun flip to FAIL and rewrite the message;
  recompute `failureReasons`; write the final `report.json`; exit 0 only for
  `result == PASS`, `messageWritten`, and a successful final report write.

`failureReasons` is durable and named in the message. A standalone truth-table
mirror of this gate (no wrapper import) confirms exit 0 only when the core verdict
is clean, the first message write succeeds, the grant was not exceeded before the
final write, the final report write succeeds, and the grant was not exceeded after
the final write.

### Post-write clock recheck (latest repair)

The earlier tail measured elapsed before the final `save_json`, so a slow final
write could cross 180s and still exit 0. The tail now:

- measures `parentElapsedAfterWriteSeconds` immediately after the final durable
  write and stores `withinGrantAfterWrite`;
- withdraws PASS and returns nonzero through `force_failure()` if that write
  crossed the grant;
- persists the post-write timing and re-checks once more (`elapsed_settled`),
  withdrawing PASS again if that crossed;
- `force_failure()` best-effort rewrites `release-message.md` and `report.json` to
  `FAIL_OR_INCONCLUSIVE`, so an earlier PASS never stays authoritative on a known
  failure.

### Clock semantics and publication authority

The wrapper budget is scoped, not global. `report["clockScope"]` records:

- `startScope`: the first line of `run()`; the outer tool ACK, interpreter startup
  before `run()`, and `argparse` are **excluded**;
- `endScope`: the final durable report write;
- `ackToTerminal`: `UNMEASURED`;
- `parentPublication`: `PENDING`;
- `authority`: coordinator actual event timestamps.

`report["withinGrantScope"]` repeats this on the verdict field, and
`report["parentPublication"]` is `UNMEASURED` and pending because this wrapper
never publishes. A wrapper PASS therefore means success **within the run-entry
window**, not a claim that the whole ACK-to-publication grant was bounded. The
coordinator's actual event timestamps remain authoritative.

## HOLD authority (Blocker C)

A transient `HOLD_UNRELEASED` observation is recorded as a historical diagnostic
(`childHoldObserved` and `childHoldSnapshot`) but is **not** sticky authority.
Authority is the child's own **final** `release`:

- the live wait sets `persistentHold` from the child's current `release`, so a
  transient HOLD is true only while it is actually live;
- the final `persistentHold` is `HOLD_UNRELEASED` from any phase's **final** child
  report, never from a stale observation;
- a drained child that rewrote `release: RELEASE` / `result: PASS` is accepted on
  that final release;
- a live Job is never treated as released. A control HOLD never reaches the native
  phase because `wait_terminal` blocks until the child is really terminal, so it
  surfaces as `BLOCKED_CONTROLS` with the final release, not a separate gate;
- the native phase state is `TERMINAL_HOLD` only when the native child's final
  `release` is `HOLD_UNRELEASED`.

## Native acceptance (Blockers D and E)

Native PASS no longer trusts the single `result` field. `native_verdict()` mirrors
`control_verdict()` and additionally requires:

- the wrapper-observed child **exit code 0** (also required for the controls
  child);
- the native report's own `result` is exactly `PASS` (any other value, including a
  torn or missing result, fails; `PASS_REQUIRES_SKIP_REVIEW` and
  `HOLD_UNRELEASED` keep their distinct states);
- `mode == "NATIVE"`, matching `grant` and `nextOwner`;
- `release == "RELEASE"`, `within150Seconds is True`, `withinPlanSeconds is True`;
- three phases, each `passed`, `cleanupConfirmed`, not `timedOut`, no errors,
  terminal exit 0, `jobActiveProcesses == 0`, suspended/assigned/resumed proven;
- `vet.state == "PASS"`, no native report errors, no `toolDrift`, no `sourceDrift`,
  no `nativeDigestDrift`, and a present `toolIdentitiesAfter`;
- the native report's bound `controlsEvidence.sha256` equals the controls report
  this wrapper inspected, and its `grant` matches.

The native phase's own tool set is the **SDK tool set**, which this wrapper cannot
reproduce, so tool identity is judged by the frozen runner's `toolDrift` plus a
present `toolIdentitiesAfter`. That is an honest weaker binding than the controls
path, not a claim of full reproduction.

**Skip policy (Blocker E, strict by decision).** A native run that passed but
reported test `--- SKIP:` lines is left non-PASS. It gets a distinct state
`PASS_REQUIRES_SKIP_REVIEW` and a named reason, and still exits nonzero. Skips are
never promoted to PASS; a skip window cannot produce exit 0.

## Exact future invocation (NOT RUN)

Nothing below has been run. It is the source-only prepared command for a future
fresh named grant. Replace every `REPLACE_` placeholder; the wrapper refuses
`REPLACE_` in `--grant` and `--next-owner`, and refuses C580/Go509/Go236.

```powershell
D:\ProgramFiles\Python\Python313\python.exe `
  .trellis\tasks\10-22-go-offline-ide\research\fixtures\run_native_grant.py `
  --grant REPLACE_WITH_NEW_EXPLICIT_GRANT `
  --next-owner REPLACE_WITH_ACTUAL_NEXT_OWNER `
  --output .trellis\tasks\10-22-go-offline-ide\research\REPLACE_WITH_NEW_EVIDENCE_PREFIX `
  --root D:\MyNewProjects\qfli_go `
  --runner .trellis\tasks\10-22-go-offline-ide\research\fixtures\run_native_window.py
```

- Interpreter: `D:\ProgramFiles\Python\Python313\python.exe`, the identity in the
  C580 evidence. Any other interpreter must be recorded as the actual identity in
  `report["python"]`; the wrapper hashes whatever `sys.executable` is.
- `--grant`: one new explicit name, never a consumed one.
- `--next-owner`: the real successor owner; the wrapper never self-grants.
- `--output`: a new directory that must not exist. The wrapper creates it and the
  runner creates the `controls/` and `native/` leaves. Suggested shape:
  `.trellis\tasks\10-22-go-offline-ide\research\<PREFIX>-grant\`, with
  `<PREFIX>-grant\controls\report.json` and `<PREFIX>-grant\native\report.json`.
- `--root`: the checkout root; it defaults correctly when omitted.
- `--runner`: the pinned runner; it defaults to the sibling `run_native_window.py`.

All other arguments are internal. The wrapper adds `--control-only` for controls,
and `--controls-report` plus the 36 `--owned-go` paths for native. There is no
`--timeout`, no `--force`, no retry flag and no model pause between phases.

### Digest method

- Runner:
  `Get-FileHash .trellis\tasks\10-22-go-offline-ide\research\fixtures\run_native_window.py -Algorithm SHA256`
  must equal
  `9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8`.
  The wrapper asserts this itself before creating any directory or process.
- Wrapper:
  `Get-FileHash .trellis\tasks\10-22-go-offline-ide\research\fixtures\run_native_grant.py -Algorithm SHA256`
  must equal the value in "Changed file and identity" above; the wrapper records
  its own hash in `report["orchestrator"]`.
- Python: the wrapper records `report["python"].sha256` for the actual
  interpreter, so the coordinator can bind a run to an interpreter build.

## HOLD policy (no timeout kill, no restart)

If a child publishes `HOLD_UNRELEASED` in its own `report.json`, the orchestrator:

- records `childHoldObserved` and a snapshot as a historical diagnostic only,
- keeps observing the **same** child and the **same** Popen handle,
- refreshes the parent's durable `report.json` every 5s with `persistentHold`
  taken from the child's **current** release,
- **never** starts native work while a control HOLD is live (it cannot reach the
  native phase, because the wait only ends at the real terminal),
- accepts the child only on its **final** release, so a drained `RELEASE` is
  authoritative and a live Job is never treated as released,
- waits for the real terminal state rather than killing the child or restarting a
  later phase.

A genuinely stuck child therefore produces a persistent HOLD, not a fabricated
release. The parent must retain/poll the same outer tool handle and publish
HOLD/overrun; this wrapper does not manufacture terminal evidence.

## Evidence written by this wrapper

`report.json` (schema 1, `mode: GRANT_ORCHESTRATION`) and `release-message.md` in
the fresh evidence root, including:

- grant, successor owner, parent PID, `startedAt`, `startedMonotonic`;
- runner expected/actual SHA-256 and `frozenIntact`; Python and orchestrator
  identities; `toolIdentitiesBefore`/`After`/`toolDrift`;
- `ownedGoPaths` (36) and `ownedGoCount`;
- per phase: `argv`, output dir, PID, process HANDLE decimal/hex, creation
  FILETIME, terminal, exit code, elapsed seconds, `popenRetained`,
  `childHoldObserved` and the child report summary (path, sha256, release,
  result, plan/work/elapsed, `withinPlanSeconds`, `within150Seconds`,
  `frozenNativeSourceSha256`, vet state, skip review, phase names, problems);
- `budget` (elapsed and remaining at the native decision point);
- `nativePhase` state: `STARTED`/`TERMINAL`/`TERMINAL_HOLD`/
  `PASS_REQUIRES_SKIP_REVIEW`/`UNRUN_BUDGET_GUARD`/`BLOCKED_CONTROLS`;
- `publication: NOT_ATTEMPTED` and
  `successorGrant: NOT_GRANTED` with the explicit reason that **no successor
  grant exists before the wrapper terminal**;
- `persistentHold`, `parentElapsedSeconds`, `withinGrantSeconds`,
  `parentOverrunSeconds`, `failureReasons`, `finalEvidence.messageWritten`,
  `result`.

Exit code is 0 only for a controls PASS, a native exact `PASS`, no tool drift, no
recorded errors, no persistent HOLD on the final release, a grant that was not
exceeded before or after the final write, a written message, and a successful
final report write. Every other outcome is 1, including a budget breach, a failed
write, and `PASS_REQUIRES_SKIP_REVIEW`. Publication remains the parent's action
after the wrapper terminal; this wrapper never publishes.

## Refusals

Before any directory or process: empty grant, `REPLACE_` placeholders, the exact
consumed grants `Go236` / `C580-Go180-20261025` / `Go509`, any grant starting with
`c580`, `go236`, `go509` or `replace_`, and any grant containing `go236` or
`go509`. The pinned runner additionally refuses `Go236` itself. Historical
C580/Go509/Go236 windows are never replayed.

## Checks performed (source only)

- Python `ast.parse`: PASS (no import, no execution).
- Text inspection: LF only, final newline present, no trailing whitespace,
  standard-library imports only (`argparse`, `hashlib`, `json`, `os`,
  `subprocess`, `sys`, `time`, and `ctypes` inside a function).
- Static assertions: `OWNED_GO_PATHS` has 36 distinct entries and all 36 files
  exist; the frozen constant equals the runner's actual SHA-256.
- Static absence checks: no `kill(`, `.terminate(`, `.wait(`, `os.kill`,
  `taskkill`, no socket/HTTP/channel code, no self-grant path.
- Manual review of the serial budget guard, the retained-Popen wait loop, the
  HOLD path and the post-terminal bookkeeping.
- Reserve arithmetic re-checked by hand: `7.5`, `22.5` and `157.5`.
- Gate truth table (standalone mirror, no wrapper import): exit 0 only for a clean
  verdict, a successful first message write, no overrun before the final write, a
  successful final report write, and no overrun after the final write.
- Clock fields present: `clockScope`, `withinGrantScope`, `parentPublication`
  (`UNMEASURED`/pending), `parentElapsedAfterWriteSeconds`, `withinGrantAfterWrite`.
- No self-referential write claim remains: `reportWrite`, `verdictWrite` and
  `reportIsFinal` all occur zero times.

These are source checks only. They do **not** establish Windows API behaviour,
process containment or executable correctness.

## What remains UNRUN / open

- This orchestrator has **never been executed or imported**. Its controls and
  native phases are UNRUN.
- The native phase of the frozen runner remains UNRUN (historical native85731
  exit1 preserved). The C580 controls PASS is historical evidence for the
  controls path only; it is **not** runtime acceptance and it does not prove this
  wrapper.
- No build, corpus, SDK/Flutter, WSL, target, five-ABI, DLL/FFI or HAP/signature
  gate is implied or closed.

## Remaining risks

- The outer tool session can still terminate the parent process externally. A
  hard external kill closes OS handles but cannot manufacture terminal/empty
  evidence; the last durable HOLD stays authoritative until the coordinator
  verifies it.
- Source/tool identity capture and hashing add real I/O time; that can consume
  the budget and produce an honest `UNRUN_BUDGET_GUARD`, never a smaller suite.
- A control that overruns its 15s plan leaves less than 150s and blocks native
  work by design.
- A concurrent path replacement during formatting is not preventable by source
  checks; the coordinator must arrange source ownership for the granted run.
- The orchestrator's own identity is captured, but this is not a full SDK/sysroot
  provenance manifest.
- The post-write recheck cannot delete a PASS file if the FAIL rewrite itself
  fails. In that case the exit code is nonzero, the printed line names the
  overrun, and the coordinator must treat the stale PASS file as non-authoritative.
- `ackToTerminal` and parent publication are `UNMEASURED`; only the coordinator's
  actual event timestamps bound the real ACK-to-publication window.

## Publication and grant ownership

This wrapper publishes nothing and self-issues nothing. `publication` is
`NOT_ATTEMPTED` and `successorGrant` is `NOT_GRANTED` with the explicit note that
no successor grant exists before the wrapper terminal. The parent must publish
this exact report only after the wrapper terminal, and any later native check
needs a fresh named grant.
