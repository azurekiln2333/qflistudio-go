import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_debugger.dart';

void main() {
  test('legacy debugger payloads default execution metadata', () {
    final snapshot = GoDebugSnapshot.fromJson({
      'ok': true,
      'sessionId': 1,
      'state': 'paused',
      'threads': [
        {'id': 1, 'paused': true},
      ],
      'events': [
        {
          'sequence': 1,
          'reason': 'breakpoint',
          'goroutineId': 1,
          'frames': [
            {'name': 'main', 'file': 'main.go', 'line': 4, 'column': 2},
          ],
        },
      ],
    }, expectedId: 1);
    expect(snapshot.threads.single.kind, GoDebugExecutionKind.goroutine);
    final event = snapshot.events.single;
    expect(event.kind, GoDebugExecutionKind.goroutine);
    expect(event.opaqueNativeBoundary, isFalse);
    expect(event.frames.single.opaqueNativeBoundary, isFalse);
  });

  test('callback metadata decodes without assuming an opaque boundary', () {
    final thread = GoDebugThread.fromJson({
      'id': 7,
      'paused': true,
      'kind': 'nativeCallback',
    });
    final event = GoDebugEvent.fromJson({
      'sequence': 1,
      'reason': 'breakpoint',
      'goroutineId': 7,
      'kind': 'nativeCallback',
      'opaqueNativeBoundary': false,
      'frames': [
        {
          'name': 'callback',
          'file': 'main.go',
          'line': 4,
          'column': 2,
          'opaqueNativeBoundary': true,
        },
      ],
    });
    expect(thread.kind, GoDebugExecutionKind.nativeCallback);
    expect(thread.kind.nameFor(thread.id), 'Native callback 7');
    expect(event.kind, GoDebugExecutionKind.nativeCallback);
    expect(event.opaqueNativeBoundary, isFalse);
    expect(event.frames.single.opaqueNativeBoundary, isTrue);
    expect(
      GoDebugThread.fromJson({'kind': 'goroutine'}).kind,
      GoDebugExecutionKind.goroutine,
    );
  });

  test('execution metadata rejects unknown kinds and malformed types', () {
    for (final kind in [null, 'worker', 1, true, <Object>[], <String, Object>{}]) {
      expect(
        () => GoDebugThread.fromJson({'kind': kind}),
        throwsFormatException,
      );
      expect(
        () => GoDebugEvent.fromJson({'kind': kind}),
        throwsFormatException,
      );
    }
    for (final boundary in [null, 0, 'true', <Object>[], <String, Object>{}]) {
      expect(
        () => GoDebugEvent.fromJson({'opaqueNativeBoundary': boundary}),
        throwsFormatException,
      );
      expect(
        () => GoDebugFrame.fromJson({'opaqueNativeBoundary': boundary}),
        throwsFormatException,
      );
    }
  });

  test('callback history retains metadata after its live owner exits', () async {
    final backend = _Backend()
      ..responseState = 'paused'
      ..sequence = 1
      ..callback = true;
    final session = await GoDebugger(
      backend: backend,
    ).start(projectPath: 'p', entryFile: 'p/main.go');
    expect(
      session.snapshot.threads.single.kind,
      GoDebugExecutionKind.nativeCallback,
    );
    backend
      ..responseState = 'terminated'
      ..sequence = 2
      ..callback = false;
    await session.poll();
    expect(session.snapshot.threads, isEmpty);
    final callback = session.snapshot.events.first;
    expect(callback.kind, GoDebugExecutionKind.nativeCallback);
    expect(callback.opaqueNativeBoundary, isTrue);
    expect(callback.frames.single.opaqueNativeBoundary, isTrue);
    expect(() => callback.frames.clear(), throwsUnsupportedError);
    await session.close();
    session.dispose();
  });

  test(
    'breakpoints parse exact files, deduplicate and reject invalid input',
    () {
      expect(
        GoDebugBreakpoints.parse(
          '7, 3\nhelper.go:12\n7',
          entryFile: 'src/main.go',
        ),
        {
          'src/main.go': [3, 7],
          'helper.go': [12],
        },
      );
      for (final input in ['0', '-1', 'a', 'file:', 'file:1000001']) {
        expect(
          () => GoDebugBreakpoints.parse(input, entryFile: 'main.go'),
          throwsA(isA<GoDebugException>()),
        );
      }
      expect(
        () => GoDebugBreakpoints.parse(
          List.generate(257, (index) => '${index + 1}').join(','),
          entryFile: 'main.go',
        ),
        throwsA(isA<GoDebugException>()),
      );
    },
  );

  test(
    'start forwards project, selected entry and breakpoints with unique identity',
    () async {
      final backend = _Backend();
      final debugger = GoDebugger(backend: backend);
      final session = await debugger.start(
        projectPath: '/project',
        entryFile: '/project/main2.go',
        breakpoints: {
          'main2.go': [7],
        },
      );
      final call = backend.calls.first;
      expect(call.request['entryFile'], '/project/main2.go');
      expect(call.request['breakpoints'], {
        'main2.go': [7],
      });
      final second = await debugger.start(
        projectPath: '/other',
        entryFile: '/other/main.go',
      );
      expect(second.id, isNot(session.id));
      await session.close();
      await second.close();
      session.dispose();
      second.dispose();
    },
  );

  test(
    'session serializes polling and commands, retains bounded immutable history',
    () async {
      final backend = _Backend();
      final session = await GoDebugger(
        backend: backend,
      ).start(projectPath: 'p', entryFile: 'p/main.go');
      var notifications = 0;
      session.addListener(() => notifications++);
      backend.responseState = 'paused';
      backend.sequence = 1;
      await session.poll();
      expect(
        session.snapshot.stoppedEvent!.frames.first.variables.first.value,
        '42',
      );
      expect(() => session.snapshot.events.clear(), throwsUnsupportedError);
      final block = Completer<void>();
      backend.blockPoll = block.future;
      final poll = session.poll();
      final command = session.command(GoDebugCommand.stepOver);
      await Future<void>.delayed(Duration.zero);
      expect(
        backend.calls.where((call) => call.operation == 'command'),
        isEmpty,
      );
      block.complete();
      await poll;
      await command;
      expect(backend.calls.last.request['command'], 'stepOver');
      expect(session.snapshot.sequence, 2);
      for (var i = 3; i < 145; i++) {
        backend.sequence = i;
        await session.poll();
      }
      expect(session.snapshot.events, hasLength(128));
      expect(notifications, greaterThan(1));
      await session.close();
      await session.close();
      expect(
        backend.calls.where((call) => call.operation == 'close'),
        hasLength(1),
      );
      expect(session.closed, isTrue);
      await expectLater(
        session.command(GoDebugCommand.continueExecution),
        throwsA(isA<GoDebugException>()),
      );
      session.dispose();
    },
  );

  test(
    'rejects stale identity, invalid payloads and preserves the current session',
    () async {
      final backend = _Backend();
      final session = await GoDebugger(
        backend: backend,
      ).start(projectPath: 'p', entryFile: 'p/main.go');
      backend.wrongIdentity = true;
      await expectLater(session.poll(), throwsA(isA<GoDebugException>()));
      expect(session.snapshot.state, 'starting');
      backend.wrongIdentity = false;
      backend.responseState = 'invented';
      await expectLater(session.poll(), throwsFormatException);
      backend.responseState = 'paused';
      await session.poll();
      await session.close();
      session.dispose();
      expect(
        () => GoDebugSnapshot.fromJson({
          'ok': true,
          'sessionId': 1,
          'state': 'paused',
          'events': 'bad',
        }, expectedId: 1),
        throwsFormatException,
      );
    },
  );

  test(
    'failed start reports the actual capability error and releases its ID',
    () async {
      final backend = _Backend()..startFailure = 'native symbol missing';
      await expectLater(
        GoDebugger(
          backend: backend,
        ).start(projectPath: 'p', entryFile: 'p/main.go'),
        throwsA(
          isA<GoDebugException>().having(
            (error) => error.message,
            'message',
            'native symbol missing',
          ),
        ),
      );
      expect(backend.calls.map((call) => call.operation), ['start', 'close']);
    },
  );

  test(
    'real native FFI stops before a side effect, reads locals and releases session',
    () async {
      final root = Directory.systemTemp.createTempSync('go_debug_ffi_');
      addTearDown(() => root.deleteSync(recursive: true));
      final marker = File(p.join(root.path, 'marker.txt'));
      final entry = File(p.join(root.path, 'main.go'));
      entry.writeAsStringSync(
        'package main\nimport ("fmt";"os")\nfunc main(){\n value := 42\n os.WriteFile("marker.txt",[]byte("written"),0600)\n fmt.Println(value)\n}\n',
      );
      final session = await GoDebugger().start(
        projectPath: root.path,
        entryFile: entry.path,
        breakpoints: {
          'main.go': [5],
        },
      );
      addTearDown(() async {
        await session.close();
        session.dispose();
      });
      await _nativeUntil(session, () => session.snapshot.state == 'paused');
      expect(marker.existsSync(), isFalse);
      await session.command(GoDebugCommand.continueExecution);
      await _nativeUntil(
        session,
        () => session.snapshot.stoppedEvent?.reason == 'breakpoint',
      );
      expect(marker.existsSync(), isFalse);
      expect(session.snapshot.stoppedEvent!.frames.first.line, 5);
      expect(
        session.snapshot.stoppedEvent!.frames.first.variables.any(
          (variable) => variable.name == 'value' && variable.value == '42',
        ),
        isTrue,
      );
      await session.command(GoDebugCommand.stepOver);
      await _nativeUntil(
        session,
        () => session.snapshot.stoppedEvent?.reason == 'stepOver',
      );
      expect(marker.existsSync(), isTrue);
      await session.command(GoDebugCommand.continueExecution);
      await _nativeUntil(session, () => session.snapshot.terminal);
      expect(session.snapshot.state, 'terminated');
      expect(session.snapshot.stdout.trim(), '42');
    },
    skip: Platform.environment['QFLI_GO_RUNTIME_LIBRARY'] == null
        ? 'Set QFLI_GO_RUNTIME_LIBRARY to test the current native artifact'
        : false,
  );
}

Future<void> _nativeUntil(GoDebugSession session, bool Function() ready) async {
  final deadline = DateTime.now().add(const Duration(seconds: 8));
  while (!ready() && DateTime.now().isBefore(deadline)) {
    await Future<void>.delayed(const Duration(milliseconds: 10));
    await session.poll();
    if (session.snapshot.state == 'failed') {
      fail(session.snapshot.events.last.message);
    }
  }
  expect(
    ready(),
    isTrue,
    reason: 'Native debugger timed out: ${session.snapshot.state}',
  );
}

class _Call {
  _Call(this.operation, this.id, this.request);
  final String operation;
  final int id;
  final Map<String, Object?> request;
}

class _Backend implements GoDebugBackend {
  final calls = <_Call>[];
  String responseState = 'starting';
  int sequence = 0;
  bool wrongIdentity = false;
  bool callback = false;
  String? startFailure;
  Future<void>? blockPoll;
  @override
  Future<Map<String, dynamic>> invoke({
    required String operation,
    required int sessionId,
    Map<String, Object?> request = const {},
    int afterSequence = 0,
  }) async {
    calls.add(_Call(operation, sessionId, request));
    if (operation == 'start' && startFailure != null) {
      return {'ok': false, 'error': startFailure};
    }
    if (operation == 'poll' && blockPoll != null) {
      final block = blockPoll;
      blockPoll = null;
      await block;
    }
    if (operation == 'command') {
      sequence++;
      responseState = request['command'] == 'stop' ? 'terminated' : 'paused';
    }
    return {
      'ok': true,
      'sessionId': wrongIdentity ? sessionId + 1 : sessionId,
      'state': operation == 'close' ? 'closed' : responseState,
      'sequence': sequence,
      'threads': [
        if (callback && responseState == 'paused')
          {'id': 1, 'paused': true, 'kind': 'nativeCallback'},
      ],
      'events': sequence > 0
          ? [
              {
                'sequence': sequence,
                'reason': operation == 'command' ? 'stepOver' : 'entry',
                'goroutineId': 1,
                if (callback) 'kind': 'nativeCallback',
                if (callback) 'opaqueNativeBoundary': true,
                'frames': [
                  {
                    'name': 'main',
                    'file': 'main.go',
                    'line': sequence + 3,
                    'column': 2,
                    if (callback) 'opaqueNativeBoundary': true,
                    'variables': [
                      {'name': 'value', 'type': 'int', 'value': '42'},
                    ],
                  },
                ],
              },
            ]
          : [],
      'breakpoints': [],
      'stdout': '',
      'stderr': '',
    };
  }
}
