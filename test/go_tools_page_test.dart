import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_tools.dart';
import 'package:qfli_go/go_tools_page.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/pages/tools_grid.dart';
import 'package:qfli_studio_core/store/project_store.dart';

void main() {
  late Directory temporary;
  late _MemoryStore store;
  late Project first;
  late Project second;

  setUp(() {
    temporary = Directory.systemTemp.createTempSync('go_tools_widget_');
    first = Project.create(
      name: 'Alpha',
      path: p.join(temporary.path, 'alpha'),
      type: 'go',
    );
    second = Project.create(
      name: 'Beta',
      path: p.join(temporary.path, 'beta'),
      type: 'go',
    );
    Directory(first.path).createSync();
    Directory(second.path).createSync();
    File(
      p.join(first.path, 'go.mod'),
    ).writeAsStringSync('module local.test/alpha\ngo 1.23\n');
    File(
      p.join(second.path, 'go.mod'),
    ).writeAsStringSync('module local.test/beta\ngo 1.23\n');
    File(p.join(first.path, 'main.go')).writeAsStringSync('package alpha\n');
    File(p.join(second.path, 'main.go')).writeAsStringSync('package beta\n');
    store = _MemoryStore([first, second]);
    store.lastBrowsedProjectId = second.id;
  });
  tearDown(() {
    store.dispose();
    temporary.deleteSync(recursive: true);
  });

  testWidgets(
    'four direct cards and terminal appear without a feature detour',
    (tester) async {
      var openedTerminal = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: GoToolsTab(
              store: store,
              onOpenTerminal: () => openedTerminal = true,
            ),
          ),
        ),
      );
      expect(find.byType(ToolsGrid), findsOneWidget);
      expect(find.text('Go 格式化'), findsOneWidget);
      expect(find.text('导入与符号'), findsOneWidget);
      expect(find.text('Go 模块检查'), findsOneWidget);
      expect(find.text('JSON 转 Go 结构体'), findsOneWidget);
      expect(find.text('专用'), findsNothing);
      await tester.tap(find.text('终端'));
      expect(openedTerminal, isTrue);
      await tester.tap(find.text('Go 格式化'));
      await tester.pumpAndSettle();
      expect(find.byType(GoSourceToolPage), findsOneWidget);
      expect(find.widgetWithText(FilledButton, '格式化'), findsOneWidget);
    },
  );

  testWidgets('supports injected first-level tools and narrow large text', (
    tester,
  ) async {
    tester.view.resetPhysicalSize();
    tester.view.physicalSize = const Size(320, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var debugOpened = false;
    await tester.pumpWidget(
      MaterialApp(
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: const TextScaler.linear(2)),
          child: child!,
        ),
        home: Scaffold(
          body: GoToolsTab(
            store: store,
            onOpenTerminal: () {},
            extraTools: [
              ToolDefinition(
                icon: Icons.bug_report,
                title: 'Go 调试',
                description: '本地断点调试',
                onTap: () => debugOpened = true,
              ),
            ],
          ),
        ),
      ),
    );
    await tester.scrollUntilVisible(
      find.text('Go 调试'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Go 调试'));
    expect(debugOpened, isTrue);
    expect(tester.takeException(), isNull);
  });

  testWidgets('formats edited input and clears stale output', (tester) async {
    final seen = <String>[];
    final tools = GoTools(
      formatter: (source, path) async {
        seen.add(source);
        return const GoToolSourceResult(
          formattedSource: 'package main\n\nfunc main() {}\n',
        );
      },
    );
    await tester.pumpWidget(
      MaterialApp(
        home: GoSourceToolPage(store: store, tools: tools),
      ),
    );
    await tester.enterText(
      find.byType(TextField).first,
      'package main;func main(){}',
    );
    await tester.ensureVisible(find.text('格式化').last);
    await tester.tap(find.widgetWithText(FilledButton, '格式化'));
    await tester.pumpAndSettle();
    expect(seen, ['package main;func main(){}']);
    expect(find.text('格式化结果'), findsOneWidget);
    await tester.ensureVisible(find.text('用结果替换输入'));
    await tester.tap(find.text('用结果替换输入'));
    await tester.pump();
    expect(
      tester.widget<TextField>(find.byType(TextField).first).controller!.text,
      'package main\n\nfunc main() {}\n',
    );
    expect(find.text('格式化结果'), findsNothing);
  });

  testWidgets('reports backend parse errors and missing capabilities', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: GoSourceToolPage(
          store: store,
          tools: GoTools(
            inspector: (_, _) async => const GoToolSourceResult(
              errors: ['snippet.go:2:1: expected declaration'],
            ),
          ),
          inspectOnly: true,
        ),
      ),
    );
    await tester.enterText(find.byType(TextField).first, 'package main\nfunc');
    await tester.ensureVisible(find.text('分析源码'));
    await tester.tap(find.text('分析源码'));
    await tester.pumpAndSettle();
    expect(find.textContaining('expected declaration'), findsOneWidget);
    await tester.pumpWidget(
      MaterialApp(
        home: GoSourceToolPage(
          key: const ValueKey('unsupported'),
          store: store,
          tools: GoTools(),
        ),
      ),
    );
    await tester.enterText(find.byType(TextField).first, 'package main');
    await tester.ensureVisible(find.widgetWithText(FilledButton, '格式化'));
    await tester.tap(find.widgetWithText(FilledButton, '格式化'));
    await tester.pumpAndSettle();
    expect(find.textContaining('后端不可用'), findsOneWidget);
  });

  testWidgets('ignores source results after input changes during analysis', (
    tester,
  ) async {
    final pending = Completer<GoToolSourceResult>();
    await tester.pumpWidget(
      MaterialApp(
        home: GoSourceToolPage(
          store: store,
          tools: GoTools(inspector: (_, _) => pending.future),
          inspectOnly: true,
        ),
      ),
    );
    await tester.enterText(find.byType(TextField).first, 'package before');
    await tester.ensureVisible(find.text('分析源码'));
    await tester.tap(find.text('分析源码'));
    await tester.pump();
    await tester.enterText(find.byType(TextField).first, 'package after');
    pending.complete(const GoToolSourceResult(report: 'old package before'));
    await tester.pumpAndSettle();
    expect(find.text('old package before'), findsNothing);
  });

  testWidgets(
    'module inspector starts with current project and switches ownership',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: GoModuleToolPage(store: store, tools: GoTools()),
        ),
      );
      expect(find.text('Beta'), findsOneWidget);
      await tester.tap(find.text('检查依赖'));
      await _finishIo(tester);
      expect(find.textContaining('module local.test/beta'), findsOneWidget);
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Alpha').last);
      await tester.pumpAndSettle();
      expect(store.lastBrowsedProjectId, first.id);
      expect(find.textContaining('module local.test/beta'), findsNothing);
      await tester.tap(find.text('检查依赖'));
      await _finishIo(tester);
      expect(find.textContaining('module local.test/alpha'), findsOneWidget);
    },
  );

  testWidgets('reads selected project source without writing it', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: GoSourceToolPage(store: store, tools: GoTools()),
      ),
    );
    await tester.tap(find.text('列出源文件'));
    await _finishIo(tester);
    await tester.tap(find.byType(DropdownButtonFormField<String>).last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('main.go').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('读取所选文件'));
    await _finishIo(tester);
    expect(
      tester.widget<TextField>(find.byType(TextField).first).controller!.text,
      'package beta\n',
    );
    await tester.enterText(find.byType(TextField).first, 'edited in tool');
    expect(
      File(p.join(second.path, 'main.go')).readAsStringSync(),
      'package beta\n',
    );
  });

  testWidgets(
    'JSON form generates data and shows invalid input at phone scale',
    (tester) async {
      tester.view.physicalSize = const Size(360, 1100);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        MaterialApp(
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: const TextScaler.linear(1.8)),
            child: child!,
          ),
          home: const GoJsonStructToolPage(),
        ),
      );
      await tester.enterText(
        find.byType(TextField).last,
        '{"user_id":12,"tags":["go"]}',
      );
      await tester.ensureVisible(find.text('生成结构体'));
      await tester.tap(find.text('生成结构体'));
      await tester.pumpAndSettle();
      expect(find.textContaining('UserID int64'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.enterText(find.byType(TextField).last, '{');
      await tester.ensureVisible(find.text('生成结构体'));
      await tester.tap(find.text('生成结构体'));
      await tester.pumpAndSettle();
      expect(find.text('Go 类型声明'), findsNothing);
      expect(find.textContaining('Unexpected'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}

Future<void> _finishIo(WidgetTester tester) async {
  for (var attempt = 0; attempt < 20; attempt++) {
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
    await tester.pump(const Duration(milliseconds: 20));
  }
  await tester.pumpAndSettle();
}

class _MemoryStore extends ProjectStore {
  _MemoryStore(this.items);
  final List<Project> items;
  @override
  List<Project> get projects => items;
  @override
  void setBrowsedProject(Project project) {
    lastBrowsedProjectId = project.id;
  }
}
