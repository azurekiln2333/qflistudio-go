# Independent source check: exact Job controller

Review scope: C717 and `observer-c717-contract-audit-20261026.md` against the new Python controller.
This checker did not import or execute the controller, frozen runner, wrapper, or any target
program. No SDK/native/compiler/test/WSL/device/channel/git operation occurred. AST parsing and file
hashing only were used as mechanical checks.

## Verdict

SOURCE PASS for the reviewed C717 identity/drain contract and the corrected controls admission path.
The initial pre-controls global-clock finding is resolved in the revised source identified below.
No false terminal path was found in the reviewed release checks. No Windows behavior or bounded
execution has been proven. Fresh exact-source coordinator approval and a later named grant remain
mandatory. This source verdict does not authorize importing or running the controller.

## Finding fixed by author: controls admission now preserves the ACK-clock reserve

Initial reviewed SHA-256: `5f727d7bd49d8976c3617e451bdfe472443f7e4a3b5f2b56085957b9f979f749`.
The initial controls path could reach root creation without a global remaining-budget admission
check after child startup and source preflight. That was a source-path finding, not an executed
Windows failure.

Revised source adds `CONTROLS_MIN_REMAINING_SECONDS = 15.0 + PUBLISH_SECONDS` (18 seconds) at line35.
`validation_child` checks this reserve after source preflight at lines265-270. It checks again at
lines287-292 after command/environment preparation, immediately before `ExactRoot` construction.
Both refusals record `controlsSkipped` and break before creating a controls phase or payload root.
The existing finalization path records `noPayloadsStarted` and permits the parent to prove the
validation outer's actual terminal/Job active0 before a truthful deferred release. The result stays
FAIL_OR_INCONCLUSIVE; no skipped controls are promoted to successful validation.

Both native157.5s admission checks remain present. The original ACK monotonic value still drives
both phases. Exact Job ownership, retained HOLD objects, no-kill outer behavior, publisher
serialization and the durable final-sender barrier are unchanged by this correction.

Focused rereview result: PASS at the revised source SHA below. AST parsing passed without import.
No additional source defect was found in this focused change. This does not prove real-time
scheduling, Windows behavior, launch timing or total180s completion.

## C717 matrix

| Requirement | Source evidence | Assessment |
| --- | --- | --- |
| Import has no file/process/Win32 effects | Top-level definitions, constants and `Path` construction only; actual dispatch behind `__main__` | Source satisfied |
| Original validation root exact identity/private Job | `ExactRoot` retains original frozen `OwnedJob`; suspended creation, HANDLE/PID/FILETIME, assignment before resume | Source satisfied; Win32 compatibility UNRUN |
| No implicit outer kill on handle close | Clears and queries job limit flags before root creation; waits for original Job empty before close | Source satisfied; flag behavior UNRUN |
| True root terminal plus Job active0 | `OwnedJob.empty` uses original root wait/exit query and same Job accounting; `exact_terminal` requires identity and closure | Source satisfied |
| Every payload terminal/active0 | Phase report bindings plus `payload_drain`, exact phase outer ledger and final validation-outer Job | Source satisfied |
| Publisher descendants drained | Every PowerShell sender gets original private `ExactRoot` Job; serialization waits for root terminal and Job active0 | Source satisfied; real PowerShell/CLI descendant behavior UNRUN |
| Final publisher separately bounded/recorded |3s observation deadline, exact retained identity, actual event parse/exit and terminal evidence | Source satisfied as acceptance deadline, not a forced termination bound |
| Pending publisher blocks later sender/validation | `publisher` refuses unresolved children; ACK is fully drained before validation launch | Source satisfied |
| Deadline means HOLD, never inferred terminal | `wait_original` marks deadlineExceeded then keeps polling original objects without kill/replacement | Source satisfied |
| Final sender proof before next-run eligibility | `deliver_final` captures actual event/result, saves controller evidence, then unlinks exclusive unresolved guard | Source satisfied |
| Controller restart cannot imply no work | Durable unresolved guard blocks `start`; no automatic recovery/deletion | Source satisfied; recovery deliberately unavailable |
| No SDK after completed validation | Post-validation paths only inspect reports and publish; `retry-final` only republishes | Source satisfied |
| No self-terminal claim | Final body labels current sender live and persistent controller control-plane-only | Source satisfied |
| Fresh source approval/grant required | Requires C approval after717 naming protocol+controller hash and a later distinct grant receipt; consumed markers reject replay | Source satisfied procedurally; parent must reconcile authoritative channel events |

## Reviewed real ownership implementation

Frozen `run_native_window.py` `OwnedJob.start` calls `_winapi.CreateProcess` suspended, retains the
returned process HANDLE immediately, records creation FILETIME, validates `GetProcessId` , assigns
the private Job, then resumes the original thread. The thread HANDLE closes in `finally` .
Assignment/resume failure retains the exact never-resumed root rather than substituting a PID
lookup. `OwnedJob.empty` requires actual root terminal and Job active0. `ExactRoot.exact_terminal`
additionally requires root creation, assignment, resume, valid identity values, no recorded errors
and closed handles.

The outer controller clears KILL_ON_JOB_CLOSE before creating its root. The frozen payload runner
retains its original internal control behavior. This controller does not rewrite that frozen
behavior. A partial-start failure or missing observation can remain HOLD indefinitely. That is
conservative ownership retention, not a bounded successful run.

## New orchestration boundary

This implementation does not execute `run_native_grant.py` . It hashes that wrapper and AST-reads
its literal36-path formatting ownership list. The new validation child serially invokes the frozen
runner for controls and then native. Native admission is checked twice against the original parent
ACK monotonic value, including a check after preflight. Controls must pass, drain and remain
within15s before native starts. Native150 includes frozen test/vet reporting. A missing, reordered,
mismatched or undrained report prevents final proof.

This hierarchy is materially different from the old approved command. Previous647/655 approval is
not inherited. The receipts in `validate_request` are operator-supplied data, not authentication.
The main agent must independently read and reconcile the exact source approval and grant.

## Durable final-sender barrier

`publisher` is synchronous and retains all original sender roots. A sender deadline does not release
the Job. Once a sender really terminates, the code parses the actual returned channel event and
checks author, recipient, body and sequence. `deliver_final` only makes `nextRunEligible` true after
confirmed publication and exact terminal/active0 for every child. It writes this evidence before
removing the unresolved guard. Evidence failure restores false eligibility. A remaining guard still
rejects another run even if a previous process died.

`nextRunEligible` is cleanup/publication eligibility. It is neither test success nor a new grant. A
final sender can be late and still eventually drain. Its late result cannot become within180
success: the actual terminal-time field remains separate. Coordinator review must use both fields
and the actual event timestamps.

## Unproven gates

Actual suspended creation, nested Jobs, no-kill flag clearing/query, cross-process monotonic-clock
comparison, inherited handles, Windows process scheduling, PowerShell/Trellis UTF-8/event behavior,
publisher3s acceptance, true ACK-to-final-sender180s, SDK link/test/vet and all target behavior are
UNRUN. A syntactically valid source file cannot prove those gates.

## Verification

- Standard-library AST parse: PASS without import.
- Initial controller hash matched the first author freeze. Revised hash is bound below.
- Frozen runner and wrapper hashes matched their declared pins.
- No source fixture was changed by this reviewer. Only this independent report was written.

Reviewed controller SHA-256: `5f727d7bd49d8976c3617e451bdfe472443f7e4a3b5f2b56085957b9f979f749` .
Size: 34333 bytes. Lines: 620.
Review timestamp: 2026-10-25T23:38:17.177277+00:00.

## Focused rereview identity

Revised controller SHA-256: `6ec0d4f5d059eeab2ddc7c9313080db06ab70df941c5d442e3fc356a20acefdb`.
Size: 35543 bytes. Lines: 637. AST parse: PASS.
Focused rereview timestamp: 2026-10-26T01:38:24.162646+00:00.
No import, process restart/relaunch, SDK/native/runtime/test/channel/git operation occurred.
