import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_debugger.dart';
import 'package:qfli_go/go_debugger_page.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/store/project_store.dart';

void main() {
  late Directory root;
  late _Store store;
  late _Backend backend;
  setUp(() {
    root = Directory.systemTemp.createTempSync('go_debug_page_');
    final project = Project.create(
      name: '当前 Go 项目',
      path: root.path,
      type: 'go',
    );
    File(
      p.join(root.path, 'main.go'),
    ).writeAsStringSync('package main\nfunc main(){}\n');
    File(
      p.join(root.path, 'main2.go'),
    ).writeAsStringSync('package main\nfunc main(){}\n');
    store = _Store([project])..lastBrowsedProjectId = project.id;
    backend = _Backend();
  });
  tearDown(() {
    store.dispose();
    root.deleteSync(recursive: true);
  });

  testWidgets(
    'selected entry and breakpoints reach backend, stopped frame and controls are real',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: GoDebuggerPage(
            store: store,
            debugger: GoDebugger(backend: backend),
          ),
        ),
      );
      await _io(tester);
      await tester.tap(find.byType(DropdownButtonFormField<String>).last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('main2.go').last);
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField), '7\nhelper.go:12');
      await tester.ensureVisible(find.text('启动调试'));
      await tester.tap(find.text('启动调试'));
      await tester.pumpAndSettle();
      expect(backend.entryFile, p.join(root.path, 'main2.go'));
      expect(backend.breakpoints, {
        'main2.go': [7],
        'helper.go': [12],
      });
      expect(find.text('状态：已暂停'), findsOneWidget);
      expect(find.textContaining('main · main2.go:7:2'), findsOneWidget);
      expect(find.textContaining('value (int) = 42'), findsOneWidget);
      await tester.ensureVisible(find.text('单步跳过'));
      await tester.tap(find.text('单步跳过'));
      await tester.pumpAndSettle();
      expect(backend.commands, ['stepOver']);
      expect(find.textContaining('main · main2.go:8:2'), findsOneWidget);
      await tester.ensureVisible(find.text('继续'));
      await tester.tap(find.text('继续'));
      await tester.pumpAndSettle();
      expect(find.text('状态：已结束'), findsOneWidget);
      expect(find.text('result 42\n'), findsOneWidget);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
      expect(backend.closes, 1);
    },
  );

  testWidgets(
    'callback labels and native boundary details survive in event history',
    (tester) async {
      backend.kind = 'nativeCallback';
      backend.opaqueNativeBoundary = true;
      backend.localsUnavailable = 'External callback locals are unavailable';
      await tester.pumpWidget(
        MaterialApp(
          home: GoDebuggerPage(
            store: store,
            debugger: GoDebugger(backend: backend),
          ),
        ),
      );
      await _io(tester);
      await tester.ensureVisible(find.text('启动调试'));
      await tester.tap(find.text('启动调试'));
      await tester.pumpAndSettle();
      expect(find.text('Native callback 1 · 命中断点'), findsOneWidget);
      expect(find.text('调用栈在原生回调边界结束，外部调用者不可用。'), findsOneWidget);
      expect(find.text('External callback locals are unavailable'), findsOneWidget);
      expect(find.text('此栈帧没有可展示的局部变量'), findsNothing);
      backend.kind = null;
      backend.opaqueNativeBoundary = false;
      await tester.ensureVisible(find.text('继续'));
      await tester.tap(find.text('继续'));
      await tester.pumpAndSettle();
      expect(find.text('状态：已结束'), findsOneWidget);
      expect(
        find.textContaining('1 · 命中断点 · Native callback 1'),
        findsOneWidget,
      );
      expect(find.textContaining('调用栈在原生回调边界结束'), findsOneWidget);
      expect(backend.commands, ['continue']);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
      expect(backend.closes, 1);
    },
  );

  testWidgets('frame metadata explains unavailable callback locals', (tester) async {
    backend.kind = 'nativeCallback';
    backend.frameOpaqueNativeBoundary = true;
    await tester.pumpWidget(
      MaterialApp(
        home: GoDebuggerPage(
          store: store,
          debugger: GoDebugger(backend: backend),
        ),
      ),
    );
    await _io(tester);
    await tester.ensureVisible(find.text('启动调试'));
    await tester.tap(find.text('启动调试'));
    await tester.pumpAndSettle();
    expect(find.text('Native callback 1 · 命中断点'), findsOneWidget);
    expect(find.text('调用栈在原生回调边界结束，外部调用者不可用。'), findsOneWidget);
    expect(find.text('原生回调边界的局部变量不可用。'), findsOneWidget);
    expect(find.textContaining('value (int) = 42'), findsNothing);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
    expect(backend.closes, 1);
  });

  testWidgets(
    'invalid breakpoints prevent start and unavailable runtime reports its error',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: GoDebuggerPage(
            store: store,
            debugger: GoDebugger(backend: backend),
          ),
        ),
      );
      await _io(tester);
      await tester.enterText(find.byType(TextField), 'zero');
      await tester.ensureVisible(find.text('启动调试'));
      await tester.tap(find.text('启动调试'));
      await tester.pumpAndSettle();
      expect(find.textContaining('断点格式无效'), findsOneWidget);
      expect(backend.starts, 0);
      await tester.enterText(find.byType(TextField), '7');
      backend.failure = '当前包缺少调试符号';
      await tester.ensureVisible(find.text('启动调试'));
      await tester.tap(find.text('启动调试'));
      await tester.pumpAndSettle();
      expect(find.text('当前包缺少调试符号'), findsOneWidget);
      expect(find.text('状态：已暂停'), findsNothing);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
    },
  );

  testWidgets('phone large text retains controls and can stop a live session', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 1100);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: const TextScaler.linear(2)),
          child: child!,
        ),
        home: GoDebuggerPage(
          store: store,
          debugger: GoDebugger(backend: backend),
        ),
      ),
    );
    await _io(tester);
    await tester.ensureVisible(find.text('启动调试'));
    await tester.tap(find.text('启动调试'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('停止'));
    expect(tester.takeException(), isNull);
    await tester.tap(find.text('停止'));
    await tester.pumpAndSettle();
    expect(backend.commands, ['stop']);
    expect(find.text('状态：已结束'), findsOneWidget);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
    expect(backend.closes, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('disposing a live debugger closes it and cancels polling', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: GoDebuggerPage(
          store: store,
          debugger: GoDebugger(backend: backend),
        ),
      ),
    );
    await _io(tester);
    await tester.ensureVisible(find.text('启动调试'));
    await tester.tap(find.text('启动调试'));
    await tester.pumpAndSettle();
    expect(find.text('状态：已暂停'), findsOneWidget);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
    final polls = backend.polls;
    await tester.pump(const Duration(milliseconds: 600));
    expect(backend.closes, 1);
    expect(backend.polls, polls);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'transient polling failure recovers without restarting the session',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: GoDebuggerPage(
            store: store,
            debugger: GoDebugger(backend: backend),
          ),
        ),
      );
      await _io(tester);
      await tester.ensureVisible(find.text('启动调试'));
      await tester.tap(find.text('启动调试'));
      await tester.pumpAndSettle();
      backend.throwPoll = true;
      await tester.pump(const Duration(milliseconds: 160));
      await tester.pump();
      expect(find.textContaining('temporary poll failure'), findsOneWidget);
      backend.throwPoll = false;
      await tester.pump(const Duration(milliseconds: 160));
      await tester.pump();
      expect(find.textContaining('temporary poll failure'), findsNothing);
      expect(backend.starts, 1);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
    },
  );
}

Future<void> _io(WidgetTester tester) async {
  for (var i = 0; i < 10; i++) {
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
    await tester.pump(const Duration(milliseconds: 20));
  }
  await tester.pumpAndSettle();
}

class _Store extends ProjectStore {
  _Store(this.items);
  final List<Project> items;
  @override
  List<Project> get projects => items;
  @override
  void setBrowsedProject(Project project) {
    lastBrowsedProjectId = project.id;
  }
}

class _Backend implements GoDebugBackend {
  int starts = 0;
  int closes = 0;
  int sequence = 1;
  int line = 7;
  String? entryFile;
  Object? breakpoints;
  String? failure;
  String state = 'paused';
  String? kind;
  String localsUnavailable = '';
  bool opaqueNativeBoundary = false, frameOpaqueNativeBoundary = false;
  final commands = <String>[];
  int polls = 0;
  bool throwPoll = false;
  @override
  Future<Map<String, dynamic>> invoke({
    required String operation,
    required int sessionId,
    Map<String, Object?> request = const {},
    int afterSequence = 0,
  }) async {
    if (operation == 'poll') {
      polls++;
      if (throwPoll) throw StateError('temporary poll failure');
    }
    if (operation == 'start') {
      starts++;
      entryFile = request['entryFile'] as String;
      breakpoints = request['breakpoints'];
      if (failure != null) return {'ok': false, 'error': failure};
    }
    if (operation == 'command') {
      final command = request['command'] as String;
      commands.add(command);
      sequence++;
      if (command == 'stepOver') {
        line++;
      } else {
        state = 'terminated';
      }
    }
    if (operation == 'close') closes++;
    return {
      'ok': true,
      'sessionId': sessionId,
      'state': operation == 'close' ? 'closed' : state,
      'sequence': sequence,
      'events': [
        {
          'sequence': sequence,
          'reason': sequence == 1
              ? 'breakpoint'
              : state == 'terminated'
              ? 'terminated'
              : 'stepOver',
          'goroutineId': 1,
          if (kind != null) 'kind': kind,
          if (opaqueNativeBoundary) 'opaqueNativeBoundary': true,
          'frames': state == 'paused'
              ? [
                  {
                    'name': 'main',
                    'file': 'main2.go',
                    'line': line,
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
                ]
              : [],
        },
      ],
      'breakpoints': [
        {'file': 'main2.go', 'line': 7, 'actualLine': 7, 'valid': true},
      ],
      'stdout': state == 'terminated' ? 'result 42\n' : '',
      'stderr': '',
    };
  }
}
