# Persistent terminal observer — prepared source, 2026-10-26

Status: **PREPARED / UNRUN / NOT READY FOR A GRANT.**
C acceptance of the persistent control-plane/controller distinction is pending
(global666 proposal). This module does not make that decision or issue a grant.

## Scope and identities

Only these two files were written:

- `fixtures/native_terminal_observer.mjs`: SHA-256
  `3465b83e7ebc09d3e0f696f6f16560d78970faac6dc2a27cfcb99048e19914ef`,
  24506 bytes, 428 lines, UTF-8 without BOM, LF and final newline.
- This handoff.

Frozen dependencies remain unchanged:

- `run_native_grant.py`: `295b23b5dfc1f94b758ad6a34ba372cbbd0b6ae14b84a3d3b8c85c4280833441`.
- `run_native_window.py`: `9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8`.
- Pinned Python: `D:/ProgramFiles/Python/Python313/python.exe`,
  `d87063e5597f257004c731b66c59c56c91038861c6877b1a3dca6b8c4e919125`.

No native, shared-core, sibling, wrapper, runner, task/spec or other source was
edited. No Git write was made.

## Minimal protocol

Import defines functions and a retained registry only. It does not read files,
launch a process, start a timer, send a message or touch the network.

`startGrantedNative()` requires an actual NEW named grant, an explicit C approval
event for the controller role, a fresh output leaf, the independently reviewed
observer SHA and the current 374-file native-source SHA. It refuses placeholders
and historical580/509/236/Go-native-20261026-01. A persistent exclusive grant
marker also prevents restart with a reused grant under another output name.

Before ACK, it hashes the pinned Python/wrapper/runner and current native inputs.
ACK and validation launch run in one async function without a model turn between
them. A failed/unconfirmed ACK or post-ACK drift produces no SDK launch. More
than7.5s in ACK/preflight retires the attempt without launching validation.

The registry retains the ORIGINAL validation ChildProcess and every original
publisher ChildProcess. The validation process's actual `close` event is the
terminal authority. There is no PID lookup, timeout kill, reset, restart or
successor grant. A live process past180s remains HOLD with its original object.

After actual validation close, the observer reads final wrapper/controls/native
reports, binds grant/root/PIDs/report hashes, and requires every recorded phase's
exact process handle/PID/creation FILETIME plus terminal, cleanupConfirmed,
Job active0 and handlesClosed. It publishes RELEASE only when that final drain
proof exists. Missing or contradictory evidence yields explicit HOLD.

Publisher commands use a fixed PowerShell command and `--stdin`; neither grant
nor message body is interpolated into shell code. Sends are serialized behind
the previous original publisher's actual close. Publication failures stay in the
registry and durable report. `retryFinalPublication()` can retry a failed final
send only after its original publisher is terminal. It never launches validation.

The final durable observer report records ACK event, validation close,
publication event and publisher close. Budget acceptance requires both actual
channel-event ACK-to-final-event time and monotonic ACK-attempt-to-publisher-close
time to fit180s. The outgoing message does not predict its own delivery time.

## Role boundary requiring C acceptance

The persistent Node runtime is control-plane infrastructure. It remains live.
The module claims terminal state only for the original validation ChildProcess
and the separately observed publisher ChildProcesses. It does NOT claim that a
Codex tool invocation, the persistent Node runtime, or the publisher currently
sending the message has exited. Node does not expose a numeric Win32 HANDLE for
its ChildProcess, so none is fabricated; exact Win32 Job/process identities come
from the pinned child reports.

This differs from the older requirement to observe a temporary outer tool
session itself exit. C must accept the distinction before any import/start or
READY publication. The module requires that actual approval event as an input.

## Future NodeRepl shape — DO NOT RUN NOW

Replace every placeholder from actual fresh C delivery and a fresh source
preflight. The example intentionally fails validation while placeholders remain.

```javascript
var observer = await import('file:///D:/MyNewProjects/qfli_go/.trellis/tasks/10-22-go-offline-ide/research/fixtures/native_terminal_observer.mjs');
var observedRun = observer.startGrantedNative({
  grant: 'REPLACE_WITH_ACTUAL_NEW_GRANT',
  outputName: 'go-native-observed-20261026-REPLACE',
  expectedNativeSourceSha256: 'REPLACE_WITH_FRESH_64_HEX_SOURCE_SHA',
  expectedObserverSha256: '3465b83e7ebc09d3e0f696f6f16560d78970faac6dc2a27cfcb99048e19914ef',
  approvedPersistentController: true,
  controllerApprovalEvent: 'REPLACE_WITH_ACTUAL_global_EVENT'
});
nodeRepl.write({ grant: observedRun.grant, evidence: observedRun.observerDirectory });
```

Later observation does not drive publication; the retained close callback does:

```javascript
nodeRepl.write(observer.observerSnapshot(observedRun.grant));
// Only after FAILED final publication and original publisher terminal:
// nodeRepl.write(await observer.retryFinalPublication(observedRun.grant));
```

`observedRun.done` resolves after final publisher close (DELIVERED or FAILED).
It remains pending while the original validation process remains live.

## Static checks and limits

- `node --check fixtures/native_terminal_observer.mjs`: exit0 (syntax only).
- Text checks: exactly four standard imports (`node:child_process`, `node:fs`,
  `node:path`, `node:crypto`), two explicit spawn sites, no `.kill`, `.terminate`,
  `shell:true`, dynamic command interpolation, SDK probe or implicit grant.
- LF/no BOM/final newline/no trailing whitespace checked.
- Frozen wrapper and runner hashes rechecked unchanged.

The module was NOT imported or executed. No synthetic controls, SDK/native,
product tests, WSL, device or channel publication was run. NodeRepl callback
persistence while idle, Windows spawn/stdio behaviour, real CLI event parsing,
recovery after controller loss and actual timing remain UNPROVEN. A controller
crash can stop observation/publication and cannot manufacture a terminal release.
The 374-file native hash excludes tool adapters such as windows-cc.cmd; the
underlying pinned runner separately captures those tool identities. This is not
complete SDK/sysroot provenance or current-product/OHOS acceptance.

## Independent review supersession

The final reviewed observer is3465b83e7ebc09d3e0f696f6f16560d78970faac6dc2a27cfcb99048e19914ef. The review fixed stdout-descriptor cleanup when stderr-open fails and added a separate fixed adapter pin for native/go_runtime/windows-cc.cmd (5c486c5420c7d74178250e03fa52061c7df638418560744d587bbba7e36c4f8b). Existing pre-ACK and post-ACK requireInputs calls enforce that pin. Reports record adapter identity separately. See native-terminal-observer-source-check-20261026.md. No module import or runtime occurred. Controller approval remains pending.
