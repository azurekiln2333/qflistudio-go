# Exact Job controller source boundary — 2026-10-26

Prepared source only. This work changes two new files: the controller fixture and this handoff. It leaves the frozen runner, wrapper, Node observer, native inputs, shared core and sibling files untouched.

The missing behavior is exact identity and Job ownership for the validation outer and every channel publisher. The fix belongs in a persistent Python control plane. It creates each root suspended, assigns a private Job before resume, retains the original HANDLE/PID/FILETIME, and queries the same Job until the root is terminal and active0. A live or uncertain root stays HOLD with original handles. The controller never kills or resets.

The frozen OwnedJob helper has KILL_ON_JOB_CLOSE. The new adapter clears that flag before creating any child and closes handles only after terminal plus active0. Partial start or assignment failures retain the exact suspended root and Job. A crash can leave payloads alive. A durable global unresolved-run marker blocks automatic recovery and any later grant until independently reconciled.

The frozen wrapper accounts from its own run entry rather than the outer ACK. The new validation-child mode therefore runs the frozen controls and native runner serially itself. It reads only the literal36-path owned list from the SHA-pinned wrapper AST. It launches native only with157.5s remaining from the original ACK-attempt clock. This is a new reviewed validation-root protocol, not authorization to reuse command647 or grant655.

ACK and final senders use separate private Jobs and deadlines. Deadline expiry records HOLD and keeps waiting on the same exact identities. No second publisher starts before the previous root and its Job are terminal and active0. Final RELEASE requires actual validation outer terminal, all child/payload reports drained, and earlier publishers drained. The live final sender never claims its own terminal. Its later terminal/result/active0 evidence is written durably before next-run eligibility.

Runtime evidence remains UNRUN: nested Jobs, Windows handle behavior, actual CLI publication, callback/loop scheduling, total180 timing, native compiler/link/test/vet and OHOS. No READY, grant request, import or execution is part of this change. Independent source review and C approval of this exact protocol are required first.

## Frozen author result

Controller: `fixtures/native_terminal_job_controller.py`

- SHA-256: `6ec0d4f5d059eeab2ddc7c9313080db06ab70df941c5d442e3fc356a20acefdb`
- Size: 35543 bytes, 637 lines, UTF-8 without BOM.
- Check: standard-library `ast.parse` of source bytes passed. The controller was not imported or executed.
- Frozen dependencies remain unchanged: runner `9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8`, wrapper `295b23b5dfc1f94b758ad6a34ba372cbbd0b6ae14b84a3d3b8c85c4280833441`, old observer `3465b83e7ebc09d3e0f696f6f16560d78970faac6dc2a27cfcb99048e19914ef`.

### Hierarchy and ownership

The Python `--serve` process is persistent control-plane infrastructure. Each ACK/final publisher is a separately retained exact suspended PowerShell root in its own private Job. The PowerShell root runs the fixed Trellis CLI sender. Its Job must reach active0, covering its CLI descendants, before another sender or validation root starts.

The controller launches the same source in `--validation-child` mode as the exact validation outer. That child has a separate original root HANDLE/PID/FILETIME/private Job. It serially launches frozen `run_native_window.py` controls and native phases in their own exact private Jobs. The frozen runner keeps its original inner payload Jobs. Thus the nesting is controller -> validation outer Job -> phase Job -> existing payload Job. Both parent and child retain original objects until terminal plus active0. No PID rediscovery substitutes for the original handles.

The validation-child mode replaces the old wrapper as the execution outer. It does not execute `run_native_grant.py`. It verifies that file and reads only its literal36-path ownership list through AST. This change fixes the original ACK-clock accounting gap: native starts only after both remaining-budget checks pass at157.5s. A fresh coordinator review must approve the new command/root hierarchy. No earlier command approval applies automatically.

### Control-plane input

A future reviewed invocation would use the pinned Python with `-B -X utf8 <controller> --serve`. Its NDJSON commands are `start`, `status`, and `retry-final`. A `start` request must include the exact protocol, new grant, fresh output name, expected controller/native SHA values, actual reconciled C approval event and actual later C grant event. The approval must be after717 and name this exact source SHA and protocol. The source refuses consumed655, C580, Go236 and Go509. These input receipts are procedural assertions made by the root after authoritative channel reconciliation. They are not cryptographic authentication and the controller does not fetch or interpret arbitrary channel history.

`retry-final` only retries final publication after original validation and earlier senders are all terminal+active0. It cannot rerun validation. Fixed publisher script bytes are checked before each publisher. A failed or uncertain final publisher retains the unresolved-run guard. The guard clears only after final-sender actual terminal/result/active0 evidence is durably saved. A crash leaves the guard in place. No automatic process recovery, guard deletion, stale PID claim or grant replay exists.

### Failure and acceptance boundaries

Deadline expiry marks HOLD and preserves original handles. It does not terminate any process. Publishers have3s acceptance deadlines. A hung sender therefore keeps its exact identities and blocks later publication or validation. Actual terminal/result evidence after a late return remains recorded. A late result cannot be reclassified as within180s. `nextRunEligible` is cleanup/publication eligibility only, not permission or test success. C still issues every subsequent grant.

Source or budget retirement before validation sends a final terminal handoff only if every prior publisher has exact terminal+active0 proof. Failed controls or native assertions can release an empty host slot while retaining FAIL_OR_INCONCLUSIVE. Unknown payload reports or partial suspended-start failures remain HOLD. Evidence-write failures in live polling retain ownership. Durable final-sender write failure keeps the guard. The old Node module is not integrated or enabled by this file.

Unproven gates: actual Windows suspended creation, no-kill flag clearing/query, nested Job compatibility, original-handle polling, inherited handle behavior, real PowerShell/Trellis UTF-8 publication, command-line payload size, publisher3s timing, process scheduling, clock sharing across processes, actual native tests/link/vet, total ACK-to-final-sender180s and coordinator reconciliation. No runtime tests, SDK/native/compiler/build/device/WSL operation, channel publication, Git operation, READY or grant request ran in this author task.

Independent review must assess both the new validation orchestration and the C717 source matrix. Runtime controls remain required under a fresh expressly approved grant. This report is source evidence only.


## Focused controls admission correction

The independent source review found that child startup or preflight could consume the original ACK clock before controls launched. The source now requires at least18s remaining for the controls15s plan plus the explicit final sender3s reserve. It checks after preflight and again immediately before `ExactRoot` construction, after command/environment preparation. A refusal records `controlsSkipped` without creating a phase or root. The existing `noPayloadsStarted` final report truthfully releases only the validation outer after its actual terminal and active0. Both native157.5s checks remain unchanged. Exact Job, HANDLE, HOLD and no-kill behavior remain unchanged. The corrected source received AST parsing only. No import, process or runtime operation occurred.
