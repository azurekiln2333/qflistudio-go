"""UNRUN exact-Job control plane; future exact-source C approval and NEW grant only.
Import has no I/O, Win32 call, imported runner, process, timer or publication.
The live controller/final sender never claims its own terminal state.
"""
from __future__ import annotations
import argparse
import ast
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path('D:/MyNewProjects/qfli_go')
RESEARCH = ROOT / '.trellis/tasks/10-22-go-offline-ide/research'
SELF = RESEARCH / 'fixtures/native_terminal_job_controller.py'
RUNNER = RESEARCH / 'fixtures/run_native_window.py'
WRAPPER = RESEARCH / 'fixtures/run_native_grant.py'
ADAPTER = ROOT / 'native/go_runtime/windows-cc.cmd'
PYTHON = Path('D:/ProgramFiles/Python/Python313/python.exe')
POWERSHELL = Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
RUNNER_SHA = '9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8'
WRAPPER_SHA = '295b23b5dfc1f94b758ad6a34ba372cbbd0b6ae14b84a3d3b8c85c4280833441'
ADAPTER_SHA = '5c486c5420c7d74178250e03fa52061c7df638418560744d587bbba7e36c4f8b'
PYTHON_SHA = 'd87063e5597f257004c731b66c59c56c91038861c6877b1a3dca6b8c4e919125'
PROTOCOL = 'go-native-exact-job-controller/v1'
TOTAL_SECONDS = 180.0
# Controls admission reserves the complete15s plan plus final sender3s.
PUBLISH_SECONDS = 3.0
CONTROLS_MIN_REMAINING_SECONDS = 15.0 + PUBLISH_SECONDS
POLL_SECONDS = 0.1
CONSUMED = frozenset({'go236', 'go509', 'c580-go180-20261025', 'go-native-20261026-01'})
_RUNNER_MODULE = None
_RETAINED = []  # Strong original ownership across errors, HOLD and retries.


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def read_bound(path, expected=None):
    raw = Path(path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if expected is not None and actual != expected:
        raise ValueError(f'Bound report/config changed: {path}')
    return json.loads(raw), actual


def source_snapshot():
    native = ROOT / 'native/go_runtime'
    files = []
    for directory, folders, names in os.walk(native, followlinks=False):
        for name in folders + names:
            if (Path(directory) / name).is_symlink():
                raise ValueError('Native source symlink is not accepted')
        for name in names:
            item = Path(directory) / name
            if item.suffix in ('.go', '.c', '.h', '.s', '.S', '.syso') or name in ('go.mod', 'go.sum', 'modules.txt'):
                files.append(item)
    files.sort(key=lambda item: tuple(part.lower() for part in item.parts))
    inventory = [[p.relative_to(native).as_posix(), digest(p)] for p in files]
    raw = json.dumps(inventory, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return {'count': len(files), 'sha256': hashlib.sha256(raw).hexdigest()}


def preflight(config, include_source=True):
    if os.name != 'nt' or Path(sys.executable).resolve() != PYTHON.resolve():
        raise ValueError('Pinned Windows Python is required')
    for path, expected in ((SELF, config['expectedControllerSha256']), (RUNNER, RUNNER_SHA),
                           (WRAPPER, WRAPPER_SHA), (ADAPTER, ADAPTER_SHA), (PYTHON, PYTHON_SHA)):
        if digest(path) != expected:
            raise ValueError(f'Pinned source/tool drift: {path}')
    if include_source:
        snapshot = source_snapshot()
        if snapshot != {'count': 374, 'sha256': config['expectedNativeSourceSha256']}:
            raise ValueError(f'Native source drift: {snapshot}')
        return snapshot


def load_runner():
    """Runtime-only verified import; frozen module defines but does not act."""
    global _RUNNER_MODULE
    if digest(RUNNER) != RUNNER_SHA:
        raise ValueError('Frozen ownership helper drift')
    if _RUNNER_MODULE is None:
        spec = importlib.util.spec_from_file_location('_go_frozen_ownership', RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _RUNNER_MODULE = module
    return _RUNNER_MODULE


def owned_go_paths():
    """Read literal ownership; never import or execute the frozen wrapper."""
    if digest(WRAPPER) != WRAPPER_SHA:
        raise ValueError('Frozen ownership-list source drift')
    tree = ast.parse(WRAPPER.read_text(encoding='utf-8'))
    matches = [n for n in tree.body if isinstance(n, ast.Assign) and
               any(isinstance(t, ast.Name) and t.id == 'OWNED_GO_PATHS' for t in n.targets)]
    if len(matches) != 1:
        raise ValueError('Ownership list is ambiguous')
    paths = ast.literal_eval(matches[0].value)
    if not isinstance(paths, tuple) or len(paths) != 36 or len(set(paths)) != 36:
        raise ValueError('Expected exact frozen36-path ownership')
    if not all(isinstance(p, str) and p.startswith('native/go_runtime/') and p.endswith('.go') for p in paths):
        raise ValueError('Unexpected formatting ownership')
    return paths


class ExactRoot:
    """Original root/Job retained; no kill-on-close and no timeout kill."""
    def __init__(self, name, directory, command, environment):
        self.name, self.streams, self.drained = name, [], False
        self.started, self.job = time.monotonic(), None
        self.record = {'name': name, 'command': list(map(str, command)), 'startedAt': now(),
                       'state': 'CREATING', 'deadlineExceeded': False, 'errors': [],
                       'process': {}, 'drainConfirmed': False}
        _RETAINED.append(self)
        try:
            helper = load_runner()
            self.job = helper.OwnedJob()
            self.record['process'] = self.job.record
            # Clear KILL_ON_JOB_CLOSE BEFORE creating a root, then query it back.
            limits = helper.ExtendedLimits()
            limits.basic.flags = 0
            self.job.check(self.job.k.SetInformationJobObject(
                self.job.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
            actual = helper.ExtendedLimits()
            self.job.check(self.job.k.QueryInformationJobObject(
                self.job.job, 9, ctypes.byref(actual), ctypes.sizeof(actual), None))
            if actual.basic.flags != 0:
                raise RuntimeError('Cannot prove no implicit kill/breakaway flags')
            self.record['killOnJobClose'] = False
            for suffix in ('stdout', 'stderr'):
                self.streams.append((Path(directory) / f'{name}.{suffix}.bin').open('xb'))
            self.job.start(list(map(str, command)), ROOT, environment, *self.streams)
            self.record['state'] = 'LIVE'
        except BaseException as error:
            self.record['errors'].append(f'{type(error).__name__}: {error}')
            self.record['state'] = 'HOLD_START_UNCERTAIN'
            # Partial assignment failure retains exact suspended root; no kill.

    def poll(self):
        if self.drained:
            return True
        if self.job is None:
            self.record['state'] = 'HOLD_NO_JOB_PROOF'
            return False
        try:
            if self.job.empty():
                self.drained = True
                self.record.update(drainConfirmed=True, terminalObservedAt=now(), state='TERMINAL_ACTIVE0')
                self.record['elapsedSeconds'] = time.monotonic() - self.started
                for stream in self.streams:
                    stream.close()
                self.streams.clear()
                self.job.close()  # Safe only after original Job active0/root terminal.
                if self.job.record.get('handlesClosed') is not True:
                    self.record['errors'].append('Terminal handle close not confirmed')
                return True
        except BaseException as error:
            self.record['errors'].append(f'Poll: {type(error).__name__}: {error}')
            self.record['state'] = 'HOLD_OBSERVATION_UNCERTAIN'
        return False

    def exact_terminal(self):
        p = self.record['process']
        return (self.drained and p.get('rootCreated') is True and p.get('terminal') is True and
                p.get('jobActiveProcesses') == 0 and p.get('handlesClosed') is True and
                p.get('assignedBeforeResume') is True and p.get('resumed') is True and
                not p.get('errors') and not self.record['errors'] and
                all(str(p.get(k, '')).isdigit() and int(p[k]) > 0 for k in
                    ('pid', 'processHandleDecimal', 'jobHandleDecimal', 'creationFiletime100ns')) and
                type(p.get('exitCode')) is int)


def wait_original(root, deadline, persist):
    """Deadline limits acceptance; unresolved originals remain HOLD indefinitely."""
    while not root.poll():
        if time.monotonic() >= deadline:
            root.record.update(deadlineExceeded=True, state='HOLD_DEADLINE_OR_OBSERVATION')
        persist()
        time.sleep(POLL_SECONDS)
    if time.monotonic() >= deadline:
        root.record['deadlineExceeded'] = True
    persist()


def process_environment():
    names = ('SystemRoot', 'WINDIR', 'COMSPEC', 'TEMP', 'TMP', 'USERPROFILE',
             'LOCALAPPDATA', 'APPDATA', 'PROGRAMDATA', 'PATHEXT', 'PATH')
    result = {name: os.environ[name] for name in names if name in os.environ}
    result.update(PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    return result


def payload_drain(report, grant, mode, pid):
    problems = []
    if (report.get('mode') != mode or report.get('grant') != grant or
            report.get('nextOwner') != 'c-coordinator' or report.get('wrapperPid') != pid or
            Path(report.get('root', '')).resolve() != ROOT.resolve() or report.get('release') != 'RELEASE'):
        problems.append('Frozen runner report identity/release mismatch')
    phases = report.get('phases')
    if not isinstance(phases, list) or not phases:
        return problems + ['No exact payload ledger']
    for phase in phases:
        p = phase.get('process', {})
        if (phase.get('cleanupConfirmed') is not True or p.get('terminal') is not True or
                p.get('jobActiveProcesses') != 0 or p.get('handlesClosed') is not True):
            problems.append(f"Payload not proven drained: {phase.get('name')}")
        if p.get('rootCreated') is True and (
                p.get('assignedBeforeResume') is not True or p.get('resumed') is not True or
                type(p.get('exitCode')) is not int or any(
                    not str(p.get(k, '')).isdigit() or int(p[k]) <= 0 for k in
                    ('pid', 'processHandleDecimal', 'jobHandleDecimal', 'creationFiletime100ns'))):
            problems.append(f"Payload exact identity incomplete: {phase.get('name')}")
    return problems


def validation_child(config, config_sha):
    """New validation root: frozen controls then native using the outer ACK clock."""
    report = {'schemaVersion': 1, 'mode': 'EXACT_JOB_VALIDATION_CHILD', 'grant': config['grant'],
              'nextOwner': 'c-coordinator', 'wrapperPid': os.getpid(), 'root': str(ROOT),
              'configSha256': config_sha, 'phases': [], 'errors': [], 'release': 'HOLD_UNRELEASED',
              'result': 'FAIL_OR_INCONCLUSIVE', 'startedAt': now()}
    output = Path(config['output']) / 'validation'
    output.mkdir(exist_ok=False)
    def persist():
        report['updatedAt'] = now()
        report['elapsedFromAckAttemptSeconds'] = time.monotonic() - config['ackMonotonic']
        try:
            write_json(output / 'progress.json', report)
        except OSError as error:
            report['errors'].append(f'Progress evidence write: {error}')
    try:
        preflight(config)
        owned = owned_go_paths()
        for phase_name in ('controls', 'native'):
            remaining = TOTAL_SECONDS - (time.monotonic() - config['ackMonotonic'])
            if phase_name == 'native' and remaining < 157.5:
                report['nativeSkipped'] = {'reason': 'ACK-clock remaining below157.5s', 'remaining': remaining}
                break
            preflight(config)
            # Preflight may consume reserve. Check again immediately before start.
            remaining = TOTAL_SECONDS - (time.monotonic() - config['ackMonotonic'])
            if phase_name == 'controls' and remaining < CONTROLS_MIN_REMAINING_SECONDS:
                report['controlsSkipped'] = {'reason': 'Post-preflight ACK-clock reserve below controls15s+final3s',
                                             'remaining': remaining,
                                             'required': CONTROLS_MIN_REMAINING_SECONDS}
                break
            if phase_name == 'native' and remaining < 157.5:
                report['nativeSkipped'] = {'reason': 'Post-preflight remaining below157.5s', 'remaining': remaining}
                break
            phase_output = output / phase_name
            command = [PYTHON, '-B', '-X', 'utf8', RUNNER, '--grant', config['grant'],
                       '--next-owner', 'c-coordinator', '--root', ROOT, '--output', phase_output]
            if phase_name == 'controls':
                command.append('--control-only')
            else:
                command.extend(['--controls-report', output / 'controls/report.json'])
                for path in owned:
                    command.extend(['--owned-go', path])
            environment = process_environment()
            if phase_name == 'controls':
                # Command/environment preparation can also consume the lease.
                # This final admission check immediately precedes root creation.
                remaining = TOTAL_SECONDS - (time.monotonic() - config['ackMonotonic'])
                if remaining < CONTROLS_MIN_REMAINING_SECONDS:
                    report['controlsSkipped'] = {'reason': 'Pre-spawn ACK-clock reserve below controls15s+final3s',
                                                 'remaining': remaining,
                                                 'required': CONTROLS_MIN_REMAINING_SECONDS}
                    break
            child = ExactRoot(phase_name, output, command, environment)
            phase = {'name': phase_name, 'outer': child.record, 'remainingAtStartSeconds': remaining}
            report['phases'].append(phase)
            persist()
            wait_original(child, child.started + (15 if phase_name == 'controls' else 150), persist)
            if not child.exact_terminal():
                report['errors'].append(f'{phase_name}: exact outer terminal/drain proof failed')
                break
            evidence, sha = read_bound(phase_output / 'report.json')
            phase.update(reportSha256=sha, reportPath=str(phase_output / 'report.json'), payload=evidence)
            phase['drainProblems'] = payload_drain(evidence, config['grant'],
                'CONTROL_ONLY' if phase_name == 'controls' else 'NATIVE', child.record['process']['pid'])
            if phase['drainProblems']:
                report['errors'].extend(phase['drainProblems'])
                break
            if phase_name == 'controls' and (evidence.get('result') != 'PASS' or
                    evidence.get('withinPlanSeconds') is not True or child.record['process']['exitCode'] != 0 or
                    child.record['deadlineExceeded']):
                report['errors'].append('Controls did not PASS within15 and drain; native retired')
                break
        # Cleanup is independent of the validation verdict. Failed controls or
        # native assertions must not reserve an empty host slot.
        if report['phases'] and all(p.get('payload') is not None and not p.get('drainProblems')
                and p['outer'].get('drainConfirmed') is True and
                p['outer']['process'].get('handlesClosed') is True for p in report['phases']):
            report['release'] = 'RELEASE'
        native = next((p for p in report['phases'] if p['name'] == 'native'), None)
        if (report['release'] == 'RELEASE' and native and native['payload'].get('result') == 'PASS' and
                native['outer']['process']['exitCode'] == 0 and not native['outer']['deadlineExceeded']):
            report['result'] = 'PASS'
    except BaseException as error:
        report['errors'].append(f'{type(error).__name__}: {error}')
    finally:
        # Exceptions cannot abandon live exact roots. No kill/replacement/retry.
        while any(not root.poll() for root in _RETAINED):
            report['release'] = 'HOLD_UNRELEASED'
            persist()
            time.sleep(POLL_SECONDS)
        if not report['phases'] and not _RETAINED:
            report['noPayloadsStarted'] = True
            report['release'] = 'RELEASE'
        report['finishedAt'] = now()
        report['elapsedFromAckAttemptSeconds'] = time.monotonic() - config['ackMonotonic']
        write_json(output / 'report.json', report)  # Final report LAST.
    return 0 if report['result'] == 'PASS' else 1


class Controller:
    """Persistent control plane; an unresolved durable guard blocks cross-runs."""
    def __init__(self):
        self.run, self.final_body = None, None
        self.children = []
        self.guard = RESEARCH / 'native-job-controller-unresolved.json'

    def persist(self):
        if self.run is None:
            return
        self.run['updatedAt'] = now()
        self.run['elapsedFromAckAttemptSeconds'] = time.monotonic() - self.run['ackMonotonic']
        try:
            write_json(Path(self.run['output']) / 'controller.json', self.run)
            if self.run.get('nextRunEligible') is not True:
                write_json(self.guard, {'protocol': PROTOCOL, 'controllerPid': os.getpid(),
                                       'grant': self.run['grant'], 'output': self.run['output'],
                                       'state': self.run['state'], 'updatedAt': now()})
            return True
        except OSError as error:
            # Evidence failure must not terminate the owner of live HANDLEs.
            self.run['errors'].append(f'Controller evidence write: {error}')
            self.run['state'] = 'HOLD_EVIDENCE_WRITE'
            return False

    def validate_request(self, request):
        if os.name != 'nt':
            raise ValueError('Windows only')
        if self.guard.exists() or (self.run and not self.run.get('nextRunEligible')):
            raise ValueError('Unresolved earlier run: no automatic recovery or next grant')
        if request.get('protocol') != PROTOCOL:
            raise ValueError('Explicit reviewed protocol required')
        grant = request.get('grant', '')
        if (not isinstance(grant, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{5,100}', grant) or
                grant.casefold() in CONSUMED or re.search(r'replace|placeholder|^c580|^go236|^go509', grant, re.I)):
            raise ValueError('A NEW explicitly authorized named grant is required')
        if not re.fullmatch(r'go-native-job-[0-9]{8}-[a-z0-9-]+', request.get('outputName', '')):
            raise ValueError('Fresh bounded output name required')
        for key in ('expectedControllerSha256', 'expectedNativeSourceSha256'):
            if not re.fullmatch(r'[a-f0-9]{64}', request.get(key, '')):
                raise ValueError(f'Explicit reviewed identity required: {key}')
        approval, grant_event = request.get('approvalEvent', {}), request.get('grantEvent', {})
        if (approval.get('by') != 'c-coordinator' or type(approval.get('seq')) is not int or approval['seq'] <= 717 or
                PROTOCOL not in approval.get('text', '') or request['expectedControllerSha256'] not in approval.get('text', '') or
                grant_event.get('by') != 'c-coordinator' or type(grant_event.get('seq')) is not int or
                grant_event['seq'] <= approval['seq'] or grant not in grant_event.get('text', '')):
            raise ValueError('Need exact-source C approval AFTER717 and a later NEW grant receipt')
        if (RESEARCH / request['outputName']).exists():
            raise ValueError('Output exists; no reuse')
        marker = RESEARCH / 'native-job-controller-consumed' / f'{grant.lower()}.json'
        if marker.exists():
            raise ValueError('Durable grant-consumed marker exists')
        preflight(request)
        return marker

    def publisher(self, kind, body):
        if any(not child.poll() for child in self.children):
            raise RuntimeError('No sender may overlap an unresolved validation/publisher Job')
        output = Path(self.run['output'])
        name = f"publisher-{len(self.run['publishers']):02d}-{kind}"
        message = output / f'{name}.message.txt'
        message.write_text(body.strip() + '\n', encoding='utf-8', newline='\n')
        script = output / 'publish.ps1'
        script_text = ("$ErrorActionPreference='Stop'\n" +
            "$OutputEncoding=[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)\n" +
            "Get-Content -Raw -Encoding UTF8 -LiteralPath $env:QFLI_GO_CONTROLLER_MESSAGE | " +
            "& 'D:/AppData/Roaming/npm/trellis.cmd' channel send qfli-core-release-sync " +
            "--scope global --as go-offline-1022 --to c-coordinator --stdin\nexit $LASTEXITCODE\n")
        if script.exists():
            if script.read_bytes() != script_text.encode('utf-8'):
                raise ValueError('Generated fixed publisher script drift; no sender launch')
        else:
            script.write_text(script_text, encoding='utf-8', newline='\n')
        environment = process_environment()
        environment['QFLI_GO_CONTROLLER_MESSAGE'] = str(message)
        command = [POWERSHELL, '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', script]
        sender = ExactRoot(name, output, command, environment)
        self.children.append(sender)
        entry = {'kind': kind, 'messageSha256': digest(message), 'outer': sender.record,
                 'deadlineSeconds': PUBLISH_SECONDS, 'confirmed': False}
        self.run['publishers'].append(entry)
        self.persist()
        wait_original(sender, sender.started + PUBLISH_SECONDS, self.persist)
        if sender.exact_terminal() and sender.record['process']['exitCode'] == 0:
            try:
                lines = (output / f'{name}.stdout.bin').read_text(encoding='utf-8-sig').splitlines()
                events = []
                for line in lines:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(event, dict) and event.get('kind') == 'message':
                        events.append(event)
                matches = [e for e in events if e.get('by') == 'go-offline-1022' and
                           e.get('to') == 'c-coordinator' and e.get('text', '').strip() == body.strip() and
                           type(e.get('seq')) is int and e['seq'] > 0 and isinstance(e.get('ts'), str)]
                if len(matches) == 1:
                    entry.update(confirmed=True, event=matches[0])
            except BaseException as error:
                entry['parseError'] = f'{type(error).__name__}: {error}'
        entry['senderTerminalEvidenceAt'] = now()
        self.persist()
        return entry

    def final_proof(self, validation):
        if not validation.exact_terminal():
            return {'proven': False, 'problems': ['Exact validation outer terminal/active0 unproven']}
        path = Path(self.run['output']) / 'validation/report.json'
        report, sha = read_bound(path)
        problems = []
        if (report.get('mode') != 'EXACT_JOB_VALIDATION_CHILD' or report.get('grant') != self.run['grant'] or
                report.get('wrapperPid') != validation.record['process']['pid'] or
                report.get('nextOwner') != 'c-coordinator' or report.get('configSha256') != self.run['childConfigSha256'] or
                Path(report.get('root', '')).resolve() != ROOT.resolve() or report.get('release') != 'RELEASE'):
            problems.append('Validation report identity/release binding failed')
        phases = report.get('phases', [])
        if ((not phases and report.get('noPayloadsStarted') is not True) or
                [p.get('name') for p in phases] not in ([], ['controls'], ['controls', 'native'])):
            problems.append('Missing/unknown/reordered validation phases')
        for phase in phases:
            outer = phase.get('outer', {})
            p = outer.get('process', {})
            if (outer.get('drainConfirmed') is not True or p.get('terminal') is not True or
                    p.get('jobActiveProcesses') != 0 or p.get('handlesClosed') is not True or
                    p.get('rootCreated') is not True or p.get('assignedBeforeResume') is not True or
                    p.get('resumed') is not True or type(p.get('exitCode')) is not int or any(
                        not str(p.get(k, '')).isdigit() or int(p[k]) <= 0 for k in
                        ('pid', 'processHandleDecimal', 'jobHandleDecimal', 'creationFiletime100ns')) or
                    outer.get('errors') or p.get('errors')):
                problems.append(f"Validation phase outer unproven: {phase.get('name')}")
            payload_path = Path(self.run['output']) / 'validation' / phase['name'] / 'report.json'
            payload, actual = read_bound(payload_path, phase.get('reportSha256'))
            if payload != phase.get('payload'):
                problems.append('Embedded payload report differs from bound file')
            problems.extend(payload_drain(payload, self.run['grant'],
                'CONTROL_ONLY' if phase['name'] == 'controls' else 'NATIVE', p.get('pid')))
        if any(not child.exact_terminal() for child in self.children):
            problems.append('An earlier publisher/validation root lacks exact terminal+active0 proof')
        return {'proven': not problems, 'problems': problems, 'validationReportSha256': sha,
                'result': report.get('result'), 'phases': phases, 'reportPath': str(path)}

    def deliver_final(self):
        if self.final_body is None or not self.run.get('drainProof', {}).get('proven'):
            raise ValueError('No proven terminal body; HOLD, no final retry')
        if any(not child.exact_terminal() for child in self.children):
            raise ValueError('Original sender/validation unresolved; no replacement sender')
        final = self.publisher('final', self.final_body)
        self.run['finalSender'] = final
        self.run['within180SecondsAtFinalSenderTerminal'] = time.monotonic() - self.run['ackMonotonic'] <= TOTAL_SECONDS
        self.run['nextRunEligible'] = bool(final['confirmed'] and final['outer']['process'].get('exitCode') == 0 and
                                           all(child.exact_terminal() for child in self.children))
        self.run['state'] = 'FINAL_SENDER_TERMINAL' if self.run['nextRunEligible'] else 'HOLD_FINAL_PUBLICATION'
        if not self.persist():  # Durable final-sender proof precedes unlocking.
            self.run['nextRunEligible'] = False
            return self.run
        if self.run['nextRunEligible']:
            self.guard.unlink()  # Only our exclusive marker; no process/Job operation.
        return self.run

    def retire_without_validation(self, reason):
        if any(not child.exact_terminal() for child in self.children):
            self.run['state'] = 'HOLD_PRELAUNCH_PUBLISHER_IDENTITY'
            self.run['errors'].append(reason)
            self.persist()
            return self.run
        self.run['drainProof'] = {'proven': True, 'problems': [],
            'validationLaunched': False, 'result': 'DEFERRED_NO_VALIDATION', 'reason': reason}
        self.final_body = (f"Go {self.run['grant']} FINAL TERMINAL RELEASE -> c-coordinator; "
            f"validation NOT LAUNCHED; reason={reason}; exact prior publishers="
            f"{json.dumps(self.run['publishers'], separators=(',', ':'))}; "
            'all prior publishers terminal+active0. This final sender remains LIVE. '
            'Controller remains live control plane only. Inspect controller.json finalSender '
            'actual terminal/result/active0 before another SDK grant. No self-terminal '
            'claim, successor grant or historical replay.')
        return self.deliver_final()

    def start(self, request):
        marker = self.validate_request(request)
        # Exclusive guard precedes consuming the named grant. Failure is fail-closed.
        with self.guard.open('x', encoding='utf-8') as stream:
            json.dump({'protocol': PROTOCOL, 'grant': request['grant'], 'controllerPid': os.getpid(),
                       'state': 'RESERVED_SOURCE_PREFLIGHT', 'createdAt': now()}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        marker.parent.mkdir(exist_ok=True)
        with marker.open('x', encoding='utf-8') as stream:
            json.dump({'grant': request['grant'], 'consumedAt': now(), 'controllerSha256': digest(SELF)}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        output = RESEARCH / request['outputName']
        output.mkdir(exist_ok=False)
        self.children, self.final_body = [], None
        self.run = {**request, 'output': str(output), 'controllerPid': os.getpid(), 'controllerRole': 'control-plane-only',
                    'controllerTerminalClaimed': False, 'nextRunEligible': False, 'state': 'ACK_PENDING',
                    'publishers': [], 'errors': [], 'ackMonotonic': time.monotonic(), 'ackAttemptAt': now()}
        self.persist()
        ack_body = (f"Go ACCEPT NEW {request['grant']}; protocol {PROTOCOL}; next-owner c-coordinator; "
                    'controls<=15s/native150 only ACK-clock remaining>=157.5s; total180 includes final sender. '
                    'Persistent controller is control plane only; no self-terminal claim; no extras/successor grant.')
        ack = self.publisher('ack', ack_body)
        self.run['ack'] = ack
        if not ack['confirmed'] or ack['outer']['deadlineExceeded']:
            return self.retire_without_validation('ACK delivery unconfirmed or sender exceeded3s')
        if time.monotonic() - self.run['ackMonotonic'] > 7.5:
            return self.retire_without_validation('ACK/prelaunch reserve exceeded7.5s')
        try:
            preflight(self.run)
        except BaseException as error:
            return self.retire_without_validation(f'Prelaunch drift/error: {type(error).__name__}: {error}')
        child_config = {k: self.run[k] for k in ('grant', 'output', 'expectedControllerSha256',
                                               'expectedNativeSourceSha256', 'ackMonotonic')}
        config_path = output / 'child-config.json'
        write_json(config_path, child_config)
        self.run['childConfigSha256'] = digest(config_path)
        if time.monotonic() - self.run['ackMonotonic'] > 7.5:
            return self.retire_without_validation('Post-preflight reserve exceeded7.5s')
        command = [PYTHON, '-B', '-X', 'utf8', SELF, '--validation-child', config_path,
                   '--config-sha256', self.run['childConfigSha256']]
        validation = ExactRoot('validation-outer', output, command, process_environment())
        self.children.append(validation)
        self.run['validationOuter'] = validation.record
        self.run['state'] = 'VALIDATION_LIVE'
        self.persist()
        wait_original(validation, self.run['ackMonotonic'] + TOTAL_SECONDS - PUBLISH_SECONDS, self.persist)
        try:
            self.run['drainProof'] = self.final_proof(validation)
        except BaseException as error:
            self.run['drainProof'] = {'proven': False, 'problems': [f'{type(error).__name__}: {error}']}
        if not self.run['drainProof']['proven']:
            self.run['state'] = 'HOLD_DRAIN_PROOF_UNCONFIRMED'
            self.persist()
            return self.run
        self.final_body = (f"Go {self.run['grant']} FINAL TERMINAL RELEASE -> c-coordinator. "
            f"Exact validation outer={json.dumps(validation.record, separators=(',', ':'))}. "
            f"Exact drain proof={json.dumps(self.run['drainProof'], separators=(',', ':'))}. "
            f"Prior publishers={json.dumps(self.run['publishers'], separators=(',', ':'))}. "
            f"Evidence={output / 'controller.json'}. "
            'Validation outer and earlier publishers are terminal+active0. This final sender is currently LIVE. '
            'Controller remains live CONTROL PLANE only. No final-sender/controller self-terminal claim. '
            'Before another SDK grant C must inspect controller.json finalSender actual terminal/result/active0. '
            'Actual channel timestamps/final-sender terminal evidence determine180s; no predicted timing claim. '
            'No automatic successor grant; consumed grant cannot rerun.')
        return self.deliver_final()


def serve():
    """Persistent stdin NDJSON; EOF cannot abandon live original HANDLE ownership."""
    controller = Controller()
    while True:
        line = sys.stdin.readline()
        if not line:
            if any(not child.poll() for child in _RETAINED):
                if controller.run:
                    controller.run['state'] = 'HOLD_INPUT_EOF_ORIGINALS_RETAINED'
                    controller.persist()
                time.sleep(POLL_SECONDS)
                continue
            return 0
        try:
            command = json.loads(line)
            action = command.get('action')
            if action == 'start':
                result = controller.start(command['request'])
            elif action == 'retry-final':
                result = controller.deliver_final()  # Publication only, never validation.
            elif action == 'status':
                result = controller.run
            else:
                raise ValueError('Only start, status and retry-final are supported')
            print(json.dumps({'ok': True, 'result': result}, ensure_ascii=False), flush=True)
        except BaseException as error:
            if controller.run:
                controller.run['errors'].append(f'{type(error).__name__}: {error}')
                controller.run['state'] = 'HOLD_CONTROL_ERROR'
                controller.persist()
            print(json.dumps({'ok': False, 'error': f'{type(error).__name__}: {error}'}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--serve', action='store_true')
    group.add_argument('--validation-child', type=Path)
    parser.add_argument('--config-sha256')
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Prepared Windows-only controller')
    if args.serve:
        return serve()
    if not args.config_sha256 or not re.fullmatch(r'[a-f0-9]{64}', args.config_sha256):
        parser.error('Child requires its exact parent-bound config SHA256')
    config, sha = read_bound(args.validation_child, args.config_sha256)
    return validation_child(config, sha)


if __name__ == '__main__':
    raise SystemExit(main())
