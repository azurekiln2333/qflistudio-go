"""Prepared Windows native checks; execute only under a NEW named grant.

Native: 128s work + 12s cleanup + 10s evidence, a 150s plan. Controls:
10s work + 3s cleanup + 2s evidence, a 15s plan. Neither is realtime.
Unconfirmed root/job termination always means HOLD with handles retained.
No process, filesystem write, or Windows API call occurs on import.
OwnedJob is adapted from qfli_note/build/note-audit/run_host_window.py.
"""
from __future__ import annotations

import argparse
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time


class Limits(C.Structure):
    _fields_ = [("processTime", C.c_longlong), ("jobTime", C.c_longlong),
                ("flags", W.DWORD), ("minWs", C.c_size_t), ("maxWs", C.c_size_t),
                ("activeLimit", W.DWORD), ("affinity", C.c_size_t),
                ("priority", W.DWORD), ("scheduling", W.DWORD)]


class ExtendedLimits(C.Structure):
    _fields_ = [("basic", Limits), ("io", C.c_ulonglong * 6),
                ("processMemory", C.c_size_t), ("jobMemory", C.c_size_t),
                ("peakProcess", C.c_size_t), ("peakJob", C.c_size_t)]


class Accounting(C.Structure):
    _fields_ = [("times", C.c_longlong * 4), ("faults", W.DWORD),
                ("total", W.DWORD), ("active", W.DWORD), ("terminated", W.DWORD)]


class OwnedJob:
    """One suspended root, assigned before resume; no breakaway or PID lookup."""

    def __init__(self):
        self.k = C.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([C.c_void_p, W.LPCWSTR], W.HANDLE),
            "SetInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
            "QueryInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p], W.BOOL),
            "AssignProcessToJobObject": ([W.HANDLE, W.HANDLE], W.BOOL),
            "TerminateJobObject": ([W.HANDLE, W.UINT], W.BOOL),
            "TerminateProcess": ([W.HANDLE, W.UINT], W.BOOL),
            "ResumeThread": ([W.HANDLE], W.DWORD),
            "CloseHandle": ([W.HANDLE], W.BOOL),
            "WaitForSingleObject": ([W.HANDLE, W.DWORD], W.DWORD),
            "GetExitCodeProcess": ([W.HANDLE, C.POINTER(W.DWORD)], W.BOOL),
            "GetProcessId": ([W.HANDLE], W.DWORD),
            "GetProcessTimes": ([W.HANDLE] + [C.POINTER(W.FILETIME)] * 4, W.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.k, name)
            function.argtypes, function.restype = arguments, result
        self.job = None
        self.process = None
        self.record = {"rootCreated": False, "terminal": True, "exitCode": None,
                       "jobActiveProcesses": None, "assignedBeforeResume": False,
                       "errors": [], "handlesClosed": False}
        self.job = self.k.CreateJobObjectW(None, None)
        self.check(self.job)
        try:
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE; no breakaway flags.
            self.check(self.k.SetInformationJobObject(self.job, 9, C.byref(limits), C.sizeof(limits)))
            self.record["jobHandleDecimal"] = str(self.job)
            self.record["jobHandleHex"] = hex(self.job)
        except BaseException:
            self.k.CloseHandle(self.job)
            self.job = None
            raise

    @staticmethod
    def check(value):
        if not value:
            raise C.WinError(C.get_last_error())

    def start(self, command, directory, environment, stdout, stderr):
        import _winapi
        import msvcrt

        with open(os.devnull, "rb") as null:
            handles = [msvcrt.get_osfhandle(stream.fileno()) for stream in (null, stdout, stderr)]
            previous = [os.get_handle_inheritable(handle) for handle in handles]
            try:
                for handle in handles:
                    os.set_handle_inheritable(handle, True)
                startup = subprocess.STARTUPINFO()
                startup.dwFlags = subprocess.STARTF_USESTDHANDLES
                startup.hStdInput, startup.hStdOutput, startup.hStdError = handles
                startup.lpAttributeList = {"handle_list": list(dict.fromkeys(handles))}
                hp, ht, pid, tid = _winapi.CreateProcess(
                    command[0], subprocess.list2cmdline(command), None, None, True,
                    0x4 | 0x08000000, environment, str(directory), startup,
                )
                # Retain the exact handle immediately, including partial-start failures.
                self.process = hp
                self.record.update(rootCreated=True, processHandleDecimal=str(hp),
                                   processHandleHex=hex(hp), pid=pid, threadId=tid,
                                   createdSuspended=True, terminal=False, createdObservedAt=now())
                try:
                    stamps = [W.FILETIME() for _ in range(4)]
                    self.check(self.k.GetProcessTimes(hp, *(C.byref(stamp) for stamp in stamps)))
                    self.record["creationFiletime100ns"] = str(
                        (stamps[0].dwHighDateTime << 32) | stamps[0].dwLowDateTime)
                    if self.k.GetProcessId(hp) != pid:
                        raise RuntimeError("Exact owned root handle/PID mismatch")
                    self.check(self.k.AssignProcessToJobObject(self.job, hp))
                    self.record["assignedBeforeResume"] = True
                    if self.k.ResumeThread(ht) != 1:
                        raise RuntimeError("Root did not resume from its single creation suspension")
                    self.record["resumed"] = True
                finally:
                    if not self.k.CloseHandle(ht):
                        self.record["errors"].append("Thread CloseHandle failed")
            finally:
                for handle, inherit in zip(handles, previous):
                    try:
                        os.set_handle_inheritable(handle, inherit)
                    except OSError as error:
                        self.record["errors"].append(f"Restore inherited handle flag: {error}")

    def empty(self):
        info = Accounting()
        self.check(self.k.QueryInformationJobObject(self.job, 1, C.byref(info), C.sizeof(info), None))
        self.record["jobActiveProcesses"] = int(info.active)
        terminal = self.process is None
        if self.process is not None:
            status = self.k.WaitForSingleObject(self.process, 0)
            if status not in (0, 258):  # WAIT_OBJECT_0 / WAIT_TIMEOUT
                raise C.WinError(C.get_last_error())
            terminal = status == 0
            if terminal:
                code = W.DWORD()
                self.check(self.k.GetExitCodeProcess(self.process, C.byref(code)))
                self.record["exitCode"] = int(code.value)
        self.record["terminal"] = terminal
        self.record["lastObservedAt"] = now()
        return terminal and info.active == 0

    def stop(self):
        self.record["ownedJobTerminationRequested"] = True
        errors = []
        if not self.k.TerminateJobObject(self.job, 124):
            errors.append(f"TerminateJobObject: {C.get_last_error()}")
        if self.process is not None and not self.record["assignedBeforeResume"]:
            # Assignment failed: this is only our exact never-resumed root handle.
            if not self.k.TerminateProcess(self.process, 124):
                errors.append(f"TerminateProcess owned suspended root: {C.get_last_error()}")
            self.record["unassignedSuspendedRootTerminationRequested"] = True
        if errors:
            raise RuntimeError("; ".join(errors))

    def close(self):
        errors = []
        for handle in (self.process, self.job):
            if handle is not None and not self.k.CloseHandle(handle):
                errors.append(f"CloseHandle failed: {C.get_last_error()}")
        self.process = self.job = None
        self.record["handlesClosed"] = not errors
        self.record["errors"].extend(errors)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def identities(paths):
    result = {}
    for path in sorted(set(paths)):
        if not path.is_file():
            raise ValueError(f"Required identity file is missing: {path}")
        result[str(path)] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return result


def changed(before, after):
    return sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))


def load_audit(root):
    """Reuse the existing hash implementation without running its CLI or tests."""
    directory = root / "tool/go_curriculum"
    spec = importlib.util.spec_from_file_location("_qfli_window_audit_native", directory / "audit_native.py")
    module = importlib.util.module_from_spec(spec)
    previous_path, previous_bytecode = sys.path[:], sys.dont_write_bytecode
    try:
        sys.path.insert(0, str(directory))
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = previous_path
        sys.dont_write_bytecode = previous_bytecode
    if module.NATIVE.resolve() != (root / "native/go_runtime").resolve():
        raise ValueError("Audit module's native root differs from requested root")
    return module


def native_snapshot(audit):
    native = audit.NATIVE
    paths = [path for path in native.rglob("*") if path.is_file() and
             (path.suffix in (".go", ".c", ".h", ".s", ".S", ".syso") or
              path.name in ("go.mod", "go.sum", "modules.txt"))]
    files = identities(paths)
    inventory_digest = audit.digest(audit.json_bytes([
        (Path(name).relative_to(native).as_posix(), value["sha256"])
        for name, value in files.items()
    ]))
    digest = audit.native_source_hash()
    if inventory_digest != digest:
        raise RuntimeError("Native sources changed during identity capture")
    return {"nativeSourceSha256": digest, "files": files}


def owned_paths(root, native, values):
    """Reject links/aliases before permitting gofmt to write an exact path."""
    owned = []
    for value in values:
        if ".." in Path(value).parts:
            raise ValueError(f"Parent traversal is not an owned path: {value}")
        candidate = root / value
        candidate.relative_to(root)
        for part in (candidate, *candidate.parents):
            if part == root:
                break
            attributes = part.lstat().st_file_attributes
            if attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError(f"Owned formatting path traverses a reparse point: {part}")
        path = candidate.resolve(strict=True)
        if not path.is_relative_to(native) or path.suffix != ".go" or not path.is_file():
            raise ValueError(f"Owned path must be an existing native .go file: {value}")
        if path.stat().st_nlink != 1:
            raise ValueError(f"Owned formatting file has multiple hard links: {path}")
        if path not in owned:
            owned.append(path)
    return owned


def setup(root, args):
    native = (root / "native/go_runtime").resolve(strict=True)
    owned = owned_paths(root, native, args.owned_go)
    sdk = (root / "native/build/go-sdk-1.27.1/go").resolve(strict=True)
    clang = args.clang.resolve(strict=True)
    mingw = args.mingw.resolve(strict=True)
    versions = sorted((mingw / "lib/gcc/x86_64-w64-mingw32").iterdir(),
                      key=lambda path: path.name, reverse=True)
    versions = [path for path in versions if path.is_dir()]
    if not versions:
        raise ValueError("No x64 MinGW GCC support directory found")
    # A small explicit environment is fully recorded; no inherited secrets or
    # machine environment/PATH mutations. Preserve standard Windows locations.
    names = ("SystemRoot", "WINDIR", "COMSPEC", "TEMP", "TMP", "USERPROFILE",
             "LOCALAPPDATA", "APPDATA", "PROGRAMDATA", "PATHEXT")
    environment = {name: os.environ[name] for name in names if name in os.environ}
    system = Path(environment["SystemRoot"])
    environment.update({
        "COMSPEC": str(system / "System32/cmd.exe"),
        "PATH": os.pathsep.join(map(str, (sdk / "bin", clang.parent, mingw / "bin", system / "System32", system))),
        "GOMAXPROCS": "2", "GOFLAGS": "-p=1", "GOMEMLIMIT": "512MiB", "GOGC": "20",
        "GOTOOLCHAIN": "local", "GOWORK": "off", "GOENV": "off", "GOPROXY": "off",
        "GOSUMDB": "off", "GO_TELEMETRY_CHILD": "2", "CGO_ENABLED": "1",
        "GOOS": "windows", "GOARCH": "amd64", "GOROOT": str(sdk),
        "CC": str(native / "windows-cc.cmd"), "QFLI_GO_CLANG": str(clang),
        "QFLI_GO_MINGW": str(mingw), "QFLI_GO_MINGW_GCC": str(versions[0]),
    })
    tools = [sdk / "bin/go.exe", sdk / "bin/gofmt.exe", clang,
             system / "System32/cmd.exe", native / "windows-cc.cmd", sdk / "VERSION",
             root / "tool/go_curriculum/audit_native.py", root / "tool/go_curriculum/assemble.py",
             Path(__file__).resolve(), Path(sys.executable).resolve()]
    if args.controls_report is not None:
        tools.append(args.controls_report.resolve(strict=True))
    # Capture the compiler/linker/vet helpers, including additions/removals.
    for directory in (sdk / "bin", sdk / "pkg/tool/windows_amd64", clang.parent):
        tools.extend(directory.glob("*.exe"))
    return owned, sdk, environment, tools


def cleanup_error(phase, label, error):
    message = f"{label}: {type(error).__name__}: {error}"
    phase.setdefault("cleanupErrorCounts", {})[message] = phase.get("cleanupErrorCounts", {}).get(message, 0) + 1
    if message not in phase["errors"]:
        phase["errors"].append(message)


def publish_hold(job, phase, output, report, started):
    report.update(release="HOLD_UNRELEASED", result="HOLD_UNRELEASED",
                  elapsedSeconds=round(time.monotonic() - started, 3), updatedAt=now())
    report["within150Seconds"] = report["elapsedSeconds"] <= 150
    report["withinPlanSeconds"] = report["elapsedSeconds"] <= report["planSeconds"]
    phase["cleanupObservationDeadlineExceeded"] = True
    process = job.record
    text = (f"HOLD_UNRELEASED {report['grant']}; next owner {report['nextOwner']} MUST WAIT.\n"
            f"{phase['name']}: HANDLE={process.get('processHandleDecimal')} "
            f"({process.get('processHandleHex')}), PID={process.get('pid')}, "
            f"creationFILETIME={process.get('creationFiletime100ns')}, "
            f"jobHANDLE={process.get('jobHandleDecimal')} ({process.get('jobHandleHex')}), "
            f"last terminal={process.get('terminal')}, last exit={process.get('exitCode')}, "
            f"last jobActiveProcesses={process.get('jobActiveProcesses')}.\n"
            f"Elapsed={report['elapsedSeconds']}s; plan={report['planSeconds']}s; "
            f"withinPlan={report['withinPlanSeconds']}; within150s={report['within150Seconds']}.\n"
            "Exact handles remain open in this same wrapper. No later phase starts. "
            "Parent must retain/poll the same outer tool handle; no PID re-lookup.\n"
            "Publication NOT_ATTEMPTED; this is durable evidence for the parent.\n")
    save(output / "report.json", report)
    (output / "release-message.md").write_text(text, encoding="utf-8")
    print(text, end="", flush=True)


def drain_owned_job(job, phase, output, report, started):
    """After 140s, retain exact handles and publish HOLD until emptiness is real."""
    if not job.record["rootCreated"]:
        phase["cleanupConfirmed"] = True
        phase["cleanupReason"] = "No root was created; this private Job was never assigned"
        job.close()
        return
    cleanup_seconds = report["cleanupDeadlineSeconds"] - report["workSeconds"]
    deadline = min(started + report["cleanupDeadlineSeconds"], time.monotonic() + cleanup_seconds)
    stop_requested = False
    next_stop_retry = float("inf")
    next_hold_update = deadline
    while True:
        try:
            phase["cleanupConfirmed"] = job.empty()
        except BaseException as error:
            phase["cleanupConfirmed"] = False
            cleanup_error(phase, "Exact-handle cleanup observation", error)
        if phase["cleanupConfirmed"]:
            phase["cleanupConfirmedAt"] = now()
            phase["cleanupConfirmedElapsedSeconds"] = round(time.monotonic() - started, 3)
            # Only an authoritative terminal+empty observation permits closure.
            job.close()
            return
        if not stop_requested or time.monotonic() >= next_stop_retry:
            try:
                job.stop()
                next_stop_retry = float("inf")
            except BaseException as error:
                cleanup_error(phase, "Owned cleanup request", error)
                next_stop_retry = time.monotonic() + 5
            stop_requested = True
        current = time.monotonic()
        if current >= next_hold_update:
            try:
                publish_hold(job, phase, output, report, started)
            except BaseException as error:
                cleanup_error(phase, "HOLD evidence publication", error)
            next_hold_update = current + 5
        try:
            time.sleep(1 if current >= deadline else 0.05)
        except BaseException as error:
            # A soft interrupt must not discard the live owned process/Job handles.
            cleanup_error(phase, "Cleanup observation interrupted; handles retained", error)


def run_phase(name, command, seconds, root, environment, output, report, started,
              expect_held_child=False):
    phase_started = time.monotonic()
    phase = {"name": name, "command": command, "cwd": str(root), "startedAt": now(),
             "budgetSeconds": seconds, "timedOut": False, "errors": [],
             "cleanupConfirmed": False, "stdout": str(output / f"{name}.stdout.bin"),
             "stderr": str(output / f"{name}.stderr.bin")}
    report["phases"].append(phase)
    job = None
    try:
        with Path(phase["stdout"]).open("wb", buffering=0) as stdout, Path(phase["stderr"]).open("wb", buffering=0) as stderr:
            job = OwnedJob()
            phase["process"] = job.record
            job.start(command, root, environment, stdout, stderr)
            save(output / "report.json", report)
            deadline = min(started + report["workSeconds"], phase_started + seconds)
            while True:
                empty = job.empty()
                if expect_held_child and job.record["terminal"] and job.record["jobActiveProcesses"] > 0:
                    phase["rootTerminalWithHeldChild"] = dict(job.record)
                    phase["negativeReleaseGateRejected"] = not empty
                    break
                if empty:
                    if expect_held_child:
                        phase["errors"].append("Negative control never observed a live child after root exit")
                    break
                if time.monotonic() >= deadline:
                    phase["timedOut"] = True
                    break
                time.sleep(0.05)
    except Exception as error:
        phase["errors"].append(f"{type(error).__name__}: {error}")
    finally:
        if job is not None:
            drain_owned_job(job, phase, output, report, started)
        else:
            phase["cleanupConfirmed"] = True  # Constructor failed before any root.
        phase["elapsedSeconds"] = round(time.monotonic() - phase_started, 3)
        process = phase.get("process", {})
        phase["passed"] = bool(process.get("rootCreated") and
                               process.get("createdSuspended") and process.get("assignedBeforeResume") and
                               process.get("resumed") and process.get("creationFiletime100ns") and
                               process.get("terminal") and process.get("exitCode") == 0 and
                               process.get("jobActiveProcesses") == 0 and phase["cleanupConfirmed"] and
                               not phase["timedOut"] and not phase["errors"] and not process.get("errors"))
        if expect_held_child:
            phase["passed"] = bool(phase["passed"] and phase.get("negativeReleaseGateRejected") and
                                   phase.get("rootTerminalWithHeldChild", {}).get("exitCode") == 0)
        save(output / "report.json", report)
    return phase


def run_controls(args):
    """Prepared real-process controls, sharing the exact native ownership path."""
    started = time.monotonic()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    if output.is_relative_to(root / "native/go_runtime"):
        raise ValueError("Control evidence must be outside native sources")
    output.mkdir(parents=True, exist_ok=False)
    report = {"schemaVersion": 1, "mode": "CONTROL_ONLY", "grant": args.grant.strip(),
              "nextOwner": args.next_owner.strip(), "outerToolHandle": args.outer_handle,
              "wrapperPid": os.getpid(), "startedAt": now(), "root": str(root),
              "planSeconds": 15, "workSeconds": 10, "cleanupDeadlineSeconds": 13,
              "phases": [], "errors": [],
              "releaseScope": "CONTROL_PROCESSES_ONLY; parent retains the named grant",
              "publication": {"state": "NOT_ATTEMPTED", "reason": "Parent polls/publishes exact report"}}
    tool_paths = [Path(__file__).resolve(), Path(sys.executable).resolve()]
    before = None
    try:
        names = ("SystemRoot", "WINDIR", "COMSPEC", "TEMP", "TMP", "USERPROFILE",
                 "LOCALAPPDATA", "APPDATA", "PROGRAMDATA", "PATHEXT")
        environment = {name: os.environ[name] for name in names if name in os.environ}
        environment["PATH"] = str(Path(environment["SystemRoot"]) / "System32")
        report["environment"] = environment
        before = identities(tool_paths)
        report["toolIdentitiesBefore"] = before
        normal = run_phase("control-normal", [sys.executable, "-I", "-c",
                           "print('normal suspended/assigned root', flush=True)"],
                           3, root, environment, output, report, started)
        if not normal["passed"]:
            raise RuntimeError("Normal suspended/assigned exact-root control failed; no later phase")
        remaining = started + 10 - time.monotonic()
        if remaining < 3:
            raise RuntimeError("Insufficient remaining negative-control work budget")
        child_code = "import time; print('held child is live', flush=True); time.sleep(60)"
        root_code = ("import os, subprocess, sys; "
                     f"child = subprocess.Popen([sys.executable, '-I', '-c', {child_code!r}]); "
                     "print('owned held child PID=' + str(child.pid), flush=True); os._exit(0)")
        run_phase("control-root-exit-child-live", [sys.executable, "-I", "-c", root_code],
                  min(5, remaining), root, environment, output, report, started,
                  expect_held_child=True)
    except BaseException as error:
        report["errors"].append(f"{type(error).__name__}: {error}")
    finally:
        try:
            after = identities(tool_paths)
            report["toolIdentitiesAfter"] = after
            report["toolDrift"] = changed(before, after) if before is not None else None
        except BaseException as error:
            report["errors"].append(f"Final control identity capture: {type(error).__name__}: {error}")
        released = all(phase["cleanupConfirmed"] for phase in report["phases"])
        report["release"] = "RELEASE" if released else "HOLD_UNRELEASED"
        report["finishedAt"] = now()
        report["elapsedSeconds"] = round(time.monotonic() - started, 3)
        report["withinPlanSeconds"] = report["elapsedSeconds"] <= 15
        report["within150Seconds"] = report["elapsedSeconds"] <= 150
        passed = (released and report["withinPlanSeconds"] and len(report["phases"]) == 2 and
                  all(phase["passed"] for phase in report["phases"]) and
                  not report["errors"] and not report.get("toolDrift"))
        report["result"] = "PASS" if passed else "FAIL_OR_INCONCLUSIVE"
        save(output / "report.json", report)
        lines = [f"{report['release']} CONTROL_ONLY {report['grant']}; "
                 f"control-owned processes drained; requested next owner {report['nextOwner']}.",
                 f"Controls {report['result']}; elapsed={report['elapsedSeconds']}s; "
                 f"within15s={report['withinPlanSeconds']}."]
        for phase in report["phases"]:
            process = phase.get("process", {})
            lines.append(f"{phase['name']}: HANDLE={process.get('processHandleDecimal')} "
                         f"({process.get('processHandleHex')}), PID={process.get('pid')}, "
                         f"creationFILETIME={process.get('creationFiletime100ns')}, "
                         f"terminal={process.get('terminal')}, exit={process.get('exitCode')}, "
                         f"jobActiveProcesses={process.get('jobActiveProcesses')}, "
                         f"cleanupConfirmed={phase['cleanupConfirmed']}, "
                         f"negativeReleaseGateRejected={phase.get('negativeReleaseGateRejected')}.")
        lines.extend(["No Go/gofmt/native command was started by CONTROL_ONLY.",
                      "CONTROL_ONLY release covers its own processes; parent controls the named grant.",
                      "Native checks require controls PASS plus the remaining explicitly granted budget.",
                      "Publication NOT_ATTEMPTED; parent must publish exact evidence."])
        (output / "release-message.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines), flush=True)
    return 0 if passed else 1


def require_controls(args):
    path = args.controls_report.resolve(strict=True)
    evidence_bytes = path.read_bytes()
    evidence = json.loads(evidence_bytes)
    phases = evidence.get("phases", [])
    if (evidence.get("mode") != "CONTROL_ONLY" or evidence.get("result") != "PASS" or
            evidence.get("grant") != args.grant.strip() or evidence.get("release") != "RELEASE" or
            evidence.get("withinPlanSeconds") is not True or len(phases) != 2 or
            not all(phase.get("passed") and phase.get("cleanupConfirmed") for phase in phases)):
        raise ValueError("Matching new-grant controls must PASS and drain before native checks")
    for phase in phases:
        process = phase.get("process", {})
        if (not process.get("terminal") or process.get("exitCode") != 0 or
                process.get("jobActiveProcesses") != 0 or not process.get("createdSuspended") or
                not process.get("assignedBeforeResume") or not process.get("resumed")):
            raise ValueError("Control exact root/Job termination or suspended assignment is unproven")
    negative = phases[1]
    snapshot = negative.get("rootTerminalWithHeldChild", {})
    if (not negative.get("negativeReleaseGateRejected") or not snapshot.get("terminal") or
            snapshot.get("exitCode") != 0 or snapshot.get("jobActiveProcesses", 0) <= 0):
        raise ValueError("Root-exit/child-live negative release control is unproven")
    current = identities([Path(__file__).resolve(), Path(sys.executable).resolve()])
    if evidence.get("toolIdentitiesAfter") != current:
        raise ValueError("Control runner/Python identity differs from the current invocation")
    return {"path": str(path), "sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "grant": evidence["grant"], "elapsedSeconds": evidence["elapsedSeconds"],
            "result": "PASS", "releaseScope": evidence["releaseScope"]}


def run(args):
    started = time.monotonic()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    if output.is_relative_to(root / "native/go_runtime"):
        raise ValueError("Evidence output must be outside native sources")
    output.mkdir(parents=True, exist_ok=False)
    report = {"schemaVersion": 1, "mode": "NATIVE", "grant": args.grant.strip(), "nextOwner": args.next_owner.strip(),
              "outerToolHandle": args.outer_handle, "wrapperPid": os.getpid(),
              "startedAt": now(), "root": str(root),
              "planSeconds": 150, "workSeconds": 128, "cleanupDeadlineSeconds": 140,
              "phases": [], "errors": [], "vet": {"state": "UNRUN"},
              "publication": {"state": "NOT_ATTEMPTED", "reason": "Parent publishes durable release text"}}
    audit = None
    before_tools = None
    frozen = None
    try:
        report["controlsEvidence"] = require_controls(args)
        owned, sdk, environment, _ = setup(root, args)
        audit = load_audit(root)
        report["environment"] = environment
        report["permittedFormatPaths"] = [str(path) for path in owned]
        report["sourceBeforeFormat"] = native_snapshot(audit)
        before_tools = identities(setup(root, args)[3])
        if before_tools[str(args.controls_report.resolve())]["sha256"] != report["controlsEvidence"]["sha256"]:
            raise RuntimeError("Control evidence changed during native preflight")
        report["toolIdentitiesBefore"] = before_tools
        for path in owned:
            backup = output / "before-format" / path.relative_to(root)
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(path.read_bytes())
        save(output / "report.json", report)
        remaining = started + 128 - time.monotonic()
        if remaining < 100:
            raise RuntimeError("Preflight left less than 100s; no formatting/test root started")
        if owned_paths(root, audit.NATIVE, args.owned_go) != owned:
            raise RuntimeError("Owned formatting paths changed before gofmt")
        formatted = run_phase("gofmt", [str(sdk / "bin/gofmt.exe"), "-w", *map(str, owned)],
                              min(15, remaining), root, environment, output, report, started)
        if owned_paths(root, audit.NATIVE, args.owned_go) != owned:
            raise RuntimeError("Owned formatting paths changed during gofmt")
        report["actualFrozenOwnedPaths"] = [str(path) for path in owned]
        frozen = native_snapshot(audit)
        report["sourceAfterFormat"] = frozen
        format_changes = changed(report["sourceBeforeFormat"]["files"], frozen["files"])
        report["formatChangedPaths"] = format_changes
        report["unexpectedFormatChanges"] = sorted(set(format_changes) - set(map(str, owned)))
        if not formatted["passed"] or report["unexpectedFormatChanges"]:
            raise RuntimeError("Formatting did not pass, drain, or stay inside explicit ownership")
        # This exact audit_native hash is frozen AFTER all permitted formatting.
        report["frozenNativeSourceSha256"] = frozen["nativeSourceSha256"]
        remaining = started + 128 - time.monotonic()
        if remaining < 95:
            raise RuntimeError("Insufficient remaining full-suite budget; native tests UNRUN")
        tested = run_phase("test", [str(sdk / "bin/go.exe"), "-C", "native/go_runtime", "test",
                                  "-mod=vendor", "-count=1", "-timeout=90s", "-v", "./..."],
                           remaining, root, environment, output, report, started)
        remaining = started + 128 - time.monotonic()
        if tested["passed"] and remaining >= 15:
            report["vet"] = {"state": "STARTED", "remainingSecondsAtStart": remaining}
            vetted = run_phase("vet", [str(sdk / "bin/go.exe"), "-C", "native/go_runtime", "vet",
                                      "-mod=vendor", "./..."], remaining,
                               root, environment, output, report, started)
            report["vet"]["state"] = "PASS" if vetted["passed"] else "FAIL_OR_INCONCLUSIVE"
        else:
            report["vet"] = {"state": "UNRUN", "reason": "Tests did not pass" if not tested["passed"]
                             else "Less than 15s actual work budget remained",
                             "remainingSeconds": remaining}
    except BaseException as error:
        report["errors"].append(f"{type(error).__name__}: {error}")
    finally:
        try:
            if audit is not None:
                after = native_snapshot(audit)
                report["sourceAfterChecks"] = after
                report["sourceDrift"] = changed(frozen["files"], after["files"]) if frozen else None
                report["nativeDigestDrift"] = bool(frozen and
                    frozen["nativeSourceSha256"] != after["nativeSourceSha256"])
            if before_tools is not None:
                after_tools = identities(setup(root, args)[3])
                report["toolIdentitiesAfter"] = after_tools
                report["toolDrift"] = changed(before_tools, after_tools)
        except BaseException as error:
            report["errors"].append(f"Final identity capture: {type(error).__name__}: {error}")
        skipped = []
        test_log = output / "test.stdout.bin"
        if test_log.is_file():
            skipped = [line.decode("utf-8", errors="replace").rstrip("\r\n")
                       for line in test_log.read_bytes().splitlines() if b"--- SKIP:" in line]
        report["testSkips"] = skipped
        report["skipReview"] = "REQUIRED" if skipped else "No verbose SKIP lines observed"
        released = all(phase["cleanupConfirmed"] for phase in report["phases"])
        report["release"] = "RELEASE" if released else "HOLD_UNRELEASED"
        report["rootsStarted"] = sum(bool(phase.get("process", {}).get("rootCreated")) for phase in report["phases"])
        report["finishedAt"] = now()
        report["elapsedSeconds"] = round(time.monotonic() - started, 3)
        report["within150Seconds"] = report["elapsedSeconds"] <= 150
        report["withinPlanSeconds"] = report["within150Seconds"]
        passed = (released and report["within150Seconds"] and len(report["phases"]) == 3 and
                  all(phase["passed"] for phase in report["phases"]) and not report["errors"] and
                  not report.get("sourceDrift") and not report.get("nativeDigestDrift") and
                  not report.get("toolDrift") and report["vet"]["state"] == "PASS")
        report["result"] = ("PASS_REQUIRES_SKIP_REVIEW" if skipped else "PASS") if passed else "FAIL_OR_INCONCLUSIVE"
        save(output / "report.json", report)
        lines = [f"{report['release']} {report['grant']}; next owner {report['nextOwner']}.",
                 f"Result {report['result']}; elapsed {report['elapsedSeconds']}s; within150s={report['within150Seconds']}."]
        for phase in report["phases"]:
            process = phase.get("process", {})
            lines.append(f"{phase['name']}: HANDLE={process.get('processHandleDecimal')} "
                         f"({process.get('processHandleHex')}), PID={process.get('pid')}, "
                         f"creationFILETIME={process.get('creationFiletime100ns')}, "
                         f"terminal={process.get('terminal')}, exit={process.get('exitCode')}, "
                         f"jobActiveProcesses={process.get('jobActiveProcesses')}, "
                         f"cleanupConfirmed={phase['cleanupConfirmed']}.")
        lines.extend([f"Vet: {report['vet']['state']}; skip review: {report['skipReview']}.",
                      f"Frozen native source: {report.get('frozenNativeSourceSha256')}.",
                      "Publication NOT_ATTEMPTED; parent must publish this exact evidence.",
                      "No build, corpus, SDK/Flutter, WSL or device gate is closed by this run."])
        (output / "release-message.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines), flush=True)
    return 0 if report["result"] == "PASS" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars="@")
    parser.add_argument("--grant", required=True, help="NEW explicitly authorized named grant; never Go236")
    parser.add_argument("--next-owner", required=True)
    parser.add_argument("--owned-go", action="append",
                        help="Explicit owned native .go path relative to repository; repeat for each file")
    parser.add_argument("--control-only", action="store_true",
                        help="Only real Python ownership controls, 15s plan; never starts Go")
    parser.add_argument("--controls-report", type=Path,
                        help="Matching same-grant PASS CONTROL_ONLY report, required before native work")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[5])
    parser.add_argument("--output", type=Path, required=True, help="New evidence directory; must not exist")
    parser.add_argument("--clang", type=Path,
                        default=Path("D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/native/llvm/bin/clang.exe"))
    parser.add_argument("--mingw", type=Path, default=Path("D:/ProgramFiles/Dev-Cpp/MinGW64"))
    parser.add_argument("--outer-handle", help="Optional exact launching tool/session handle supplied by parent")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("Windows only")
    if (not args.grant.strip() or args.grant.strip().casefold() == "go236" or
            not args.next_owner.strip() or args.grant.startswith("REPLACE_") or
            args.next_owner.startswith("REPLACE_")):
        parser.error("A NEW nonempty named grant and explicit next owner are required; Go236 is released")
    if args.control_only:
        if args.owned_go or args.controls_report:
            parser.error("CONTROL_ONLY does not accept formatting paths or a prior controls report")
        return run_controls(args)
    if not args.owned_go or args.controls_report is None:
        parser.error("Native checks require explicit --owned-go paths and matching --controls-report")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
