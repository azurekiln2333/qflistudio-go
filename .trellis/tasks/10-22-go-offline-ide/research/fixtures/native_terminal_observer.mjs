/**
 * Prepared, UNRUN persistent control-plane observer.
 * Import has no I/O, process launch, timers, channel publication or grant action.
 * C must approve this controller/validation-root distinction before start().
 */
import * as cp from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as crypto from 'node:crypto';

const ROOT = 'D:/MyNewProjects/qfli_go';
const RESEARCH = `${ROOT}/.trellis/tasks/10-22-go-offline-ide/research`;
const WRAPPER = `${RESEARCH}/fixtures/run_native_grant.py`;
const RUNNER = `${RESEARCH}/fixtures/run_native_window.py`;
const ADAPTER = `${ROOT}/native/go_runtime/windows-cc.cmd`;
const PYTHON = 'D:/ProgramFiles/Python/Python313/python.exe';
const POWERSHELL = 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe';
const WRAPPER_SHA = '295b23b5dfc1f94b758ad6a34ba372cbbd0b6ae14b84a3d3b8c85c4280833441';
const RUNNER_SHA = '9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8';
const PYTHON_SHA = 'd87063e5597f257004c731b66c59c56c91038861c6877b1a3dca6b8c4e919125';
const ADAPTER_SHA = '5c486c5420c7d74178250e03fa52061c7df638418560744d587bbba7e36c4f8b';
// Fixed command text only: neither the grant nor any message enters shell code.
const SEND_COMMAND = "& 'D:/AppData/Roaming/npm/trellis.cmd' channel send qfli-core-release-sync --scope global --as go-offline-1022 --to c-coordinator --stdin";
const TOTAL_MS = 180_000;
const TERMINAL_NATIVE_STATES = new Set(['FAIL_OR_INCONCLUSIVE', 'PASS', 'PASS_REQUIRES_SKIP_REVIEW']);
const runs = new Map();

const iso = () => new Date().toISOString();
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fileHash = name => hash(fs.readFileSync(name));
const elapsedMs = run => Number(process.hrtime.bigint() - run.startedTick) / 1e6;
const clone = value => JSON.parse(JSON.stringify(value));
const positive = value => /^(?:[1-9][0-9]*)$/.test(String(value));
const samePath = (left, right) => typeof left === 'string' &&
  path.resolve(left).toLowerCase() === path.resolve(right).toLowerCase();

function sourceDigest() {
  const native = path.join(ROOT, 'native/go_runtime');
  const names = [];
  function visit(directory) {
    for (const item of fs.readdirSync(directory, { withFileTypes: true })) {
      const name = path.join(directory, item.name);
      if (item.isSymbolicLink()) throw new Error(`Native source symlink is not accepted: ${name}`);
      if (item.isDirectory()) visit(name);
      else if (item.isFile() && (/\.(?:go|c|h|s|S|syso)$/.test(item.name) ||
        ['go.mod', 'go.sum', 'modules.txt'].includes(item.name))) names.push(name);
    }
  }
  visit(native);
  // Match Python WindowsPath ordering component by component (not locale order).
  names.sort((a, b) => {
    const left = a.toLowerCase().split(/[\\/]/);
    const right = b.toLowerCase().split(/[\\/]/);
    for (let index = 0; index < Math.min(left.length, right.length); index += 1) {
      if (left[index] < right[index]) return -1;
      if (left[index] > right[index]) return 1;
    }
    return left.length - right.length;
  });
  const inventory = names.map(name => [path.relative(native, name).split(path.sep).join('/'), fileHash(name)]);
  return { count: inventory.length, sha256: hash(Buffer.from(JSON.stringify(inventory), 'utf8')) };
}

function requireInputs(run) {
  if (fileHash(WRAPPER) !== WRAPPER_SHA || fileHash(RUNNER) !== RUNNER_SHA || fileHash(PYTHON) !== PYTHON_SHA) {
    throw new Error('Pinned Python/wrapper/runner drift: no validation launch');
  }
  const adapterSha256 = fileHash(ADAPTER);
  run.record.adapter.checks.push({ sha256: adapterSha256, checkedAt: iso() });
  if (adapterSha256 !== ADAPTER_SHA) throw new Error('Pinned Windows compiler adapter drift: no validation launch');
  const source = sourceDigest();
  if (source.count !== 374 || source.sha256 !== run.record.expectedNativeSourceSha256) {
    throw new Error(`Native source drift: ${source.count}/${source.sha256}; no validation launch`);
  }
  if (fs.existsSync(run.output)) throw new Error('Validation output already exists: no reuse');
  return source;
}

function persist(run) {
  run.record.updatedAt = iso();
  run.record.elapsedFromAckAttemptMs = elapsedMs(run);
  const temporary = path.join(run.observerDirectory, 'observer.json.tmp');
  fs.writeFileSync(temporary, `${JSON.stringify(run.record, null, 2)}\n`, { encoding: 'utf8' });
  fs.renameSync(temporary, path.join(run.observerDirectory, 'observer.json'));
}

function safePersist(run) {
  try { persist(run); return true; }
  catch (error) { run.record.errors.push(`Observer evidence write: ${error.message}`); return false; }
}

function readReport(name) {
  const bytes = fs.readFileSync(name);
  return { data: JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/, '')), sha256: hash(bytes), path: name };
}

function eventFrom(stdout, text) {
  for (const line of stdout.split(/\r?\n/)) {
    try {
      const event = JSON.parse(line.replace(/^\uFEFF/, ''));
      if (event.kind === 'message' && event.by === 'go-offline-1022' && event.text === text &&
        Number.isInteger(event.seq) && Number.isFinite(Date.parse(event.ts))) return event;
    } catch { /* Other CLI output is retained in the publisher log, not evidence. */ }
  }
  return null;
}

// The returned Promise resolves only on the ORIGINAL publisher's 'close' event.
// A failed observation never causes a second publisher to overlap this one.
function publish(run, kind, text) {
  if (run.publisherLive) throw new Error('Original publisher remains live; retry is forbidden');
  const ordinal = run.record.publishers.length + 1;
  const item = {
    ordinal, kind, startedAt: iso(), pid: null, spawnObserved: false,
    terminal: false, exitCode: null, signal: null, event: null, delivered: false,
    identityKind: 'original retained Node ChildProcess; no native HANDLE is fabricated',
    controlPlaneOnly: true,
  };
  run.record.publishers.push(item);
  return new Promise(resolve => {
    let stdout = '';
    let out;
    let err;
    try {
      out = fs.openSync(path.join(run.observerDirectory, `publisher-${ordinal}.stdout.bin`), 'wx');
      err = fs.openSync(path.join(run.observerDirectory, `publisher-${ordinal}.stderr.bin`), 'wx');
    } catch (error) {
      if (out !== undefined) fs.closeSync(out);
      item.terminal = true; item.neverSpawned = true; item.error = error.message;
      safePersist(run); resolve(item); return;
    }
    run.publisherLive = true;
    let publisher;
    try {
      publisher = cp.spawn(POWERSHELL,
        ['-NoLogo', '-NoProfile', '-NonInteractive', '-Command', SEND_COMMAND],
        { cwd: ROOT, windowsHide: true, shell: false, stdio: ['pipe', 'pipe', 'pipe'] });
    } catch (error) {
      fs.closeSync(out); fs.closeSync(err);
      run.publisherLive = false;
      item.terminal = true; item.neverSpawned = true; item.error = error.message;
      safePersist(run); resolve(item); return;
    }
    run.publisherChildren.push(publisher); // Exact object retained after terminal too.
    item.pid = publisher.pid ?? null;
    publisher.once('spawn', () => { item.spawnObserved = true; item.pid = publisher.pid; safePersist(run); });
    publisher.stdout.on('data', bytes => {
      try { fs.writeSync(out, bytes); } catch (error) { item.logError = error.message; }
      if (stdout.length < 1_048_576) stdout += bytes.toString('utf8');
      else item.outputTruncated = true;
    });
    publisher.stderr.on('data', bytes => {
      try { fs.writeSync(err, bytes); } catch (error) { item.logError = error.message; }
    });
    publisher.once('error', error => { item.error = error.message; safePersist(run); });
    publisher.stdin.on('error', error => { item.stdinError = error.message; });
    publisher.once('close', (code, signal) => {
      try { fs.closeSync(out); } catch (error) { item.logError = error.message; }
      try { fs.closeSync(err); } catch (error) { item.logError = error.message; }
      item.terminal = true; item.exitCode = code; item.signal = signal; item.closedAt = iso();
      item.elapsedFromAckAttemptMs = elapsedMs(run);
      item.event = eventFrom(stdout, text);
      item.delivered = code === 0 && signal === null && item.event !== null;
      run.publisherLive = false;
      safePersist(run);
      resolve(item);
    });
    publisher.stdin.end(`${text}\n`, 'utf8');
    safePersist(run);
  });
}

function queuePublication(run, kind, text) {
  const next = run.publicationTail.then(() => publish(run, kind, text));
  // Keep the serialization chain usable after an I/O exception, without hiding it.
  run.publicationTail = next.catch(error => { run.record.errors.push(`Publisher: ${error.message}`); safePersist(run); });
  return next;
}

function checkDrain(run) {
  const problems = [];
  const exact = [];
  const wrapper = readReport(path.join(run.output, 'report.json'));
  const report = wrapper.data;
  if (!run.record.validation.terminal) problems.push('Original outer validation ChildProcess is not terminal');
  if (report.mode !== 'GRANT_ORCHESTRATION' || report.grant !== run.record.grant ||
      report.nextOwner !== 'c-coordinator' || !samePath(report.root, ROOT) ||
      report.parentPid !== run.record.validation.pid) problems.push('Outer report identity mismatch');
  if (!Array.isArray(report.phases)) throw new Error('Outer phases are absent');
  const seen = new Set();
  for (const phase of report.phases) {
    if (!['controls', 'native'].includes(phase.phase) || seen.has(phase.phase)) {
      problems.push('Unknown or repeated outer phase'); continue;
    }
    seen.add(phase.phase);
    if (phase.popenRetained !== true || phase.terminal !== true || !Number.isInteger(phase.exitCode) ||
        !positive(phase.pid) || !positive(phase.processHandleDecimal) ||
        !positive(phase.creationFiletime100ns)) problems.push(`${phase.phase}: outer child identity/terminal is unproven`);
    exact.push({ kind: 'retained-python-child', phase: phase.phase, pid: phase.pid,
      processHandleDecimal: phase.processHandleDecimal, processHandleHex: phase.processHandleHex,
      creationFiletime100ns: phase.creationFiletime100ns, terminal: phase.terminal, exitCode: phase.exitCode });
    const child = readReport(path.join(run.output, phase.phase, 'report.json'));
    const expectedMode = phase.phase === 'controls' ? 'CONTROL_ONLY' : 'NATIVE';
    if (child.data.mode !== expectedMode || child.data.grant !== run.record.grant ||
        child.data.nextOwner !== 'c-coordinator' || !samePath(child.data.root, ROOT) || child.data.wrapperPid !== phase.pid ||
        child.data.release !== 'RELEASE' || !Array.isArray(child.data.phases) ||
        child.sha256 !== phase.childReport?.sha256) problems.push(`${phase.phase}: final child report/release binding failed`);
    for (const jobPhase of child.data.phases ?? []) {
      const identity = jobPhase.process ?? {};
      exact.push({ kind: 'windows-job', phase: `${phase.phase}/${jobPhase.name}`,
        cleanupConfirmed: jobPhase.cleanupConfirmed, ...identity });
      if (jobPhase.cleanupConfirmed !== true || identity.terminal !== true ||
          identity.jobActiveProcesses !== 0 || identity.handlesClosed !== true) {
        problems.push(`${phase.phase}/${jobPhase.name}: exact Job is not proven terminal/empty/closed`);
      }
      if (identity.rootCreated === true && (!positive(identity.pid) ||
          !positive(identity.processHandleDecimal) || !positive(identity.jobHandleDecimal) ||
          !positive(identity.creationFiletime100ns) || !Number.isInteger(identity.exitCode))) {
        problems.push(`${phase.phase}/${jobPhase.name}: started root identity is incomplete`);
      }
    }
  }
  if (report.phases.length === 0) problems.push('No final child-phase ledger: no inference of active0');
  if (seen.has('native') && !seen.has('controls')) problems.push('Native phase has no matching controls');
  const terminalResult = TERMINAL_NATIVE_STATES.has(report.result);
  return { proven: problems.length === 0, problems, exact, wrapperSha256: wrapper.sha256,
    nativeResult: terminalResult ? report.result : `UNRECOGNIZED:${String(report.result)}`,
    evidencePath: wrapper.path };
}

function finalMessage(run, proof, state) {
  return [
    `Go ${run.record.grant} ${state} -> c-coordinator; NO SUCCESSOR GRANT.`,
    `Original outer validation ChildProcess PID=${run.record.validation.pid}; ` +
      `terminal=${run.record.validation.terminal}; exit=${run.record.validation.exitCode}; signal=${run.record.validation.signal}.`,
    `Drain proven=${proof.proven}; reportedWrapperResult=${proof.nativeResult}; exact identities=${JSON.stringify(proof.exact)}.`,
    `Problems=${JSON.stringify(proof.problems)}; evidence=${proof.evidencePath}.`,
    `ACK event=${run.record.ack?.event?.seq ?? 'UNCONFIRMED'}; ` +
      `ACK-attempt-to-this-publication-preparation=${elapsedMs(run).toFixed(3)}ms of ${TOTAL_MS}ms.`,
    'Actual ACK/final channel event timestamps determine coordination budget; this text does not predict its own delivery time.',
    'Persistent Node controller remains live control-plane infrastructure, not a validation root. ' +
      'This publisher remains live until send returns; no publisher/controller terminal claim is made here.',
    `Controller distinction approval=${run.record.controllerApprovalEvent}; grant consumed; no rerun; ` +
      'no WSL/device/core/sibling operation or broader acceptance is implied.',
  ].join('\n');
}

async function finalize(run) {
  if (run.finalizing) return;
  run.finalizing = true;
  if (run.deadlineTimer) clearTimeout(run.deadlineTimer);
  let proof;
  try { proof = checkDrain(run); }
  catch (error) {
    proof = { proven: false, problems: [error.message], exact: [], nativeResult: 'UNPROVEN', evidencePath: run.output };
  }
  if (!safePersist(run)) { proof.proven = false; proof.problems.push('Controller durable evidence write failed'); }
  run.record.drain = proof;
  run.record.state = proof.proven ? 'RELEASE' : 'HOLD_UNRELEASED';
  run.finalBody = finalMessage(run, proof, run.record.state);
  await deliverFinal(run);
}

async function deliverFinal(run) {
  run.record.finalPublication = { state: 'PENDING', attempts: (run.record.finalPublication?.attempts ?? 0) + 1 };
  safePersist(run);
  try {
    const result = await queuePublication(run, 'final', run.finalBody);
    const final = run.record.finalPublication;
    final.state = result.delivered ? 'DELIVERED' : 'FAILED';
    final.publisherOrdinal = result.ordinal; final.publisherTerminal = result.terminal;
    final.actualEvent = result.event;
    final.closedAt = result.closedAt;
    final.ackAttemptToPublisherCloseMs = elapsedMs(run);
    const ackTime = Date.parse(run.record.ack?.event?.ts);
    const finalTime = Date.parse(result.event?.ts);
    final.ackEventToPublicationEventMs = Number.isFinite(ackTime) && Number.isFinite(finalTime) ? finalTime - ackTime : null;
    const validationTime = Date.parse(run.record.validation.closedAt);
    final.ackEventToValidationCloseMs = Number.isFinite(ackTime) && Number.isFinite(validationTime) ? validationTime - ackTime : null;
    final.validationCloseToPublicationEventMs = Number.isFinite(validationTime) && Number.isFinite(finalTime) ? finalTime - validationTime : null;
    final.within180Seconds = result.delivered && final.ackEventToPublicationEventMs !== null &&
      final.ackEventToPublicationEventMs >= 0 && final.ackEventToPublicationEventMs <= TOTAL_MS &&
      final.ackAttemptToPublisherCloseMs <= TOTAL_MS;
    safePersist(run);
  } catch (error) {
    run.record.finalPublication.state = 'FAILED';
    run.record.errors.push(`Final publication: ${error.message}`); safePersist(run);
  }
  run.resolveDone(clone(run.record));
}

function deferWithoutLaunch(run, reason) {
  run.finalizing = true;
  if (run.deadlineTimer) clearTimeout(run.deadlineTimer);
  run.record.state = 'DEFER_NO_VALIDATION_LAUNCH';
  run.record.errors.push(reason);
  run.finalBody = finalMessage(run,
    { proven: true, problems: [reason], exact: [], nativeResult: 'UNRUN', evidencePath: run.observerDirectory },
    'RELEASE_NO_LAUNCH');
  return deliverFinal(run);
}

async function ackThenLaunch(run) {
  try {
    const ackText = `ACCEPT NEW ${run.record.grant}; next-owner c-coordinator; ` +
      `observer retained original ChildProcess protocol approved at ${run.record.controllerApprovalEvent}. ` +
      'Pinned preflight passed; controls15/native150 only remaining>=157.5; total180 includes final publication. ' +
      'No historical replay, no extras, no successor self-grant.';
    run.record.ack = await queuePublication(run, 'ack', ackText);
    if (!run.record.ack.delivered) return deferWithoutLaunch(run, 'ACK delivery unconfirmed; validation never launched');
    if (elapsedMs(run) > 7_500) return deferWithoutLaunch(run, 'ACK/pre-launch consumed more than7.5s; no validation launch');
    requireInputs(run); // A changed preflight retires this consumed grant, never launches SDK.
    if (elapsedMs(run) > 7_500) return deferWithoutLaunch(run, 'Post-ACK preflight consumed reserve; no validation launch');
    let out;
    let err;
    try {
      out = fs.openSync(path.join(run.observerDirectory, 'validation.stdout.bin'), 'wx');
      err = fs.openSync(path.join(run.observerDirectory, 'validation.stderr.bin'), 'wx');
    } catch (error) {
      if (out !== undefined) {
        try { fs.closeSync(out); }
        catch (closeError) { run.record.errors.push(`Validation log close: ${closeError.message}`); }
      }
      return deferWithoutLaunch(run, `Validation log open failed: ${error.message}; validation never launched`);
    }
    const args = ['-B', '-X', 'utf8', WRAPPER, '--grant', run.record.grant,
      '--next-owner', 'c-coordinator', '--output', run.output, '--root', ROOT, '--runner', RUNNER];
    let child;
    try { child = cp.spawn(PYTHON, args, { cwd: ROOT, windowsHide: true, shell: false, stdio: ['ignore', out, err] }); }
    catch (error) { fs.closeSync(out); fs.closeSync(err); return deferWithoutLaunch(run, `Spawn failed: ${error.message}`); }
    run.validationChild = child; // Retain ORIGINAL object until and after authoritative close.
    run.record.validation = { pid: child.pid ?? null, terminal: false, exitCode: null, signal: null,
      retainedOriginalChildProcess: true, nativeHandle: 'Node does not expose a numeric HANDLE; none is fabricated',
      args, launchedAt: iso(), errors: [] };
    run.record.state = 'VALIDATION_LIVE';
    child.once('spawn', () => { run.record.validation.pid = child.pid; safePersist(run); });
    child.once('error', error => { run.record.validation.errors.push(error.message); safePersist(run); });
    child.once('close', (code, signal) => {
      try { fs.closeSync(out); } catch (error) { run.record.errors.push(`Validation log close: ${error.message}`); }
      try { fs.closeSync(err); } catch (error) { run.record.errors.push(`Validation log close: ${error.message}`); }
      Object.assign(run.record.validation, { terminal: true, exitCode: code, signal, closedAt: iso(),
        elapsedFromAckAttemptMs: elapsedMs(run) });
      safePersist(run);
      void finalize(run).catch(error => { run.record.errors.push(`Finalize: ${error.message}`); safePersist(run); });
    });
    safePersist(run);
  } catch (error) {
    if (run.validationChild) {
      run.record.state = 'HOLD_UNRELEASED';
      run.record.errors.push(`Post-spawn observer failure: ${error.message}; original child retained`);
      safePersist(run);
      return;
    }
    return deferWithoutLaunch(run, `${error.message}; validation was not launched`);
  }
}

/** Start only after a NEW grant and explicit C approval of the controller role. */
export function startGrantedNative(options) {
  const { grant, outputName, expectedNativeSourceSha256, expectedObserverSha256,
    approvedPersistentController, controllerApprovalEvent } = options ?? {};
  if (process.platform !== 'win32') throw new Error('Prepared Windows-only protocol');
  if (approvedPersistentController !== true || !/^global[1-9][0-9]*$/.test(controllerApprovalEvent ?? '')) {
    throw new Error('C approval of persistent control-plane distinction is still required');
  }
  if (typeof grant !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9-]{5,100}$/.test(grant) ||
      /replace|placeholder|go236|go509|^c580|^go-native-20261026-01$/i.test(grant)) {
    throw new Error('A fresh explicit grant is required; consumed/placeholder grants are refused');
  }
  if (!/^go-native-observed-[0-9]{8}-[a-z0-9-]+$/.test(outputName ?? '') ||
      !/^[a-f0-9]{64}$/.test(expectedNativeSourceSha256 ?? '') ||
      !/^[a-f0-9]{64}$/.test(expectedObserverSha256 ?? '')) throw new Error('Explicit fresh output and source identities are required');
  const self = path.join(RESEARCH, 'fixtures/native_terminal_observer.mjs');
  if (fileHash(self) !== expectedObserverSha256) throw new Error('Observer source differs from reviewed identity');
  if (runs.has(grant)) throw new Error('Grant already retained by this controller');
  const output = path.join(RESEARCH, outputName);
  const observerDirectory = path.join(RESEARCH, `${outputName}.observer`);
  const run = { output, observerDirectory, startedTick: process.hrtime.bigint(), publicationTail: Promise.resolve(),
    publisherLive: false, publisherChildren: [], validationChild: null, finalizing: false, finalBody: null,
    record: { schemaVersion: 1, grant, expectedNativeSourceSha256, expectedObserverSha256,
      adapter: { path: ADAPTER, expectedSha256: ADAPTER_SHA, checks: [] },
      controllerApprovalEvent, controller: { kind: 'persistent Node control-plane infrastructure', terminalClaimed: false },
      state: 'PREFLIGHT', startedAt: iso(), totalMs: TOTAL_MS, validation: { launched: false, terminal: false, pid: null },
      publishers: [], errors: [], successorGrant: 'NOT_GRANTED' } };
  run.record.initialSource = requireInputs(run);
  if (fs.existsSync(observerDirectory)) throw new Error('Observer output already exists');
  const consumed = path.join(RESEARCH, 'native-observer-consumed');
  fs.mkdirSync(consumed, { recursive: true });
  const marker = fs.openSync(path.join(consumed, `${grant.toLowerCase()}.json`), 'wx');
  try { fs.writeFileSync(marker, `${JSON.stringify({ grant, consumedAt: iso(), output })}\n`, 'utf8'); }
  finally { fs.closeSync(marker); }
  fs.mkdirSync(observerDirectory);
  run.startedTick = process.hrtime.bigint(); // Budget begins at ACK attempt, not at source preparation.
  run.record.ackAttemptAt = iso();
  run.done = new Promise(resolve => { run.resolveDone = resolve; });
  runs.set(grant, run);
  persist(run);
  run.deadlineTimer = setTimeout(() => {
    if (run.record.validation.terminal || run.finalizing) return;
    run.record.state = 'HOLD_UNRELEASED';
    run.record.deadline = { reachedAt: iso(), elapsedMs: elapsedMs(run), action: 'retain original processes; no kill or replacement' };
    safePersist(run);
    // Serialized after the original publisher terminal, never a concurrent send.
    void queuePublication(run, 'deadline-hold', `Go ${grant} HOLD_UNRELEASED: total180 deadline reached; ` +
      `validation PID=${run.record.validation.pid}; terminal=${run.record.validation.terminal}. ` +
      'Original objects retained; no timeout kill/reset/restart; successor NOT_GRANTED. ' +
      `Evidence ${observerDirectory}; controller/publisher remain control-plane infrastructure.`)
      .catch(error => { run.record.errors.push(`HOLD publication: ${error.message}`); safePersist(run); });
  }, TOTAL_MS);
  void ackThenLaunch(run).catch(error => { run.record.errors.push(`Observer: ${error.message}`); safePersist(run); });
  return Object.freeze({ grant, output, observerDirectory, done: run.done });
}

export function observerSnapshot(grant) {
  const run = runs.get(grant);
  if (!run) throw new Error('No retained observer for that grant');
  return clone(run.record);
}

/** Explicit publication retry only; this function NEVER launches validation again. */
export function retryFinalPublication(grant) {
  const run = runs.get(grant);
  if (!run || !run.finalBody || run.record.finalPublication?.state !== 'FAILED' || run.publisherLive) {
    throw new Error('Retry requires a failed final publication and an actually terminal original publisher');
  }
  if (run.validationChild && run.record.validation.terminal !== true) throw new Error('Original validation child is still live');
  return deliverFinal(run).then(() => clone(run.record));
}
