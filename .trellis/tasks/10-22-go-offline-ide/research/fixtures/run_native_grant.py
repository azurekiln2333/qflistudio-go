"""One future invocation: same-runner controls, then native iff budget remains.

Prepared source only. Import of this module performs no filesystem write, starts
no process and calls no Windows API. Every effect happens inside run().

Why this file exists
--------------------
The C580 window showed the concrete orchestration gap: the controls phase really
PASSed in 0.227s, but the parent model paused 105.262s between two tool calls, so
the budget guard refused to start the native phase. Two separate invocations
cannot guarantee the serial timing. This wrapper performs both phases inside ONE
process: it launches the pinned run_native_window.py controls, inspects the
matching PASS/drain evidence, and immediately launches the native phase only when
the reserve-adjusted deadline for the 150s native plan still fits the single 180s
grant. There is no model pause between the phases because there is no second tool
call.

Non-negotiables (see research/native-window-runner-source-handoff-20261024.md)
------------------------------------------------------------------------------
* The pinned runner stays byte-identical. Its SHA-256 is asserted before and
  after the run; any drift blocks native work and is reported.
* Both children use the SAME python executable, runner path, grant and successor
  owner. run_native_window.py:require_controls compares tool identities, so a
  different interpreter or runner would be rejected by the native phase itself.
* The owned-go list is the explicit 36-path template below. No glob, no git scan
  and no vendor walk picks formatting ownership.
* Output directories are fresh; the runner refuses an existing evidence leaf and
  this wrapper refuses an existing evidence root.
* Timing is monotonic from the first line of run(). The parent records its own
  elapsed seconds and the remaining budget at the native decision point.
* Each child's real PID, process HANDLE decimal/hex, creation FILETIME and exit
  code are recorded. The exact original Popen object is retained until the real
  terminal state; this wrapper never kills, never times out and never restarts.
* A child that publishes HOLD_UNRELEASED is waited on as the SAME child for as
  long as it stays live. Native work never starts while a HOLD is live, and a
  persistent HOLD is reported rather than papered over by a timeout.
* Nothing is published to the channel and no grant is self-issued. The parent
  publishes the exact report after the wrapper terminal. No successor grant
  exists before that terminal and none is implied here.

Windows only, one process at a time, and only under a NEW named grant.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

# Frozen dependency identities. These are asserted, never rewritten.
FROZEN_RUNNER_SHA256 = "9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8"
RUNNER_NAME = "run_native_window.py"

# One grant, one process. The 180s named grant must cover every observable cost:
# the pre-run() orchestrator startup, the 15s controls plan, the native launch and
# interpreter startup, the full 150s native plan, the parent's post-terminal
# evidence writes, and the coordinator's release/publication window.
TOTAL_GRANT_SECONDS = 180.0
CONTROLS_PLAN_SECONDS = 15.0
NATIVE_PLAN_SECONDS = 150.0
RUN_ENTRY_RESERVE_SECONDS = 1.0
NATIVE_LAUNCH_RESERVE_SECONDS = 1.5
FINAL_EVIDENCE_RESERVE_SECONDS = 2.0
PARENT_RELEASE_RESERVE_SECONDS = 3.0
RESERVE_TOTAL_SECONDS = (RUN_ENTRY_RESERVE_SECONDS + NATIVE_LAUNCH_RESERVE_SECONDS +
                         FINAL_EVIDENCE_RESERVE_SECONDS + PARENT_RELEASE_RESERVE_SECONDS)
# Native may start no later than this outer elapsed time:
# 180 - 1.0 - 1.5 - 150 - 2.0 - 3.0 = 22.5s.
NATIVE_DEADLINE_SECONDS = (TOTAL_GRANT_SECONDS - RUN_ENTRY_RESERVE_SECONDS - NATIVE_LAUNCH_RESERVE_SECONDS
                           - NATIVE_PLAN_SECONDS - FINAL_EVIDENCE_RESERVE_SECONDS
                           - PARENT_RELEASE_RESERVE_SECONDS)
# Equivalently, the remaining grant at the decision point:
# 1.0 + 1.5 + 150 + 2.0 + 3.0 = 157.5s.
NATIVE_MIN_REMAINING_SECONDS = NATIVE_PLAN_SECONDS + RESERVE_TOTAL_SECONDS

# Poll cadence for the retained children and the durable HOLD refresh interval.
POLL_SECONDS = 0.25
HOLD_UPDATE_SECONDS = 5.0

# The explicit 36-path native ownership template. Frozen here on purpose: any
# later ownership change is a reviewed edit to this list, not a CLI override.
OWNED_GO_PATHS = (
    "native/go_runtime/code_analysis.go",
    "native/go_runtime/code_analysis_test.go",
    "native/go_runtime/curriculum_compat_test.go",
    "native/go_runtime/debug_bridge.go",
    "native/go_runtime/debugger.go",
    "native/go_runtime/debugger_test.go",
    "native/go_runtime/embedded_helper_lifetime_test.go",
    "native/go_runtime/embedded_helper_test.go",
    "native/go_runtime/embedded_testing.go",
    "native/go_runtime/embedded_testing_test.go",
    "native/go_runtime/entry_environment_test.go",
    "native/go_runtime/execution_lifecycle_test.go",
    "native/go_runtime/ide_bridge.go",
    "native/go_runtime/loop_variables_test.go",
    "native/go_runtime/native_callback_provenance_test.go",
    "native/go_runtime/native_method_values_test.go",
    "native/go_runtime/project_environment.go",
    "native/go_runtime/project_environment_test.go",
    "native/go_runtime/project_symlinks.go",
    "native/go_runtime/project_symlinks_test.go",
    "native/go_runtime/runtime.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/ast.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/cfg.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/debugger.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/generic.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/interp.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/qfli_callsite.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/qfli_equal.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/qfli_errors.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/qfli_execution.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/qfli_format.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/qfli_native_values.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/qfli_test_context.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/run.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/type.go",
    "native/go_runtime/vendor/github.com/traefik/yaegi/interp/value.go",
)
EXPECTED_OWNED_COUNT = 36

# Grants that were already consumed. Replay is refused before any directory or
# process is created. Go236/Go509 were never replayed and never will be here.
HISTORICAL_GRANT_EXACT = frozenset({
    "go236",
    "c580-go180-20261025",
    "go509",
})
HISTORICAL_GRANT_PREFIXES = ("c580", "go236", "go509", "replace_")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def identities(paths):
    result = {}
    for path in sorted(set(Path(item) for item in paths)):
        if not path.is_file():
            raise ValueError(f"Required identity file is missing: {path}")
        result[str(path)] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    return result


def changed_paths(before, after):
    return sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))


def save_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read_json(path):
    """Read a child's durable evidence; a torn/absent file is simply not evidence."""
    try:
        return json.loads(Path(path).read_bytes())
    except (OSError, ValueError):
        return None


def refusal_reason(grant, next_owner):
    """Refuse consumed grants and unfilled placeholders before any side effect."""
    folded = grant.strip().casefold()
    owner = next_owner.strip()
    if not folded:
        return "A NEW nonempty named grant is required"
    if folded in HISTORICAL_GRANT_EXACT or folded.startswith(HISTORICAL_GRANT_PREFIXES):
        return f"Grant {grant!r} is historical and consumed; request a NEW named grant"
    if "go236" in folded or "go509" in folded:
        return f"Grant {grant!r} names a historical window; request a NEW named grant"
    if not owner:
        return "An explicit successor owner is required"
    if owner.casefold().startswith("replace_"):
        return "The successor owner placeholder was not replaced"
    return None


def creation_filetime(handle_value):
    """Creation FILETIME of the real child, read from the retained Popen handle."""
    if handle_value is None:
        return None, "no process handle was exposed by Popen"
    try:
        import ctypes as C
        from ctypes import wintypes as W
        kernel32 = C.WinDLL("kernel32", use_last_error=True)
        get_times = kernel32.GetProcessTimes
        get_times.argtypes = [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4
        get_times.restype = W.BOOL
        stamps = [W.FILETIME() for _ in range(4)]
        if not get_times(W.HANDLE(handle_value), *(C.byref(stamp) for stamp in stamps)):
            return None, f"GetProcessTimes failed: {C.get_last_error()}"
        return str((stamps[0].dwHighDateTime << 32) | stamps[0].dwLowDateTime), None
    except BaseException as error:  # noqa: BLE001 - evidence, never a crash
        return None, f"{type(error).__name__}: {error}"


def launch(argv, root, record, stdout_path, stderr_path):
    """Start one child and immediately capture its exact identity."""
    record["argv"] = [str(item) for item in argv]
    record["launchedAt"] = now_iso()
    record["launchedMonotonic"] = time.monotonic()
    stdout_stream = Path(stdout_path).open("wb", buffering=0)
    stderr_stream = Path(stderr_path).open("wb", buffering=0)
    record["stdout"] = str(stdout_path)
    record["stderr"] = str(stderr_path)
    try:
        process = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
            [str(item) for item in argv],
            cwd=str(root),
            stdin=subprocess.DEVNULL,
            stdout=stdout_stream,
            stderr=stderr_stream,
            close_fds=True,
        )
    except BaseException:
        stdout_stream.close()
        stderr_stream.close()
        raise
    record["popenRetained"] = True
    record["pid"] = process.pid
    handle = getattr(process, "_handle", None)
    handle_value = None
    if handle is not None:
        try:
            handle_value = int(handle)
        except (TypeError, ValueError):
            handle_value = None
    record["processHandleDecimal"] = None if handle_value is None else str(handle_value)
    record["processHandleHex"] = None if handle_value is None else hex(handle_value)
    stamp, stamp_error = creation_filetime(handle_value)
    record["creationFiletime100ns"] = stamp
    if stamp_error:
        record.setdefault("errors", []).append(f"Creation FILETIME: {stamp_error}")
    return process, [stdout_stream, stderr_stream]


def child_release_is_hold(evidence):
    """A live HOLD is only what the child's CURRENT evidence says, never a sticky flag."""
    return isinstance(evidence, dict) and evidence.get("release") == "HOLD_UNRELEASED"


def wait_terminal(process, record, child_report_path, report, output, started):
    """Wait for the REAL terminal state. Never kill, never time out, never restart.

    While the child is live, a durable HOLD_UNRELEASED in its own evidence is
    recorded and the same child keeps being observed. The Popen object stays
    referenced for the whole wait, so its process HANDLE is never re-looked-up.
    """
    next_hold_update = 0.0
    while True:
        code = process.poll()
        if code is not None:
            return code
        child_evidence = read_json(child_report_path)
        if child_release_is_hold(child_evidence):
            # Historical diagnostic only. The child's FINAL release is authoritative.
            record["childHoldObserved"] = True
            record["childHoldSnapshot"] = {
                key: child_evidence.get(key)
                for key in ("release", "result", "elapsedSeconds", "withinPlanSeconds", "errors")
            }
        current = time.monotonic()
        if current >= next_hold_update:
            report["parentElapsedSeconds"] = round(current - started, 3)
            report["persistentHold"] = child_release_is_hold(child_evidence)
            try:
                save_json(Path(output) / "report.json", report)
            except BaseException as error:  # noqa: BLE001 - keep observing the child
                record.setdefault("errors", []).append(f"Parent HOLD evidence write: {error}")
            next_hold_update = current + HOLD_UPDATE_SECONDS
        time.sleep(POLL_SECONDS)


def control_verdict(evidence, exit_code, grant, runner, python_executable):
    """Mirror the native phase's own acceptance of a matching controls report."""
    problems = []
    if not isinstance(evidence, dict):
        return False, ["The controls report is missing or unreadable"]
    if exit_code != 0:
        problems.append(f"the wrapper observed child exit {exit_code}, expected 0")
    if evidence.get("mode") != "CONTROL_ONLY":
        problems.append(f"mode is {evidence.get('mode')!r}, expected CONTROL_ONLY")
    if evidence.get("result") != "PASS":
        problems.append(f"result is {evidence.get('result')!r}, expected PASS")
    if evidence.get("grant") != grant:
        problems.append(f"grant {evidence.get('grant')!r} does not match {grant!r}")
    if evidence.get("release") != "RELEASE":
        problems.append(f"release is {evidence.get('release')!r}, expected RELEASE")
    if evidence.get("withinPlanSeconds") is not True:
        problems.append("the controls plan was exceeded")
    if evidence.get("toolDrift"):
        problems.append(f"control tool identities drifted: {evidence.get('toolDrift')}")
    phases = evidence.get("phases") or []
    if len(phases) != 2:
        problems.append(f"{len(phases)} control phases ran, expected 2")
    for phase in phases:
        name = phase.get("name")
        if not (phase.get("passed") and phase.get("cleanupConfirmed")):
            problems.append(f"{name}: not passed/drained")
        process = phase.get("process") or {}
        if not process.get("terminal"):
            problems.append(f"{name}: root is not terminal")
        if process.get("exitCode") != 0:
            problems.append(f"{name}: exit {process.get('exitCode')} is not 0")
        if process.get("jobActiveProcesses") != 0:
            problems.append(f"{name}: job active processes {process.get('jobActiveProcesses')} is not 0")
        for field in ("createdSuspended", "assignedBeforeResume", "resumed"):
            if not process.get(field):
                problems.append(f"{name}: {field} is unproven")
    if len(phases) == 2:
        negative = phases[1]
        snapshot = negative.get("rootTerminalWithHeldChild") or {}
        if not negative.get("negativeReleaseGateRejected"):
            problems.append("the root-exit/child-live negative release gate was not observed")
        if not snapshot.get("terminal") or snapshot.get("exitCode") != 0:
            problems.append("the negative control did not observe a terminal exit0 root")
        if (snapshot.get("jobActiveProcesses") or 0) <= 0:
            problems.append("the negative control did not observe a live held child")
    try:
        current = identities([runner, python_executable])
    except ValueError as error:
        problems.append(str(error))
        current = None
    if current is not None and evidence.get("toolIdentitiesAfter") != current:
        problems.append("control runner/Python identity differs from this invocation")
    return (not problems), problems


def native_verdict(evidence, exit_code, grant, next_owner, controls_sha256):
    """Strict acceptance of the native phase. Skips are never promoted to PASS.

    Returns (passed, state, problems). state is PASS, PASS_REQUIRES_SKIP_REVIEW,
    HOLD_UNRELEASED or FAIL_OR_INCONCLUSIVE. The native phase's own tool set is the
    SDK tool set, which this wrapper cannot reproduce, so tool identity is judged by
    the frozen runner's toolDrift plus a present toolIdentitiesAfter.
    """
    if not isinstance(evidence, dict):
        return False, "FAIL_OR_INCONCLUSIVE", ["The native report is missing or unreadable"]
    problems = []
    observed = evidence.get("result")
    observed_hold = observed == "HOLD_UNRELEASED" or evidence.get("release") == "HOLD_UNRELEASED"
    if observed != "PASS":
        problems.append(f"observed result is {observed!r}, expected exact PASS")
    if exit_code != 0:
        problems.append(f"the wrapper observed child exit {exit_code}, expected 0")
    if evidence.get("mode") != "NATIVE":
        problems.append(f"mode is {evidence.get('mode')!r}, expected NATIVE")
    if evidence.get("grant") != grant:
        problems.append(f"grant {evidence.get('grant')!r} does not match {grant!r}")
    if evidence.get("nextOwner") != next_owner:
        problems.append(f"next owner {evidence.get('nextOwner')!r} does not match {next_owner!r}")
    if evidence.get("release") != "RELEASE":
        problems.append(f"release is {evidence.get('release')!r}, expected RELEASE")
    if evidence.get("within150Seconds") is not True:
        problems.append("the native 150s plan was exceeded")
    if evidence.get("withinPlanSeconds") is not True:
        problems.append("the native plan was exceeded")
    vet = evidence.get("vet") or {}
    if vet.get("state") != "PASS":
        problems.append(f"vet state is {vet.get('state')!r}, expected PASS")
    if evidence.get("skipReview") != "No verbose SKIP lines observed":
        problems.append(f"skip review is {evidence.get('skipReview')!r}")
    if evidence.get("testSkips"):
        problems.append(f"{len(evidence['testSkips'])} skipped test line(s) remain")
    phases = evidence.get("phases")
    if not isinstance(phases, list):
        problems.append("the native report phases are not a list")
        phases = []
    if len(phases) != 3:
        problems.append(f"{len(phases)} native phases ran, expected 3")
    for phase in phases:
        name = phase.get("name")
        if not phase.get("passed"):
            problems.append(f"{name}: not passed")
        if not phase.get("cleanupConfirmed"):
            problems.append(f"{name}: drain not confirmed")
        if phase.get("timedOut"):
            problems.append(f"{name}: timed out")
        if phase.get("errors"):
            problems.append(f"{name}: {len(phase['errors'])} phase error(s)")
        process = phase.get("process") or {}
        if not process.get("terminal"):
            problems.append(f"{name}: root is not terminal")
        if process.get("exitCode") != 0:
            problems.append(f"{name}: exit {process.get('exitCode')} is not 0")
        if process.get("jobActiveProcesses") != 0:
            problems.append(f"{name}: job active processes {process.get('jobActiveProcesses')} is not 0")
        for field in ("createdSuspended", "assignedBeforeResume", "resumed"):
            if not process.get(field):
                problems.append(f"{name}: {field} is unproven")
    if evidence.get("errors"):
        problems.append(f"{len(evidence['errors'])} native report error(s)")
    if evidence.get("toolDrift"):
        problems.append(f"native tool identities drifted: {evidence.get('toolDrift')}")
    if not evidence.get("toolIdentitiesAfter"):
        problems.append("the native report has no toolIdentitiesAfter")
    if evidence.get("sourceDrift"):
        problems.append(f"native source drift: {evidence.get('sourceDrift')}")
    if evidence.get("nativeDigestDrift"):
        problems.append("the frozen native digest drifted")
    control_binding = evidence.get("controlsEvidence") or {}
    if controls_sha256 is not None and control_binding.get("sha256") != controls_sha256:
        problems.append("the native phase did not bind to this exact controls evidence")
    if control_binding.get("grant") != grant:
        problems.append("the native phase's bound controls grant does not match")
    if observed_hold and not problems:
        problems.append("the native phase ended in HOLD_UNRELEASED")
    if problems:
        if observed == "PASS_REQUIRES_SKIP_REVIEW":
            return False, "PASS_REQUIRES_SKIP_REVIEW", problems
        if observed_hold:
            return False, "HOLD_UNRELEASED", problems
        return False, "FAIL_OR_INCONCLUSIVE", problems
    return True, "PASS", []


def child_summary(evidence, path):
    """Compact, hash-bound view of one child's own durable report."""
    summary = {"path": str(path), "present": isinstance(evidence, dict)}
    if summary["present"]:
        try:
            summary["sha256"] = sha256_file(path)
        except OSError as error:
            summary["errors"] = [f"{type(error).__name__}: {error}"]
    if isinstance(evidence, dict):
        for key in ("mode", "grant", "nextOwner", "release", "result", "planSeconds",
                    "workSeconds", "elapsedSeconds", "withinPlanSeconds",
                    "within150Seconds", "frozenNativeSourceSha256", "skipReview", "errors"):
            if key in evidence:
                summary[key] = evidence[key]
        vet = evidence.get("vet")
        if isinstance(vet, dict):
            summary["vet"] = vet.get("state")
        summary["phaseNames"] = [phase.get("name") for phase in evidence.get("phases") or []]
    return summary


def run(args):
    started = time.monotonic()
    root = args.root.resolve(strict=True)
    runner = args.runner.resolve(strict=True)
    output = args.output.resolve()
    controls_out = output / "controls"
    native_out = output / "native"
    python_executable = Path(sys.executable).resolve()
    report = {
        "schemaVersion": 1,
        "mode": "GRANT_ORCHESTRATION",
        "grant": args.grant.strip(),
        "nextOwner": args.next_owner.strip(),
        "parentPid": os.getpid(),
        "startedAt": now_iso(),
        "startedMonotonic": started,
        "root": str(root),
        "totalGrantSeconds": TOTAL_GRANT_SECONDS,
        "controlsPlanSeconds": CONTROLS_PLAN_SECONDS,
        "clockScope": {
            "startScope": "wrapper run entry: the first line of run()",
            "startExcludes": ["outer tool ACK", "interpreter startup before run()", "argparse"],
            "endScope": "the final durable report write",
            "ackToTerminal": "UNMEASURED",
            "parentPublication": "PENDING",
            "authority": "Coordinator actual event timestamps remain authoritative",
        },
        "parentPublication": {
            "state": "UNMEASURED",
            "pending": True,
            "reason": "This wrapper never publishes; the parent publishes after the wrapper terminal",
            "authority": "Coordinator actual event timestamps",
        },
        "reserveAccounting": {
            "nativePlanSeconds": NATIVE_PLAN_SECONDS,
            "runEntryReserveSeconds": RUN_ENTRY_RESERVE_SECONDS,
            "nativeLaunchReserveSeconds": NATIVE_LAUNCH_RESERVE_SECONDS,
            "finalEvidenceReserveSeconds": FINAL_EVIDENCE_RESERVE_SECONDS,
            "parentReleaseReserveSeconds": PARENT_RELEASE_RESERVE_SECONDS,
            "reserveTotalSeconds": RESERVE_TOTAL_SECONDS,
            "nativeDeadlineSeconds": NATIVE_DEADLINE_SECONDS,
            "nativeMinRemainingSeconds": NATIVE_MIN_REMAINING_SECONDS,
        },
        "publication": {
            "state": "NOT_ATTEMPTED",
            "reason": "This wrapper does not publish to the channel; the parent publishes the exact report",
        },
        "successorGrant": {
            "state": "NOT_GRANTED",
            "nextOwner": args.next_owner.strip(),
            "reason": "No successor grant is issued before the wrapper terminal; the parent publishes after it",
        },
        "phases": [],
        "ownedGoPaths": list(OWNED_GO_PATHS),
        "ownedGoCount": len(OWNED_GO_PATHS),
        "errors": [],
        "budget": {},
        "nativePhase": {"state": "NOT_STARTED"},
        "result": "IN_PROGRESS",
    }
    before = None
    records = []
    controls = None
    controls_passed = False

    # Phase 1: controls through the pinned runner, same python, same grant.
    try:
        if len(OWNED_GO_PATHS) != EXPECTED_OWNED_COUNT or len(set(OWNED_GO_PATHS)) != EXPECTED_OWNED_COUNT:
            raise RuntimeError(f"The owned-go template must hold {EXPECTED_OWNED_COUNT} distinct paths")
        runner_sha = sha256_file(runner)
        report["runner"] = {"path": str(runner), "expectedSha256": FROZEN_RUNNER_SHA256,
                            "actualSha256": runner_sha, "frozenIntact": runner_sha == FROZEN_RUNNER_SHA256}
        report["python"] = {"path": str(python_executable), "sha256": sha256_file(python_executable)}
        report["orchestrator"] = {"path": str(Path(__file__).resolve()),
                                  "sha256": sha256_file(Path(__file__).resolve())}
        if runner_sha != FROZEN_RUNNER_SHA256:
            raise RuntimeError("The pinned runner bytes changed; the frozen runner must stay unchanged")
        if output.exists():
            raise RuntimeError("The evidence directory must be fresh; it already exists")
        output.mkdir(parents=True, exist_ok=False)
        before = identities([runner, python_executable, Path(__file__).resolve()])
        controls = {"phase": "controls", "outputDir": str(controls_out), "errors": []}
        report["phases"].append(controls)
        controls_argv = [sys.executable, runner, "--control-only",
                         "--grant", report["grant"], "--next-owner", report["nextOwner"],
                         "--root", root, "--output", controls_out]
        save_json(output / "report.json", report)
        process, streams = launch(controls_argv, root, controls,
                                  output / "controls.wrapper.stdout.bin",
                                  output / "controls.wrapper.stderr.bin")
        records.append(process)
        controls_report_path = controls_out / "report.json"
        try:
            controls["exitCode"] = wait_terminal(process, controls, controls_report_path, report, output, started)
        finally:
            for stream in streams:
                stream.close()
            controls["terminal"] = process.poll() is not None
            controls["elapsedSeconds"] = round(time.monotonic() - controls["launchedMonotonic"], 3)
            controls["parentElapsedSeconds"] = round(time.monotonic() - started, 3)
        controls_evidence = read_json(controls_report_path)
        controls["childReport"] = child_summary(controls_evidence, controls_report_path)
        controls_passed, controls_problems = control_verdict(
            controls_evidence, controls.get("exitCode"), report["grant"], runner, python_executable)
        controls["verdict"] = {"passed": controls_passed, "problems": controls_problems}
        save_json(output / "report.json", report)
    except BaseException as error:
        report["errors"].append(f"{type(error).__name__}: {error}")
        controls_passed = False

    # Phase 2: native, immediately and only if the controls really passed and the
    # remaining part of THIS grant can still cover the 150s native plan.
    try:
        elapsed = time.monotonic() - started
        remaining = TOTAL_GRANT_SECONDS - elapsed
        report["budget"] = {
            "elapsedAtNativeDecisionSeconds": round(elapsed, 3),
            "remainingAtNativeDecisionSeconds": round(remaining, 3),
            "nativeDeadlineSeconds": NATIVE_DEADLINE_SECONDS,
            "nativeMinRemainingSeconds": NATIVE_MIN_REMAINING_SECONDS,
            "reserveTotalSeconds": RESERVE_TOTAL_SECONDS,
            "deadlineExceeded": elapsed > NATIVE_DEADLINE_SECONDS,
        }
        if controls is not None:
            controls["deadlineExceeded"] = elapsed > NATIVE_DEADLINE_SECONDS
        # A live control HOLD never reaches this branch: wait_terminal blocks until
        # the child is really terminal, so a HOLD shows up as BLOCKED_CONTROLS with
        # its final release. No native work may start either way.
        if controls is None or not controls_passed:
            report["nativePhase"] = {
                "state": "BLOCKED_CONTROLS",
                "reason": "Matching same-grant controls did not PASS and drain",
                "controlsFinalRelease": ((controls or {}).get("childReport") or {}).get("release"),
            }
        elif remaining < NATIVE_MIN_REMAINING_SECONDS:
            report["nativePhase"] = {
                "state": "UNRUN_BUDGET_GUARD",
                "reason": "The 150s native plan plus reserves no longer fit the 180s grant",
                "remainingSeconds": round(remaining, 3),
                "nativeMinRemainingSeconds": NATIVE_MIN_REMAINING_SECONDS,
                "nativeDeadlineSeconds": NATIVE_DEADLINE_SECONDS,
            }
        else:
            native = {"phase": "native", "outputDir": str(native_out), "errors": []}
            report["phases"].append(native)
            report["nativePhase"] = {"state": "STARTED", "remainingSecondsAtStart": round(remaining, 3)}
            native_argv = [sys.executable, runner,
                           "--grant", report["grant"], "--next-owner", report["nextOwner"],
                           "--controls-report", str(Path(controls["outputDir"]) / "report.json"),
                           "--root", root, "--output", native_out]
            for owned in OWNED_GO_PATHS:
                native_argv.extend(["--owned-go", owned])
            process, streams = launch(native_argv, root, native,
                                      output / "native.wrapper.stdout.bin",
                                      output / "native.wrapper.stderr.bin")
            records.append(process)
            native_report_path = native_out / "report.json"
            try:
                native["exitCode"] = wait_terminal(process, native, native_report_path, report, output, started)
            finally:
                for stream in streams:
                    stream.close()
                native["terminal"] = process.poll() is not None
                native["elapsedSeconds"] = round(time.monotonic() - native["launchedMonotonic"], 3)
                native["parentElapsedSeconds"] = round(time.monotonic() - started, 3)
            native_evidence = read_json(native_report_path)
            native["childReport"] = child_summary(native_evidence, native_report_path)
            controls_evidence_path = Path(controls["outputDir"]) / "report.json"
            try:
                controls_sha = sha256_file(controls_evidence_path)
            except OSError:
                controls_sha = None
            native_passed_now, native_verdict_state, native_problems = native_verdict(
                native_evidence, native.get("exitCode"), report["grant"],
                report["nextOwner"], controls_sha)
            native["verdict"] = {
                "passed": native_passed_now,
                "state": native_verdict_state,
                "problems": native_problems,
                "observedResult": (native_evidence or {}).get("result"),
                "release": (native_evidence or {}).get("release"),
            }
            native_release = (native_evidence or {}).get("release")
            report["nativePhase"] = {
                "state": "TERMINAL_HOLD" if native_release == "HOLD_UNRELEASED" else native_verdict_state,
                "result": native_verdict_state,
                "release": native_release,
            }
            if native_release == "HOLD_UNRELEASED":
                report["nativePhase"]["reason"] = (
                    "The native child ended in HOLD_UNRELEASED; never treated as released")
            elif native_verdict_state == "PASS_REQUIRES_SKIP_REVIEW":
                report["nativePhase"]["reason"] = (
                    "The native run passed but reported test SKIP lines; strict policy keeps it non-PASS")
    except BaseException as error:
        report["errors"].append(f"{type(error).__name__}: {error}")

    # Exact, post-terminal bookkeeping. No successor grant is created here.
    try:
        if before is not None:
            after = identities([runner, python_executable, Path(__file__).resolve()])
            report["toolIdentitiesAfter"] = after
            report["toolDrift"] = changed_paths(before, after)
        else:
            report["toolDrift"] = None
    except BaseException as error:
        report["errors"].append(f"Final identity capture: {type(error).__name__}: {error}")
    native_state = report["nativePhase"].get("state")
    native_passed = report["nativePhase"].get("result") == "PASS"
    # Final authority is each phase's own FINAL release, never a transient observation.
    report["persistentHold"] = any(
        (phase.get("childReport") or {}).get("release") == "HOLD_UNRELEASED"
        for phase in report["phases"])
    report["finishedAt"] = now_iso()
    elapsed = time.monotonic() - started
    report["parentElapsedSeconds"] = round(elapsed, 3)
    report["withinGrantSeconds"] = elapsed <= TOTAL_GRANT_SECONDS
    report["withinGrantScope"] = (
        "measured from the wrapper run entry to the final durable write; "
        "outer ACK-to-terminal and parent publication are UNMEASURED")
    report["parentOverrunSeconds"] = round(max(0.0, elapsed - TOTAL_GRANT_SECONDS), 3)
    report["successorGrant"] = {
        "state": "NOT_GRANTED",
        "nextOwner": report["nextOwner"],
        "reason": "No successor grant is issued before the wrapper terminal; the parent publishes after it",
        "wrapperTerminal": bool(report["phases"]) and all(
            phase.get("terminal") for phase in report["phases"]),
    }

    # Durable evidence ordering: write the message first (a fact already known),
    # then the final report LAST. The report never claims its own write succeeded;
    # its presence with the final result is the attestation, and the exit code
    # confirms it. Publication still belongs to the parent after this terminal.
    report["finalEvidence"] = {"messageWritten": False}

    def core_blockers():
        items = []
        if not controls_passed:
            items.append("controls did not PASS and drain")
        if not native_passed:
            items.append(f"native phase {native_state} did not PASS")
        if report.get("toolDrift"):
            items.append(f"tool identity drift: {report['toolDrift']}")
        if report["errors"]:
            items.append(f"{len(report['errors'])} recorded error(s)")
        if report["persistentHold"]:
            items.append("a persistent HOLD was observed")
        if not report["withinGrantSeconds"]:
            items.append(
                f"the wrapper exceeded the {TOTAL_GRANT_SECONDS}s grant by "
                f"{report['parentOverrunSeconds']}s")
        return items

    def write_message():
        """Render from the current report and write it. Returns (text, ok)."""
        try:
            text = render_message(report, controls_passed, native_state)
            (Path(output) / "release-message.md").write_text(text, encoding="utf-8")
            return text, True
        except BaseException as error:
            report["errors"].append(f"Message write: {type(error).__name__}: {error}")
            return None, False

    report["failureReasons"] = core_blockers()
    report["result"] = "PASS" if not report["failureReasons"] else "FAIL_OR_INCONCLUSIVE"
    message, message_ok = write_message()
    if not message_ok:
        # The durable message could not be written: force a non-PASS verdict and
        # retry once so any durable message cannot claim PASS.
        report["result"] = "FAIL_OR_INCONCLUSIVE"
        report["failureReasons"] = core_blockers()
        message, message_ok = write_message()
    elapsed_final = time.monotonic() - started
    report["parentElapsedSeconds"] = round(elapsed_final, 3)
    if elapsed_final > TOTAL_GRANT_SECONDS:
        report["withinGrantSeconds"] = False
        report["parentOverrunSeconds"] = round(elapsed_final - TOTAL_GRANT_SECONDS, 3)
        if report["result"] == "PASS":
            report["result"] = "FAIL_OR_INCONCLUSIVE"
            report["failureReasons"] = core_blockers()
            message, retry_ok = write_message()
            message_ok = message_ok and retry_ok
    report["failureReasons"] = core_blockers()
    if report["failureReasons"]:
        report["result"] = "FAIL_OR_INCONCLUSIVE"
    report["finalEvidence"] = {"messageWritten": message_ok}

    def force_failure(reason):
        """Best-effort durable FAIL so an earlier PASS never stays authoritative."""
        report["result"] = "FAIL_OR_INCONCLUSIVE"
        report["failureReasons"] = core_blockers() + [reason]
        report["finalEvidence"] = {"messageWritten": False}
        try:
            text = render_message(report, controls_passed, native_state)
            (Path(output) / "release-message.md").write_text(text, encoding="utf-8")
            report["finalEvidence"]["messageWritten"] = True
        except BaseException as error:
            report["errors"].append(f"Failure message write: {type(error).__name__}: {error}")
        report["failureReasons"] = core_blockers() + [reason]
        try:
            save_json(Path(output) / "report.json", report)
        except BaseException as error:
            report["errors"].append(f"Failure report write: {type(error).__name__}: {error}")
        print(
            f"ORCHESTRATION {report['grant']} result FAIL_OR_INCONCLUSIVE: {reason}",
            flush=True)
        return 1

    final_report_ok = False
    try:
        save_json(Path(output) / "report.json", report)
        final_report_ok = True
    except BaseException as error:
        report["errors"].append(f"Final report write: {type(error).__name__}: {error}")
    if not final_report_ok:
        return force_failure("the final report could not be written; no PASS is claimed")

    # Recheck the clock AFTER the final durable write. A slow write must not let a
    # run that crossed the grant exit 0 or keep a PASS on disk.
    elapsed_after = time.monotonic() - started
    report["parentElapsedAfterWriteSeconds"] = round(elapsed_after, 3)
    report["withinGrantAfterWrite"] = elapsed_after <= TOTAL_GRANT_SECONDS
    if not report["withinGrantAfterWrite"]:
        report["withinGrantSeconds"] = False
        report["parentOverrunSeconds"] = round(elapsed_after - TOTAL_GRANT_SECONDS, 3)
        return force_failure(
            f"the wrapper crossed the {TOTAL_GRANT_SECONDS}s grant during the final durable write "
            f"({report['parentOverrunSeconds']}s over); PASS is withdrawn")

    # Persist the post-write timing so the durable report carries it, then recheck.
    try:
        save_json(Path(output) / "report.json", report)
    except BaseException as error:
        report["errors"].append(f"Timing report write: {type(error).__name__}: {error}")
        return force_failure("the post-write timing report could not be written")
    elapsed_settled = time.monotonic() - started
    if elapsed_settled > TOTAL_GRANT_SECONDS:
        report["parentElapsedAfterWriteSeconds"] = round(elapsed_settled, 3)
        report["withinGrantAfterWrite"] = False
        report["withinGrantSeconds"] = False
        report["parentOverrunSeconds"] = round(elapsed_settled - TOTAL_GRANT_SECONDS, 3)
        return force_failure(
            f"the wrapper crossed the {TOTAL_GRANT_SECONDS}s grant while settling timing "
            f"({report['parentOverrunSeconds']}s over); PASS is withdrawn")

    if report["result"] == "PASS" and message_ok and message is not None:
        print(message, end="", flush=True)
    else:
        print(
            f"ORCHESTRATION {report['grant']} result {report['result']}; "
            f"message written={message_ok}; failure reasons={report['failureReasons']}.",
            flush=True)
    return 0 if (report["result"] == "PASS" and message_ok and final_report_ok) else 1


def render_message(report, controls_passed, native_state):
    """Exact, parent-publishable text. Explicitly not a successor grant."""
    lines = [
        f"ORCHESTRATION {report['grant']}; requested next owner {report['nextOwner']}.",
        f"Result {report['result']}; controls PASS={controls_passed}; native phase {native_state}.",
        f"Parent elapsed {report['parentElapsedSeconds']}s of {report['totalGrantSeconds']}s; "
        f"withinGrant={report['withinGrantSeconds']}; overrun={report['parentOverrunSeconds']}s.",
        f"Native deadline {NATIVE_DEADLINE_SECONDS}s; reserve {RESERVE_TOTAL_SECONDS}s "
        f"(entry {RUN_ENTRY_RESERVE_SECONDS} + launch {NATIVE_LAUNCH_RESERVE_SECONDS} + "
        f"evidence {FINAL_EVIDENCE_RESERVE_SECONDS} + release {PARENT_RELEASE_RESERVE_SECONDS}).",
        f"Budget scope: {report.get('withinGrantScope')}.",
        f"Parent publication: {report.get('parentPublication', {}).get('state')} "
        f"(pending={report.get('parentPublication', {}).get('pending')}); "
        f"coordinator actual event timestamps are authoritative.",
        f"Frozen runner intact={report.get('runner', {}).get('frozenIntact')}; "
        f"runner sha256={report.get('runner', {}).get('actualSha256')}.",
        f"Owned-go template: {report['ownedGoCount']} explicit paths; tool drift={report.get('toolDrift')}.",
    ]
    for phase in report["phases"]:
        lines.append(
            f"{phase['phase']}: PID={phase.get('pid')}, "
            f"HANDLE={phase.get('processHandleDecimal')} ({phase.get('processHandleHex')}), "
            f"creationFILETIME={phase.get('creationFiletime100ns')}, "
            f"terminal={phase.get('terminal')}, exit={phase.get('exitCode')}, "
            f"elapsed={phase.get('elapsedSeconds')}s, "
            f"holdObserved={phase.get('childHoldObserved', False)}."
        )
        child = phase.get("childReport") or {}
        lines.append(
            f"  {phase['phase']} evidence: release={child.get('release')}, result={child.get('result')}, "
            f"phases={child.get('phaseNames')}, sha256={child.get('sha256')}."
        )
        problems = (phase.get("verdict") or {}).get("problems") or []
        if problems:
            lines.append(f"  {phase['phase']} problems: {' | '.join(problems)}")
    if report["errors"]:
        lines.append(f"Errors: {' | '.join(report['errors'])}")
    reasons = report.get("failureReasons") or []
    if reasons:
        lines.append(f"Failure reasons: {' | '.join(reasons)}")
    lines.append(
        "The final report is written last; its presence with this result is the "
        "attestation, and the parent publishes it after the wrapper terminal."
    )
    lines.extend([
        f"Persistent HOLD observed={report['persistentHold']}; no kill, no timeout, no restart was used.",
        f"Publication {report['publication']['state']}; this wrapper neither publishes nor self-issues grants.",
        f"Successor grant {report['successorGrant']['state']}: {report['successorGrant']['reason']}",
        "The parent must publish this exact report only after the wrapper terminal.",
        "No build, corpus, SDK/Flutter, WSL or device gate is implied or closed by this run.",
    ])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--grant", required=True, help="NEW explicitly authorized named grant")
    parser.add_argument("--next-owner", required=True, help="Exact successor owner to name in evidence")
    parser.add_argument("--output", required=True, type=Path, help="New evidence directory; must not exist")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[5],
                        help="Repository root; defaults to the checkout containing this fixture")
    parser.add_argument("--runner", type=Path,
                        default=Path(__file__).resolve().parent / RUNNER_NAME,
                        help="Pinned run_native_window.py; its frozen SHA-256 is asserted")
    args = parser.parse_args(argv)
    if os.name != "nt":
        parser.error("Windows only")
    reason = refusal_reason(args.grant, args.next_owner)
    if reason:
        parser.error(reason)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
