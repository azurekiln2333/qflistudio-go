# Bounded native runner source handoff — 2026-10-24

Prepared by `/root/go_native_window_prepare_1024` for the coordinator. This is
source preparation only. No grant is requested, accepted, reserved or inferred.
Go236 remains RELEASED (original global seq287, reconfirmed414). Historical
native85731 exit1, SDK21711 exit0, and final SDK70405 / shell PID64664 exit0 are
preserved. No new Go/gofmt/SDK/Dart/Flutter/test/analyze/build/WSL/device process,
runner import, runner invocation, Windows API self-control, kill or reset was
performed in this work.

## Changed files and identities

- `fixtures/run_native_window.py` — standalone Windows/Python 3.11+ wrapper using
  the standard library and the repository's existing native hash function.
  SHA-256: `9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8`.
- `fixtures/native-window-controls.example.args` — explicit control-mode
  argument file with rejected grant/owner placeholders. SHA-256:
  `ea45dbe796c5e9d0a704f4d4fc5627444a8cb2e5725e630b58063cc73da9af5c`.
- `fixtures/native-window-checks.example.args` — explicit 36-path native
  argument file, linked to a controls report. SHA-256:
  `bb97bdcc3c8d8b48a32be3c0eec5addca2501c1f61bcdbac6a0fc9d981ecf131`.
- This handoff. Native, product, shared-core, test, spec and sibling files were
  not modified by this worker. Existing fixture files were preserved.

The Windows Job implementation was adapted by reading, without executing or
modifying, `D:/MyNewProjects/qfli_note/build/note-audit/run_host_window.py`.
Its observed SHA-256 is
`a4515f877e739cb459a158498f51c04e9ac062a1f95b8d8295975fc8db1cd642`.
Compiler/environment setup follows `tool/build_desktop_go_runtime.ps1` and
`native/go_runtime/windows-cc.cmd`. The actual hash implementation is reused
from `tool/go_curriculum/audit_native.py:native_source_hash`; the wrapper also
cross-checks that hash against its captured native-file inventory.

## Execution and containment contract

Import has no filesystem writes, process launches or Windows API calls. CLI
execution requires nonempty `--grant`, `--next-owner`, an explicit repeated
`--owned-go` list, matching `--controls-report`, and a new `--output` directory
outside native sources. Control-only mode requires no formatting paths. The
historical exact grant name `Go236` and `REPLACE_` grant/owner placeholders are
rejected. The CLI does not authenticate a
grant against the channel: the coordinator must already have a NEW named grant.

Only supplied existing native `.go` paths may be formatted. Parent traversal,
path-component reparse points and files with multiple hard links are rejected.
The actual paths are rechecked immediately before/after formatting and recorded
as `actualFrozenOwnedPaths`. No broad vendor walk chooses formatting ownership.
The pre-format native inventory and exact owned-file backup bytes are retained;
actual changed paths must be a subset of the explicit list. A concurrent path
replacement between checks cannot be prevented by these source checks; the
coordinator must arrange source ownership for the granted run.

Each phase gets a private non-breakaway Windows Job with kill-on-close enabled.
Its exact root is created suspended, identified by HANDLE/PID/creation FILETIME,
assigned to the Job, and only then resumed. Assignment/start failure retains the
same exact owned root handle. Cleanup terminates only this private Job or an
exact never-resumed owned root whose assignment failed. There is no foreign PID
enumeration, OpenProcess lookup, taskkill or global process reset.

Each phase records the exact decimal/hex HANDLE, PID, creation FILETIME, command,
cwd, terminal status, exit, elapsed time and Job active count. Report-level
`wrapperPid` identifies the process in which those HANDLE values are valid.
`--outer-handle` can record the launching tool/session identity if known. The
actual minimal process-local Windows/offline/memory environment is fully
recorded; inherited secrets are not copied into the child environment. Machine
environment and machine PATH are unchanged. Pinned Go/gofmt, SDK helper
executables, Clang-directory executables, cmd.exe, compiler adapter, Python and
hash-helper identities are captured before/after; any drift invalidates a pass.
This is not a complete SDK/sysroot/package provenance manifest.

The plan is 128 seconds for new work, a cleanup observation deadline no later
than 140 seconds from wrapper start, then evidence within a 150-second plan.
After preflight, serial phases are:

1. Explicit-list `gofmt -w`, up to 15 seconds; freeze the actual native hash
   **after** permitted formatting. At least 95 work seconds must remain before
   the full test command can start.
2. `go -C native/go_runtime test -mod=vendor -count=1 -timeout=90s -v ./...`.
   The root/descendant bound also covers compile time and subprocess fixtures.
3. `go -C native/go_runtime vet -mod=vendor ./...` only if the full tests passed
   and at least 15 actual work seconds remain. Otherwise vet is explicitly
   UNRUN. A full pass requires vet too.

Every phase captures independent raw binary stdout/stderr. Failures, timeouts
and cleanup errors remain in the report. Verbose `--- SKIP:` lines are retained
and force `PASS_REQUIRES_SKIP_REVIEW` rather than an unconditional pass; Windows
symlink skips leave real symlink acceptance open. No test filter is used.

The source reviewer identified and this worker repaired an early draft that
would close unconfirmed handles at the observation deadline. The revised
`drain_owned_job` keeps the **same wrapper, root HANDLE and Job HANDLE live**,
starts no later phase, writes HOLD evidence, and continues observing those same
handles until terminal **and** zero active Job processes are authoritative.
Transient observation errors and soft interrupts retain the handles and retry;
failed owned termination requests retry. Only confirmed termination (or no root
ever created) permits handle closure. A HOLD update is written every five
seconds after the observation deadline. The parent must retain/poll the same
outer tool handle and promptly publish HOLD/overrun, rather than time out or
reset the wrapper. An unconfirmed run has no RELEASE.

OS scheduling and cleanup are not realtime. The wrapper may remain live beyond
150 seconds while holding exact handles. It reports observed elapsed time and
whether the evidence/release-decision point was within150; the outer tool must
also record the wrapper's actual terminal elapsed time. Hard external
termination can close OS handles but cannot manufacture terminal/empty evidence;
the last durable HOLD remains authoritative until the coordinator verifies it.

`report.json` and `release-message.md` are written in the new output directory.
The wrapper does not publish channel messages: publication is explicitly
NOT_ATTEMPTED, so the parent must publish the exact evidence promptly. Release
and test success are separate: failed checks can release after all owned work
really drains. No native build, corpus/SDK/Flutter, Linux race, WSL, target,
five-ABI, DLL/FFI or HAP/signature gate is implied or closed.

## First-grant controls and invocation template — DO NOT RUN NOW

The runner and **Win32 containment controls are UNRUN**. Before treating the
runner as proven, a NEW explicitly authorized window must first execute
`--control-only`. It shares the exact same OwnedJob, run_phase and drain path:

- A real Python root must be created suspended, assigned before resume, exit0,
  and leave zero Job processes, with exact handle/PID/FILETIME evidence.
- A real Python root launches a Python child held for60s and exits0. The wrapper
  must observe root terminal/exit0 **while Job active count remains positive**,
  record that snapshot and reject the release gate. Only its own Job is then
  terminated; terminal plus zero active processes must be observed before
  closing either exact owned handle.

Controls have a10s work deadline, cleanup observation deadline13s, and15s total
plan. HOLD retains the same exact handles and may exceed that plan. Native
execution requires the matching same-grant PASS controls report with both
confirmed drains, the root-exit/child-live negative observation, and unchanged
runner/Python executable identities. Any control failure or identity change
blocks native commands. No control is executed merely by preparing/importing
the file.

The intended first request is one NEW named window with an at-most165s plan:
15s controls, then the150s native plan **only if controls pass and the actual
granted budget remains**. No request was sent by this worker. The coordinator
must poll the same launching tool handle, inspect exact control evidence,
account for actual elapsed time between invocations, and publish HOLD/overrun
if cleanup is unconfirmed. A control report's RELEASE is explicitly scoped to
its control-owned processes; it does not hand the global named grant away
between these two authorized phases.

The `.args` files contain one literal argument per line, supported by argparse
`@file` expansion. The native file explicitly lists36 existing owned Go paths
from the source-review handoffs and the current task's scoped tracked/untracked
native source changes. All nine source-review-owned paths are included. The
unchanged SDK-proof-only `stdlib/go1_22_sort.go` and `go1_22_net_rpc.go` are
excluded. No runtime git scan or broad vendor formatting chooses ownership.
The coordinator must review this explicit list for any later ownership changes
before the new grant. Replace the matching grant/owner/evidence placeholders
in both files; do not reuse Go236. From `D:/MyNewProjects/qfli_go`, the future
commands are:

```powershell
python '.trellis/tasks/10-22-go-offline-ide/research/fixtures/run_native_window.py' '@.trellis/tasks/10-22-go-offline-ide/research/fixtures/native-window-controls.example.args'
```

After the **exact controls report passes** and enough authorized budget remains:

```powershell
python '.trellis/tasks/10-22-go-offline-ide/research/fixtures/run_native_window.py' '@.trellis/tasks/10-22-go-offline-ide/research/fixtures/native-window-checks.example.args'
```

## Checks and remaining risks

Python AST parsing, final-newline/trailing-whitespace inspection and manual
containment/partial-start/serial-budget/release-path review: PASS. Static
assertions verified that `run_phase` has no unconditional Job close and that
cleanup retains a continuing observation loop with durable HOLD. These checks
read source only and do not establish Windows API behavior or executable
correctness. The argument inventory has36 distinct existing native Go paths;
the nine review-owned paths are included and the proof-only stdlib sources are
excluded. Runner import, CLI/help, native execution and **Win32 containment
controls: UNRUN**. No tests or native/source acceptance gate was closed here.

The coordinator's independent source review and a later explicitly authorized
execution remain required. Source/tool identity capture adds real I/O overhead
and can consume the available work budget; that produces honest UNRUN/failure,
not a smaller filtered suite or a fabricated pass. Current native repairs and
their source review remain unexecuted since the retained native85731 exit1.
