import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_code_analyzer.dart';
import 'package:qfli_go/go_debugger.dart';
import 'package:qfli_go/go_ide_tools.dart';
import 'package:qfli_go/go_platform.dart';
import 'package:qfli_go/go_studio_debugger.dart';
import 'package:qfli_go/main.dart' show goProfile;
import 'package:qfli_studio_core/services/code_analysis.dart';
import 'package:qfli_studio_core/services/debug_session.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/tools/offline_tools.dart';

const _operationIds = [
  'analyze-unsaved-utf16',
  'format-and-inspect',
  'shared-debug-break-step-continue',
  'opaque-native-callback',
  'debug-stop-close-reopen',
];

/// Identifies bytes actually loaded by the target process, not a supplied hash.
/// iOS links the runtime statically, so its containing executable is identified.
Future<Map<String, Object?>> loadedGoNativeAuditRuntime() async {
  if (Platform.isIOS) {
    final executable = File(Platform.resolvedExecutable);
    return {
      'kind': 'statically-linked-app-executable',
      'path': executable.path,
      'sha256': _bytesHash(await executable.readAsBytes()),
    };
  }
  final mappings = await File('/proc/self/maps').readAsLines();
  final candidates = mappings
      .where((line) => line.contains('libqfli_go_runtime.so'))
      .map((line) => line.substring(line.indexOf('/')).trim())
      .toSet();
  if (candidates.length != 1) {
    throw StateError('cannot identify exactly one loaded Go runtime: $candidates');
  }
  final path = candidates.single;
  return {
    'kind': 'dynamic-library',
    'path': path,
    'sha256': _bytesHash(await File(path).readAsBytes()),
  };
}

/// Registers actual target-ABI checks in both native and catalog audit entrypoints.
/// These direct API checks do not establish editor decoration or panel rendering.
Future<void> Function() registerGoNativeIdeAcceptance({
  required IntegrationTestWidgetsFlutterBinding binding,
  bool requireEmbeddedRuntime = false,
  Future<Map<String, Object?>> Function()? runtimeIdentity,
  Future<void> Function()? beforeAudit,
}) {
  final embedded = goRuntimeBackendFor(Platform.operatingSystem) ==
      GoRuntimeBackend.embeddedInterpreter;
  Completer<void>? ownershipReleased;
  testWidgets(
    'packaged Go IDE APIs execute through the bundled FFI runtime',
    (tester) async {
      final released = Completer<void>();
      ownershipReleased = released;
      var predecessorsReleased = beforeAudit == null;
      _NativeIdeAudit? audit;
      try {
        final report = await tester.runAsync(() async {
          await beforeAudit?.call();
          predecessorsReleased = true;
          audit = _NativeIdeAudit(
            binding, runtimeIdentity ?? loadedGoNativeAuditRuntime,
          );
          return audit!.run();
        });
        expect(report, isNotNull);
        expect(report!['success'], isTrue,
            reason: 'Go native IDE audit: ${report['reportPath']}');
      } finally {
        // A framework timeout may start another registered test while this
        // body still awaits its native close. Release only from this body's
        // actual finally, and retain the gate if any native cleanup is unsure.
        if (predecessorsReleased &&
            (audit == null || audit!.pendingCleanup.isEmpty)) {
          released.complete();
        }
      }
    },
    skip: !embedded && !requireEmbeddedRuntime
        ? 'Bundled Go IDE acceptance requires an Android/OHOS/iOS target'
        : false,
    timeout: const Timeout(Duration(minutes: 4)),
  );
  return () async {
    final released = ownershipReleased;
    if (released != null) await released.future;
  };
}

class _NativeIdeAudit {
  _NativeIdeAudit(this.binding, this.readRuntimeIdentity);

  final IntegrationTestWidgetsFlutterBinding binding;
  final Future<Map<String, Object?>> Function() readRuntimeIdentity;
  final records = <Map<String, Object?>>[];
  final errors = <String>[];
  final pendingCleanup = <String>[];
  late final Directory root;
  late final String originalCwd;
  Map<String, Object?>? runtime;
  bool blocked = false;

  Future<Map<String, Object?>> run() async {
    originalCwd = Directory.current.path;
    root = await Directory.systemTemp.createTemp('qfli-go-native-ide-');
    final previousProfile = StudioProfile.current;
    StudioProfile.current = goProfile;
    try {
      final embedded = goRuntimeBackendFor(Platform.operatingSystem) ==
          GoRuntimeBackend.embeddedInterpreter;
      if (!embedded) {
        errors.add('Target acceptance refuses the host SDK backend');
        blocked = true;
      }
      await _record(_operationIds[0], _analyze);
      await _record(_operationIds[1], _tools);
      if (embedded) {
        try {
          runtime = await readRuntimeIdentity();
        } catch (error) {
          errors.add('Loaded runtime identity unavailable: $error');
        }
      }
      await _record(_operationIds[2], _sharedDebug);
      await _record(_operationIds[3], _opaqueCallback);
      await _record(_operationIds[4], _stopClose);
      if (embedded) {
        try {
          final after = await readRuntimeIdentity();
          if (runtime != null && (after['path'] != runtime!['path'] ||
              after['sha256'] != runtime!['sha256'])) {
            errors.add('Loaded runtime file identity changed during the audit');
          }
          runtime = after;
        } catch (error) {
          errors.add('Loaded runtime identity unavailable: $error');
        }
      }
      if (Directory.current.path != originalCwd) {
        errors.add('The process working directory changed during the audit');
      }
      if (!blocked && pendingCleanup.isEmpty) {
        try {
          await root.delete(recursive: true);
        } catch (error) {
          errors.add('Fixture root cleanup failed: $error');
        }
      }
      return await _publish(finalReport: true);
    } finally {
      StudioProfile.current = previousProfile;
    }
  }

  Future<void> _record(
    String id,
    Future<void> Function(_AuditCase context, Map<String, Object?> evidence) action,
  ) async {
    final record = <String, Object?>{
      'id': id,
      'status': blocked ? 'not-run' : 'running',
      'passed': false,
      'cleanupComplete': false,
      'evidence': <String, Object?>{},
    };
    records.add(record);
    if (blocked) {
      record['reason'] = 'A prior preflight or cleanup failure retains ownership';
      return;
    }
    final directory = Directory(p.join(root.path, id));
    final context = _AuditCase(directory);
    final started = Stopwatch()..start();
    try {
      await directory.create();
      await action(context, record['evidence']! as Map<String, Object?>);
      record['status'] = 'passed';
      record['passed'] = true;
    } catch (error, stack) {
      record['status'] = 'failed';
      record['error'] = '$error';
      record['stack'] = '$stack';
    } finally {
      record['sessionIds'] = context.leases.map((lease) => lease.id).toList();
      for (final lease in context.leases.reversed) {
        try {
          final closing = lease.release();
          try {
            await closing.timeout(const Duration(seconds: 15));
          } on TimeoutException {
            // Observation expiration is not worker exit. Publish its exact ID,
            // then wait for THIS close future before starting another case.
            final priorStatus = record['status'];
            final priorPassed = record['passed'];
            pendingCleanup.add(lease.id);
            record['status'] = 'cleanup-pending';
            record['passed'] = false;
            record['cleanupObservationTimeout'] = true;
            await _publish(finalReport: false);
            await closing;
            pendingCleanup.remove(lease.id);
            record['status'] = priorStatus;
            record['passed'] = priorPassed;
          }
        } catch (error, stack) {
          record['status'] = 'cleanup-failed';
          record['passed'] = false;
          record['cleanupError'] = '$error';
          record['cleanupStack'] = '$stack';
          if (!pendingCleanup.contains(lease.id)) pendingCleanup.add(lease.id);
          blocked = true;
        }
      }
      if (!blocked && pendingCleanup.isEmpty) {
        try {
          if (await directory.exists()) await directory.delete(recursive: true);
          record['cleanupComplete'] = true;
        } catch (error, stack) {
          record['status'] = 'cleanup-failed';
          record['passed'] = false;
          record['cleanupError'] = '$error';
          record['cleanupStack'] = '$stack';
          blocked = true;
        }
      }
      record['durationMs'] = started.elapsedMilliseconds;
    }
  }

  Future<Map<String, Object?>> _publish({required bool finalReport}) async {
    final ids = records.map((record) => record['id']).toList();
    final complete = ids.length == _operationIds.length &&
        ids.toSet().length == _operationIds.length &&
        ids.toSet().containsAll(_operationIds);
    final reportFile = File(p.join(
      Directory.systemTemp.path,
      'qfli-go-native-ide-device.json',
    ));
    final report = <String, Object?>{
      'schemaVersion': 1,
      'evidenceLevel': Platform.isIOS
          ? 'target-api-statically-linked-app-container'
          : 'packaged-ffi-device-api',
      'deviceExecution': goRuntimeBackendFor(Platform.operatingSystem) ==
          GoRuntimeBackend.embeddedInterpreter,
      'operatingSystem': Platform.operatingSystem,
      'operatingSystemVersion': Platform.operatingSystemVersion,
      'runtime': runtime,
      'requiredOperationIds': _operationIds,
      'records': records,
      'errors': errors,
      'pendingCleanupSessionIds': pendingCleanup,
      'fixtureRoot': root.path,
      'workingDirectoryBefore': originalCwd,
      'workingDirectoryAfter': Directory.current.path,
      'final': finalReport,
      'success': finalReport && complete && runtime != null &&
          errors.isEmpty && pendingCleanup.isEmpty && !blocked &&
          records.every((record) =>
              record['passed'] == true && record['cleanupComplete'] == true),
      'reportPath': reportFile.path,
    };
    try {
      await reportFile.writeAsString(jsonEncode(report), flush: true);
    } catch (error) {
      report['success'] = false;
      report['reportWriteError'] = '$error';
    }
    binding.reportData = {
      ...?binding.reportData,
      'goNativeIdeAudit': report,
    };
    // ignore: avoid_print
    print('QFLI_GO_NATIVE_IDE_AUDIT ${jsonEncode(report)}');
    return report;
  }
}

class _AuditLease {
  _AuditLease(this.id, this.release);
  final String id;
  final Future<void> Function() release;
}

class _AuditCase {
  _AuditCase(this.directory);
  final Directory directory;
  final leases = <_AuditLease>[];
  File get entry => File(p.join(directory.path, 'main.go'));

  GoDebugSession trackNative(GoDebugSession session) {
    leases.add(_AuditLease('go:${session.id}', () async {
      await session.close();
      expect(session.closed, isTrue);
      expect(session.snapshot.terminal, isTrue);
      await _expectReleased(session.id);
      session.dispose();
    }));
    return session;
  }

  DebugSession trackShared(DebugSession session) {
    leases.add(_AuditLease(session.id, () async {
      await session.dispose();
      await session.done;
      expect(session.snapshot.isTerminal, isTrue);
      await _expectReleased(int.parse(session.id.split(':').last));
    }));
    return session;
  }
}

Future<void> _expectReleased(int id) async {
  final response = await const NativeGoDebugBackend().invoke(
    operation: 'poll', sessionId: id,
  );
  expect(response['ok'], isFalse,
      reason: 'Native registry still accepts closed session $id');
}

Future<void> _until(
  FutureOr<bool> Function() predicate, {
  required String reason,
}) async {
  final deadline = DateTime.now().add(const Duration(seconds: 15));
  while (DateTime.now().isBefore(deadline)) {
    if (await predicate()) return;
    await Future<void>.delayed(const Duration(milliseconds: 20));
  }
  throw StateError(reason);
}

Future<GoDebugSnapshot> _nativeUntil(
  GoDebugSession session,
  bool Function(GoDebugSnapshot snapshot) predicate,
) async {
  await _until(() async {
    final snapshot = await session.poll();
    if (snapshot.state == 'failed') {
      throw StateError('Native debugger failed: ${snapshot.stderr}');
    }
    return predicate(snapshot);
  }, reason: 'Session ${session.id} did not reach the required native state');
  return session.snapshot;
}

Future<void> _analyze(_AuditCase context, Map<String, Object?> evidence) async {
  const disk = 'saved text is deliberately different from the open buffer';
  await context.entry.writeAsString(disk);
  final marker = File(p.join(context.directory.path, 'must-not-exist'));
  final valid = 'package main\r\nimport "os"\r\n'
      'var _ = func() int { os.WriteFile(${jsonEncode(marker.path)}, '
      '[]byte("init"), 0600); return 1 }()\r\n'
      'func main(){os.WriteFile(${jsonEncode(marker.path)}, '
      '[]byte("main"), 0600)}\r\n';
  final invalid = '$valid' 'var 中文 = "😀"; var bad = 💥\r\n';
  evidence.addAll({
    'sourceSha256': OfflineDigest.sha256(invalid),
    'validSourceSha256': OfflineDigest.sha256(valid),
    'diskSha256': OfflineDigest.sha256(disk),
  });
  Future<CodeAnalysisResult> analyze(String text, int revision) =>
      GoCodeAnalyzer().analyze(CodeAnalysisRequest(
        projectPath: context.directory.path,
        activeFilePath: context.entry.path,
        language: 'go',
        revision: revision,
        documents: [CodeDocumentSnapshot(
          path: context.entry.path, text: text, revision: revision,
        )],
      ));
  final broken = await analyze(invalid, 41);
  evidence['unavailableReason'] = broken.unavailableReason;
  evidence['diagnostics'] = [for (final diagnostic in broken.diagnostics) {
    'path': diagnostic.filePath,
    'startOffset': diagnostic.startOffset,
    'endOffset': diagnostic.endOffset,
    'message': diagnostic.message,
    'severity': diagnostic.severity.name,
  }];
  expect(broken.unavailableReason, isNull);
  final start = invalid.indexOf('💥');
  expect(broken.diagnostics.any((diagnostic) =>
      diagnostic.filePath == context.entry.path &&
      diagnostic.startOffset == start && diagnostic.endOffset == start + 2 &&
      diagnostic.severity == CodeDiagnosticSeverity.error), isTrue);
  final clean = await analyze(valid, 42);
  expect(clean.unavailableReason, isNull);
  expect(clean.diagnostics, isEmpty);
  expect(await marker.exists(), isFalse);
  expect(await context.entry.readAsString(), disk);
  evidence.addAll({
    'sourceSha256': OfflineDigest.sha256(invalid),
    'validSourceSha256': OfflineDigest.sha256(valid),
    'diskSha256': OfflineDigest.sha256(disk),
    'expectedUtf16Range': [start, start + 2],
    'diagnostics': [for (final diagnostic in broken.diagnostics) {
      'path': diagnostic.filePath,
      'startOffset': diagnostic.startOffset,
      'endOffset': diagnostic.endOffset,
      'message': diagnostic.message,
      'severity': diagnostic.severity.name,
    }],
    'markerAbsent': true,
    'savedBufferUnchanged': true,
    'newRevisionClean': true,
  });
}

Future<void> _tools(_AuditCase context, Map<String, Object?> evidence) async {
  const source = 'package main\nimport "fmt"\n'
      'func main(){fmt.Println("offline")}\n';
  const expected = 'package main\n\nimport "fmt"\n\n'
      'func main() { fmt.Println("offline") }\n';
  await context.entry.writeAsString('untouched saved tool source');
  final tools = createGoIdeTools();
  evidence['sourceSha256'] = OfflineDigest.sha256(source);
  final formatted = await tools.format(source, context.entry.path);
  evidence['formattedSource'] = formatted.formattedSource;
  evidence['formatErrors'] = formatted.errors;
  evidence['unavailableReason'] = formatted.unavailableReason;
  expect(formatted.unavailableReason, isNull);
  expect(formatted.errors, isEmpty);
  expect(formatted.formattedSource, expected);
  const inspected = 'package main\nimport f "fmt"\n'
      'type record struct{ Value int }\n'
      'func (r record) Number() int { return r.Value }\n'
      'func main(){f.Println(record{Value:3}.Number())}\n';
  final result = await tools.inspect(inspected, context.entry.path);
  evidence['inspection'] = result.report;
  evidence['inspectionErrors'] = result.errors;
  expect(result.unavailableReason, isNull);
  expect(result.errors, isEmpty);
  expect(result.report, contains('import f "fmt"'));
  expect(result.report, contains('type record'));
  expect(result.report, contains('method (record) Number'));
  final invalid = await tools.format('package main\nfunc {', context.entry.path);
  expect(invalid.unavailableReason, isNull);
  expect(invalid.formattedSource, isNull);
  expect(invalid.errors, isNotEmpty);
  expect(await context.entry.readAsString(), 'untouched saved tool source');
  evidence.addAll({
    'sourceSha256': OfflineDigest.sha256(source),
    'formattedSource': formatted.formattedSource,
    'expectedFormattedSource': expected,
    'inspectedSourceSha256': OfflineDigest.sha256(inspected),
    'inspection': result.report,
    'invalidSourceErrors': invalid.errors,
    'savedBufferUnchanged': true,
  });
}

Future<void> _sharedDebug(
  _AuditCase context, Map<String, Object?> evidence,
) async {
  final marker = File(p.join(context.directory.path, 'continued.marker'));
  final source = 'package main\nimport ("fmt"; "os")\nfunc main() {\n'
      ' value := 42\n value += 1\n'
      ' _ = os.WriteFile(${jsonEncode(marker.path)}, []byte("continued"), 0600)\n'
      ' fmt.Println(value)\n}\n';
  await context.entry.writeAsString(source);
  evidence['sourceSha256'] = OfflineDigest.sha256(source);
  final session = context.trackShared(await GoStudioDebugger(
    pollInterval: const Duration(milliseconds: 10),
  ).launch(DebugLaunchRequest(
    projectPath: context.directory.path,
    entryFilePath: context.entry.path,
    language: 'go', documents: const [], stopOnEntry: true,
    breakpoints: [DebugBreakpoint(filePath: context.entry.path, line: 5)],
  )));
  evidence['sessionId'] = session.id;
  await _until(() => session.snapshot.phase == DebugPhase.paused,
      reason: 'Shared session did not pause on entry');
  await session.command(DebugCommand.resume,
      pauseToken: session.snapshot.pauseToken);
  await _until(() => session.snapshot.phase == DebugPhase.paused &&
      session.snapshot.frames.firstOrNull?.location?.line == 5,
      reason: 'Shared breakpoint did not pause at the marked statement');
  final paused = session.snapshot;
  evidence['pausedSnapshot'] = _sharedEvidence(paused);
  final owner = paused.threads.singleWhere((thread) => thread.isPaused);
  expect(paused.breakpoints.single.status, DebugBreakpointStatus.verified);
  expect(paused.frames.first.location!.filePath,
      await context.entry.resolveSymbolicLinks());
  expect(paused.frames.first.locals.any((variable) =>
      variable.name == 'value' && variable.value == '42'), isTrue);
  expect(await marker.exists(), isFalse);
  expect(paused.stdout, isEmpty);
  await session.command(DebugCommand.stepOver,
      pauseToken: paused.pauseToken, threadId: owner.id);
  await _until(() => session.snapshot.phase == DebugPhase.paused &&
      session.snapshot.pauseToken != paused.pauseToken &&
      session.snapshot.frames.firstOrNull?.location?.line == 6,
      reason: 'Shared stepOver did not reach the next source statement');
  final stepped = session.snapshot;
  evidence['steppedSnapshot'] = _sharedEvidence(stepped);
  final steppedOwner = stepped.threads.singleWhere((thread) => thread.isPaused);
  expect(steppedOwner.id.split(':').last, owner.id.split(':').last);
  expect(stepped.frames.first.locals.any((variable) =>
      variable.name == 'value' && variable.value == '43'), isTrue);
  expect(await marker.exists(), isFalse);
  await session.command(DebugCommand.resume,
      pauseToken: stepped.pauseToken, threadId: steppedOwner.id);
  await session.done.timeout(const Duration(seconds: 15));
  evidence['terminalSnapshot'] = _sharedEvidence(session.snapshot);
  expect(session.snapshot.phase, DebugPhase.terminated);
  expect(session.snapshot.stdout, '43\n');
  expect(await marker.readAsString(), 'continued');
  await _expectReleased(int.parse(session.id.split(':').last));
  evidence.addAll({
    'sourceSha256': OfflineDigest.sha256(source),
    'sessionId': session.id,
    'ownerId': owner.id,
    'steppedOwnerId': steppedOwner.id,
    'pausedLine': 5, 'steppedLine': 6,
    'pausedValue': '42', 'steppedValue': '43',
    'markerAbsentBeforeContinue': true,
    'markerAfterContinue': await marker.readAsString(),
    'stdout': session.snapshot.stdout,
    'stderr': session.snapshot.stderr,
    'phase': session.snapshot.phase.name,
    'registryReleased': true,
  });
}

Future<void> _opaqueCallback(
  _AuditCase context, Map<String, Object?> evidence,
) async {
  const source = 'package main\nimport ("fmt"; "sync")\nfunc main() {\n'
      ' pool := sync.Pool{New: func() interface{} {\n'
      '  value := 42\n  fmt.Println("callback", value)\n  return value\n }}\n'
      ' fmt.Println("result", pool.Get())\n}\n';
  await context.entry.writeAsString(source);
  evidence['sourceSha256'] = OfflineDigest.sha256(source);
  final session = context.trackNative(await GoDebugger().start(
    projectPath: context.directory.path, entryFile: context.entry.path,
    breakpoints: const {'main.go': [6]},
  ));
  evidence['sessionId'] = session.id;
  final entry = await _nativeUntil(session, (snapshot) => snapshot.state == 'paused');
  final mainId = entry.threads.singleWhere((thread) => thread.paused).id;
  await session.command(GoDebugCommand.continueExecution, goroutineId: mainId);
  final paused = await _nativeUntil(session, (snapshot) =>
      snapshot.threads.any((thread) => thread.paused &&
          thread.kind == GoDebugExecutionKind.nativeCallback));
  evidence['pausedSnapshot'] = _nativeEvidence(paused);
  final owner = paused.threads.singleWhere((thread) =>
      thread.paused && thread.kind == GoDebugExecutionKind.nativeCallback);
  final stopped = paused.stoppedEvent!;
  expect(owner.id, isNot(mainId));
  expect(stopped.goroutineId, owner.id);
  expect(stopped.kind, GoDebugExecutionKind.nativeCallback);
  expect(stopped.opaqueNativeBoundary, isTrue);
  expect(stopped.frames, hasLength(1));
  expect(stopped.frames.single.line, 6);
  expect(stopped.frames.single.opaqueNativeBoundary, isTrue);
  expect(stopped.frames.single.variables, isEmpty);
  expect(stopped.frames.single.localsUnavailableReason,
      'Opaque native callback may capture values outside this stack; locals were not read');
  expect(paused.stdout, isEmpty);
  await session.command(GoDebugCommand.stepOver, goroutineId: owner.id);
  final stepped = await _nativeUntil(session, (snapshot) =>
      snapshot.sequence > paused.sequence && snapshot.state == 'paused' &&
      snapshot.stoppedEvent?.frames.firstOrNull?.line == 7);
  evidence['steppedSnapshot'] = _nativeEvidence(stepped);
  expect(stepped.stoppedEvent!.goroutineId, owner.id);
  await session.command(GoDebugCommand.continueExecution, goroutineId: owner.id);
  final terminal = await _nativeUntil(session, (snapshot) => snapshot.terminal);
  evidence['terminalSnapshot'] = _nativeEvidence(terminal);
  expect(terminal.state, 'terminated');
  expect(terminal.stdout, 'callback 42\nresult 42\n');
  expect(terminal.threads, isEmpty);
  expect(terminal.events.any((event) =>
      event.goroutineId == owner.id && event.opaqueNativeBoundary &&
      event.kind == GoDebugExecutionKind.nativeCallback &&
      event.frames.any((frame) => frame.opaqueNativeBoundary)), isTrue);
  evidence.addAll({
    'sourceSha256': OfflineDigest.sha256(source),
    'sessionId': session.id, 'mainOwnerId': mainId, 'callbackOwnerId': owner.id,
    'kind': stopped.kind.name,
    'opaqueNativeBoundary': stopped.opaqueNativeBoundary,
    'frameNames': stopped.frames.map((frame) => frame.name).toList(),
    'pausedLine': stopped.frames.single.line,
    'steppedLine': stepped.stoppedEvent!.frames.single.line,
    'localsUnavailableReason': stopped.frames.single.localsUnavailableReason,
    'stdout': terminal.stdout, 'stderr': terminal.stderr,
    'terminalState': terminal.state,
    'metadataRetainedAfterOwnerExit': true,
  });
}

Future<void> _stopClose(_AuditCase context, Map<String, Object?> evidence) async {
  final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
  final requestReady = Completer<HttpRequest>();
  final subscription = server.listen((request) {
    if (!requestReady.isCompleted) {
      requestReady.complete(request);
    } else {
      request.response.statusCode = HttpStatus.serviceUnavailable;
      unawaited(request.response.close());
    }
  });
  HttpRequest? heldRequest;
  Future<void>? responseClosed;
  try {
    final url = 'http://127.0.0.1:${server.port}/held';
    final source = 'package main\nimport "net/http"\nfunc main() {\n'
        ' response, err := http.Get(${jsonEncode(url)})\n'
        ' if err != nil { panic(err) }\n response.Body.Close()\n}\n';
    await context.entry.writeAsString(source);
    evidence['sourceSha256'] = OfflineDigest.sha256(source);
    evidence['loopbackEndpoint'] = url;
    final session = context.trackNative(await GoDebugger().start(
      projectPath: context.directory.path, entryFile: context.entry.path,
    ));
    evidence['sessionId'] = session.id;
    await _nativeUntil(session, (snapshot) => snapshot.state == 'paused');
    await session.command(GoDebugCommand.continueExecution);
    heldRequest = await requestReady.future.timeout(const Duration(seconds: 15));
    evidence['requestObservedBeforeClose'] = true;
    var closeCompleted = false;
    final closing = session.close().then((_) => closeCompleted = true);
    await Future<void>.delayed(const Duration(milliseconds: 100));
    evidence['closeCompletedWhileNativeCallHeld'] = closeCompleted;
    evidence['snapshotWhileNativeCallHeld'] = _nativeEvidence(session.snapshot);
    expect(closeCompleted, isFalse,
        reason: 'Close returned while the compiled HTTP call was still held');
    expect(session.closed, isFalse);
    expect(session.snapshot.terminal, isFalse);
    heldRequest.response.write('released');
    responseClosed = heldRequest.response.close();
    await responseClosed;
    await closing.timeout(const Duration(seconds: 15));
    expect(session.closed, isTrue);
    expect(session.snapshot.terminal, isTrue);
    await _expectReleased(session.id);
    const freshSource = 'package main\nimport "fmt"\n'
        'func main(){fmt.Println("fresh session")}\n';
    await context.entry.writeAsString(freshSource);
    final fresh = context.trackNative(await GoDebugger().start(
      projectPath: context.directory.path, entryFile: context.entry.path,
    ));
    expect(fresh.id, isNot(session.id));
    await _nativeUntil(fresh, (snapshot) => snapshot.state == 'paused');
    await fresh.command(GoDebugCommand.continueExecution);
    final finished = await _nativeUntil(fresh, (snapshot) => snapshot.terminal);
    evidence['freshTerminalSnapshot'] = _nativeEvidence(finished);
    expect(finished.state, 'terminated');
    expect(finished.stdout, 'fresh session\n');
    evidence.addAll({
      'sourceSha256': OfflineDigest.sha256(source),
      'sessionId': session.id,
      'loopbackEndpoint': url,
      'requestObservedBeforeClose': true,
      'closePendingWhileNativeCallHeld': true,
      'terminalAfterFixtureRelease': session.snapshot.terminal,
      'registryReleased': true,
      'freshSessionId': fresh.id,
      'freshSourceSha256': OfflineDigest.sha256(freshSource),
      'freshStdout': finished.stdout,
    });
  } finally {
    // Release this fixture's native call before the outer lease cleanup waits.
    if (heldRequest != null && responseClosed == null) {
      heldRequest.response.write('fixture cleanup');
      await heldRequest.response.close();
    }
    await subscription.cancel();
    await server.close(force: true);
  }
}

String _bytesHash(List<int> bytes) => OfflineDigest.sha256Bytes(bytes)
    .map((byte) => byte.toRadixString(16).padLeft(2, '0')).join();

Map<String, Object?> _sharedEvidence(DebugSnapshot snapshot) => {
  'sessionId': snapshot.sessionId, 'revision': snapshot.revision,
  'phase': snapshot.phase.name, 'stdout': snapshot.stdout,
  'stderr': snapshot.stderr, 'message': snapshot.message,
  'frames': [for (final frame in snapshot.frames) {
    'threadId': frame.threadId, 'name': frame.name,
    'file': frame.location?.filePath, 'line': frame.location?.line,
    'localsUnavailableReason': frame.localsUnavailableReason,
    'locals': [for (final variable in frame.locals) {
      'name': variable.name, 'type': variable.type, 'value': variable.value,
    }],
  }],
};

Map<String, Object?> _nativeEvidence(GoDebugSnapshot snapshot) => {
  'sessionId': snapshot.sessionId, 'sequence': snapshot.sequence,
  'state': snapshot.state, 'stdout': snapshot.stdout, 'stderr': snapshot.stderr,
  'threads': [for (final thread in snapshot.threads) {
    'id': thread.id, 'kind': thread.kind.name, 'paused': thread.paused,
  }],
  'stoppedEvent': snapshot.stoppedEvent == null ? null : {
    'reason': snapshot.stoppedEvent!.reason,
    'ownerId': snapshot.stoppedEvent!.goroutineId,
    'kind': snapshot.stoppedEvent!.kind.name,
    'opaqueNativeBoundary': snapshot.stoppedEvent!.opaqueNativeBoundary,
    'frames': [for (final frame in snapshot.stoppedEvent!.frames) {
      'name': frame.name, 'file': frame.file, 'line': frame.line,
      'opaqueNativeBoundary': frame.opaqueNativeBoundary,
      'localsUnavailableReason': frame.localsUnavailableReason,
    }],
  },
};
