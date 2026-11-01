import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_debugger.dart';
import 'package:qfli_go/go_studio_debugger.dart';
import 'package:qfli_studio_core/services/code_analysis.dart';
import 'package:qfli_studio_core/services/debug_session.dart';

void main() {
  late Directory root;
  late File entry;
  late _Backend backend;
  late GoStudioDebugger debugger;
  setUp(() {
    root = Directory.systemTemp.createTempSync('go_studio_debug_');
    entry = File(p.join(root.path, 'main.go'))
      ..writeAsStringSync(
        'package main\nfunc main(){\n value:=42\n println(value)\n}\n',
      );
    backend = _Backend();
    debugger = GoStudioDebugger(
      debugger: GoDebugger(backend: backend),
      pollInterval: const Duration(milliseconds: 2),
    );
  });
  tearDown(() => root.deleteSync(recursive: true));

  DebugLaunchRequest request({
    String language = 'go',
    String? project,
    String? file,
    List<CodeDocumentSnapshot> documents = const [],
    List<DebugBreakpoint> breakpoints = const [],
    bool stopOnEntry = true,
  }) => DebugLaunchRequest(
    projectPath: project ?? root.path,
    entryFilePath: file ?? entry.path,
    language: language,
    documents: documents,
    breakpoints: breakpoints,
    stopOnEntry: stopOnEntry,
  );

  test(
    'declares only implemented capabilities and validates before execution',
    () async {
      expect(
        debugger.capabilities.breakpointUpdate,
        DebugBreakpointUpdate.launchOnly,
      );
      expect(debugger.capabilities.outputDelivery, DebugOutputDelivery.live);
      expect(debugger.capabilities.supportsDocumentSnapshots, isFalse);
      expect(debugger.supportsLanguage('python'), isFalse);
      final outside = File(
        p.join(root.parent.path, '${p.basename(root.path)}_outside.go'),
      )..writeAsStringSync('package main');
      addTearDown(() => outside.deleteSync());
      for (final invalid in [
        request(language: 'python'),
        request(project: 'relative'),
        request(file: 'main.go'),
        request(file: outside.path),
        request(file: p.join(root.path, 'missing.go')),
        request(
          documents: [
            CodeDocumentSnapshot(path: entry.path, text: 'dirty', revision: 1),
          ],
        ),
        request(breakpoints: [DebugBreakpoint(filePath: entry.path, line: 99)]),
        request(
          breakpoints: [
            DebugBreakpoint(filePath: entry.path, line: 4),
            DebugBreakpoint(filePath: entry.path, line: 4),
          ],
        ),
      ]) {
        await expectLater(debugger.launch(invalid), throwsA(anything));
      }
      expect(backend.operations, isEmpty);
    },
  );

  test('rejects physical symlink escapes before execution', () async {
    final outside = Directory.systemTemp.createTempSync('go_debug_external_');
    addTearDown(() => outside.deleteSync(recursive: true));
    final foreign = File(p.join(outside.path, 'foreign.go'))
      ..writeAsStringSync('package main');
    final link = Link(p.join(root.path, 'alias.go'));
    try {
      await link.create(foreign.path);
    } on FileSystemException {
      markTestSkipped('This host cannot create filesystem symlinks');
      return;
    }
    await expectLater(
      debugger.launch(request(file: link.path)),
      throwsA(isA<GoDebugException>()),
    );
    expect(backend.operations, isEmpty);
  });

  test(
    'maps real source, locals and breakpoints and rejects stale commands without dispatch',
    () async {
      final session = await debugger.launch(
        request(breakpoints: [DebugBreakpoint(filePath: entry.path, line: 4)]),
      );
      addTearDown(session.dispose);
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      final snapshot = session.snapshot;
      expect(
        snapshot.frames.first.location!.filePath,
        entry.resolveSymbolicLinksSync(),
      );
      expect(snapshot.frames.first.locals.single.value, '42');
      expect(
        snapshot.breakpoints.single.status,
        DebugBreakpointStatus.verified,
      );
      expect(snapshot.exitCode, isNull);
      final token = snapshot.pauseToken!;
      for (final invalid in [
        const DebugPauseToken(sessionId: 'other', generation: 1),
        DebugPauseToken(
          sessionId: session.id,
          generation: token.generation + 1,
        ),
      ]) {
        await expectLater(
          session.command(DebugCommand.resume, pauseToken: invalid),
          throwsA(isA<GoDebugException>()),
        );
      }
      await expectLater(
        session.command(
          DebugCommand.resume,
          pauseToken: token,
          threadId: 'unknown',
        ),
        throwsA(isA<GoDebugException>()),
      );
      await expectLater(
        session.setBreakpoints([]),
        throwsA(isA<GoDebugException>()),
      );
      expect(backend.commands, isEmpty);
      await session.command(
        DebugCommand.stepOver,
        pauseToken: token,
        threadId: snapshot.threads.single.id,
      );
      expect(backend.commands, ['stepOver']);
      expect(session.snapshot.pauseToken, isNot(token));
      await expectLater(
        session.command(DebugCommand.resume, pauseToken: token),
        throwsA(isA<GoDebugException>()),
      );
      expect(backend.commands, ['stepOver']);
      await session.command(
        DebugCommand.resume,
        pauseToken: session.snapshot.pauseToken,
      );
      expect(session.snapshot.phase, DebugPhase.running);
      expect(session.snapshot.frames, isEmpty);
      expect(session.snapshot.pauseToken, isNull);
      await session.command(DebugCommand.pause);
      expect(backend.commands.last, 'pause');
    },
  );

  test(
    'callback owners keep native command IDs and explicit locals reasons',
    () async {
      backend.kind = 'nativeCallback';
      backend.opaqueNativeBoundary = true;
      backend.localsUnavailable = 'External callback locals are unavailable';
      final session = await debugger.launch(request());
      addTearDown(session.dispose);
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      final snapshot = session.snapshot;
      expect(snapshot.threads.single.name, 'Native callback 1');
      expect(snapshot.frames.single.locals, isEmpty);
      expect(
        snapshot.frames.single.localsUnavailableReason,
        'External callback locals are unavailable',
      );
      expect(
        snapshot.console,
        contains(
          'Native callback 1: Call stack ends at an opaque native callback boundary',
        ),
      );
      await session.command(
        DebugCommand.stepOver,
        pauseToken: snapshot.pauseToken,
        threadId: snapshot.threads.single.id,
      );
      expect(backend.commandRequests.single['goroutineId'], 1);
      expect(backend.commands, ['stepOver']);
      expect(session.snapshot.pauseToken, isNot(snapshot.pauseToken));
    },
  );

  test(
    'stopped-event fallback preserves callback kind and opaque boundary',
    () async {
      backend.kind = 'nativeCallback';
      backend.includeThreads = false;
      backend.opaqueNativeBoundary = true;
      final session = await debugger.launch(request());
      addTearDown(session.dispose);
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      expect(session.snapshot.threads.single.name, 'Native callback 1');
      expect(
        session.snapshot.frames.single.localsUnavailableReason,
        contains('opaque native callback boundary'),
      );
      expect(session.snapshot.frames.single.locals, isEmpty);
    },
  );

  test('frame boundary alone explains unavailable callback locals', () async {
    backend.kind = 'nativeCallback';
    backend.frameOpaqueNativeBoundary = true;
    final session = await debugger.launch(request());
    addTearDown(session.dispose);
    await _until(() => session.snapshot.phase == DebugPhase.paused);
    expect(
      session.snapshot.frames.single.localsUnavailableReason,
      contains('opaque native callback boundary'),
    );
    expect(session.snapshot.console, contains('external caller unavailable'));
  });

  test('kind-only updates publish labels without inventing a boundary', () async {
    final session = await debugger.launch(request());
    addTearDown(session.dispose);
    await _until(() => session.snapshot.phase == DebugPhase.paused);
    final before = session.snapshot;
    expect(before.threads.single.name, 'Goroutine 1');
    backend.kind = 'nativeCallback';
    await _until(
      () => session.snapshot.threads.single.name == 'Native callback 1',
    );
    expect(session.snapshot.revision, greaterThan(before.revision));
    expect(session.snapshot.pauseToken, before.pauseToken);
    expect(session.snapshot.frames.single.locals.single.value, '42');
    expect(session.snapshot.frames.single.localsUnavailableReason, isNull);
  });

  test(
    'output-only updates increase revisions and replace complete rolling output',
    () async {
      final session = await debugger.launch(request());
      addTearDown(session.dispose);
      final updates = <DebugSnapshot>[];
      final subscription = session.updates.listen(updates.add);
      addTearDown(subscription.cancel);
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      final before = session.snapshot;
      backend.stdout = 'first\n';
      await _until(() => session.snapshot.stdout == 'first\n');
      expect(session.snapshot.revision, greaterThan(before.revision));
      expect(session.snapshot.pauseToken, before.pauseToken);
      backend.stdout = '中😀' * 40000;
      backend.outputTruncated = true;
      await _until(() => session.snapshot.stdoutTruncated);
      expect(session.snapshot.stdout.runes.length, 65536);
      expect(session.snapshot.stdout.contains('first'), isFalse);
      expect(session.snapshot.stdout.contains('\uFFFD'), isFalse);
      expect(updates, isNotEmpty);
      expect(() => session.snapshot.frames.clear(), throwsUnsupportedError);
    },
  );

  test(
    'automatic entry resume preserves the first actual breakpoint pause',
    () async {
      final session = await debugger.launch(request(stopOnEntry: false));
      addTearDown(session.dispose);
      await _until(() => backend.commands.contains('continue'));
      backend.reason = 'breakpoint';
      backend.state = 'paused';
      backend.sequence++;
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      expect(
        backend.commands.where((command) => command == 'continue'),
        hasLength(1),
      );
      expect(session.snapshot.frames.single.location!.line, 4);
    },
  );

  test(
    'resuming one goroutine invalidates its token while another stays paused',
    () async {
      backend.secondPaused = true;
      backend.sequence = 2;
      final session = await debugger.launch(request());
      addTearDown(session.dispose);
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      final token = session.snapshot.pauseToken!;
      final thread = session.snapshot.threads.first.id;
      await session.command(
        DebugCommand.resume,
        pauseToken: token,
        threadId: thread,
      );
      expect(session.snapshot.phase, DebugPhase.paused);
      expect(session.snapshot.pauseToken, isNot(token));
      expect(
        session.snapshot.threads.where((thread) => thread.isPaused),
        hasLength(1),
      );
      await expectLater(
        session.command(DebugCommand.stepInto, pauseToken: token),
        throwsA(isA<GoDebugException>()),
      );
      expect(backend.commands, ['continue']);
    },
  );

  test(
    'stop, done and disposal await actual termination and native cleanup',
    () async {
      backend.holdWorker = true;
      backend.closeGate = Completer<void>();
      final session = await debugger.launch(request());
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      var stopped = false,
          finished = false,
          disposed = false,
          streamClosed = false;
      session.done.then((_) => finished = true);
      session.updates.listen((_) {}, onDone: () => streamClosed = true);
      final stop = session.stop().then((_) => stopped = true);
      final dispose = session.dispose().then((_) => disposed = true);
      await _until(() => backend.commands.contains('stop'));
      await Future<void>.delayed(const Duration(milliseconds: 40));
      expect(session.snapshot.phase, DebugPhase.stopping);
      expect([
        stopped,
        finished,
        disposed,
        streamClosed,
      ], everyElement(isFalse));
      expect(
        backend.operations.where((operation) => operation == 'close'),
        isEmpty,
      );
      backend.workerExited = true;
      await _until(() => backend.operations.contains('close'));
      expect([
        stopped,
        finished,
        disposed,
        streamClosed,
      ], everyElement(isFalse));
      backend.closeGate!.complete();
      await Future.wait([stop, dispose, session.done]);
      expect([stopped, finished, disposed, streamClosed], everyElement(isTrue));
      expect(
        backend.operations.where((operation) => operation == 'close'),
        hasLength(1),
      );
      await session.stop();
      await session.dispose();
    },
  );

  test(
    'unknown native sources are not fabricated and unavailable locals stay explicit',
    () async {
      backend.frameFile = '../outside.go';
      backend.localsUnavailable = 'Other workers may mutate shared values';
      final session = await debugger.launch(request());
      addTearDown(session.dispose);
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      final frame = session.snapshot.frames.single;
      expect(frame.location, isNull);
      expect(frame.locals, isEmpty);
      expect(frame.localsUnavailableReason, contains('Other workers'));
    },
  );

  test(
    'failed workers preserve the real message and unknown exit status after cleanup',
    () async {
      final session = await debugger.launch(request());
      addTearDown(session.dispose);
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      backend.state = 'failed';
      backend.message = 'panic: useful error';
      backend.sequence++;
      await session.done;
      expect(session.snapshot.phase, DebugPhase.failed);
      expect(session.snapshot.message, 'panic: useful error');
      expect(session.snapshot.exitCode, isNull);
    },
  );

  test(
    'real shared adapter controls an opaque native callback and retains its boundary',
    () async {
      entry.writeAsStringSync('''package main
import ("fmt"; "sync")
func main() {
 pool := sync.Pool{New: func() interface{} {
  value := 42
  fmt.Println("callback", value)
  return value
 }}
 fmt.Println("result", pool.Get())
}
''');
      final session = await GoStudioDebugger(
        pollInterval: const Duration(milliseconds: 10),
      ).launch(
        request(
          breakpoints: [DebugBreakpoint(filePath: entry.path, line: 6)],
        ),
      );
      addTearDown(session.dispose);
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      await session.command(
        DebugCommand.resume,
        pauseToken: session.snapshot.pauseToken,
      );
      await _until(
        () => session.snapshot.threads.any(
          (thread) => thread.isPaused && thread.name.startsWith('Native callback '),
        ),
      );
      final callback = session.snapshot;
      final owner = callback.threads.singleWhere((thread) => thread.isPaused);
      expect(int.parse(owner.id.split(':').last), isNot(1));
      expect(callback.frames, hasLength(1));
      expect(callback.frames.single.threadId, owner.id);
      expect(callback.frames.single.location!.line, 6);
      expect(callback.frames.single.locals, isEmpty);
      expect(
        callback.frames.single.localsUnavailableReason,
        'Opaque native callback may capture values outside this stack; locals were not read',
      );
      expect(callback.console, contains('external caller unavailable'));
      expect(callback.stdout, isEmpty);
      await session.command(
        DebugCommand.stepOver,
        pauseToken: callback.pauseToken,
        threadId: owner.id,
      );
      await _until(
        () => session.snapshot.phase == DebugPhase.paused &&
            session.snapshot.pauseToken != callback.pauseToken &&
            session.snapshot.frames.single.location!.line != 6,
      );
      final stepped = session.snapshot;
      final steppedOwner = stepped.threads.singleWhere((thread) => thread.isPaused);
      expect(steppedOwner.id.split(':').last, owner.id.split(':').last);
      expect(steppedOwner.name, owner.name);
      expect(stepped.frames, hasLength(1));
      await session.command(
        DebugCommand.resume,
        pauseToken: stepped.pauseToken,
        threadId: steppedOwner.id,
      );
      await session.done;
      expect(session.snapshot.phase, DebugPhase.terminated);
      expect(session.snapshot.stdout, 'callback 42\nresult 42\n');
      expect(session.snapshot.threads, isEmpty);
      expect(session.snapshot.console, contains('${owner.name}: Call stack ends'));
      final response = await const NativeGoDebugBackend().invoke(
        operation: 'poll',
        sessionId: int.parse(session.id.split(':').last),
      );
      expect(response['ok'], isFalse);
    },
    skip: Platform.environment['QFLI_GO_RUNTIME_LIBRARY'] == null
        ? 'Set QFLI_GO_RUNTIME_LIBRARY to test the rebuilt native callback ABI'
        : false,
  );

  test(
    'real shared adapter pauses, inspects disk sources and releases native ownership',
    () async {
      entry.writeAsStringSync(
        'package main\nimport "fmt"\nfunc main(){\n value:=42\n fmt.Println(value)\n}\n',
      );
      final session =
          await GoStudioDebugger(
            pollInterval: const Duration(milliseconds: 10),
          ).launch(
            request(
              breakpoints: [DebugBreakpoint(filePath: entry.path, line: 5)],
            ),
          );
      addTearDown(session.dispose);
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      await session.command(
        DebugCommand.resume,
        pauseToken: session.snapshot.pauseToken,
      );
      await _until(() => session.snapshot.phase == DebugPhase.paused);
      expect(
        session.snapshot.frames.first.location!.filePath,
        entry.resolveSymbolicLinksSync(),
      );
      expect(session.snapshot.frames.first.location!.line, 5);
      expect(
        session.snapshot.frames.first.locals.any(
          (variable) => variable.name == 'value' && variable.value == '42',
        ),
        isTrue,
      );
      await session.command(
        DebugCommand.resume,
        pauseToken: session.snapshot.pauseToken,
      );
      await session.done;
      expect(session.snapshot.phase, DebugPhase.terminated);
      expect(session.snapshot.stdout.trim(), '42');
      final nativeId = int.parse(session.id.split(':').last);
      final response = await const NativeGoDebugBackend().invoke(
        operation: 'poll',
        sessionId: nativeId,
      );
      expect(response['ok'], isFalse);
    },
    skip: Platform.environment['QFLI_GO_RUNTIME_LIBRARY'] == null
        ? 'Set QFLI_GO_RUNTIME_LIBRARY to test the rebuilt native artifact'
        : false,
  );
}

Future<void> _until(bool Function() predicate) async {
  final deadline = DateTime.now().add(const Duration(seconds: 3));
  while (!predicate() && DateTime.now().isBefore(deadline)) {
    await Future<void>.delayed(const Duration(milliseconds: 2));
  }
  expect(
    predicate(),
    isTrue,
    reason: 'Debugger condition did not become observable',
  );
}

final class _Backend implements GoDebugBackend {
  final operations = <String>[];
  final commands = <String>[];
  final commandRequests = <Map<String, Object?>>[];
  String state = 'paused',
      reason = 'entry',
      stdout = '',
      message = '',
      frameFile = 'qfli-project/main.go',
      localsUnavailable = '';
  String? kind;
  int sequence = 1;
  bool outputTruncated = false, holdWorker = false, workerExited = false;
  bool secondPaused = false, firstResumed = false;
  bool includeThreads = true;
  bool opaqueNativeBoundary = false, frameOpaqueNativeBoundary = false;
  Completer<void>? closeGate;

  @override
  Future<Map<String, dynamic>> invoke({
    required String operation,
    required int sessionId,
    Map<String, Object?> request = const {},
    int afterSequence = 0,
  }) async {
    operations.add(operation);
    if (operation == 'command') {
      final command = request['command'] as String;
      commands.add(command);
      commandRequests.add(Map<String, Object?>.of(request));
      switch (command) {
        case 'stop':
          state = holdWorker && !workerExited ? 'stopping' : 'terminated';
        case 'continue':
          firstResumed = secondPaused;
          state = secondPaused ? 'paused' : 'running';
        case 'pause':
          state = 'paused';
          reason = 'pause';
          sequence++;
        default:
          state = 'paused';
          reason = command;
          sequence++;
      }
    }
    if (operation == 'poll' && state == 'stopping' && workerExited) {
      state = 'terminated';
    }
    if (operation == 'close') {
      await closeGate?.future;
      state = 'closed';
    }
    return {
      'ok': true,
      'sessionId': sessionId,
      'state': state,
      'sequence': sequence,
      'stdout': stdout,
      'stderr': '',
      'outputTruncated': outputTruncated,
      'threads': [
        if (includeThreads)
          {
            'id': 1,
            'paused': state == 'paused' && !firstResumed,
            if (kind != null) 'kind': kind,
          },
        if (includeThreads && secondPaused)
          {'id': 2, 'paused': state == 'paused'},
      ],
      'breakpoints': [
        {'file': 'main.go', 'line': 4, 'actualLine': 4, 'valid': true},
      ],
      'events': [
        {
          'sequence': secondPaused ? sequence - 1 : sequence,
          'reason': reason,
          'goroutineId': 1,
          if (kind != null) 'kind': kind,
          if (opaqueNativeBoundary) 'opaqueNativeBoundary': true,
          'message': message,
          'frames': [
            {
              'name': 'main',
              'file': frameFile,
              'line': 4,
              'column': 2,
              'localsUnavailableReason': localsUnavailable,
              if (frameOpaqueNativeBoundary) 'opaqueNativeBoundary': true,
              'variables': localsUnavailable.isEmpty &&
                      !opaqueNativeBoundary &&
                      !frameOpaqueNativeBoundary
                  ? [
                      {'name': 'value', 'type': 'int', 'value': '42'},
                    ]
                  : [],
            },
          ],
        },
        if (secondPaused)
          {
            'sequence': sequence,
            'reason': 'breakpoint',
            'goroutineId': 2,
            'frames': [
              {
                'name': 'worker',
                'file': frameFile,
                'line': 3,
                'column': 1,
                'variables': [],
              },
            ],
          },
      ],
    };
  }
}
