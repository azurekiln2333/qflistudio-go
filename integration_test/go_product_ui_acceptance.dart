import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart' show debugPrintSynchronously;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_code_analyzer.dart';
import 'package:qfli_go/go_debugger.dart';
import 'package:qfli_go/go_platform.dart';
import 'package:qfli_go/go_studio_debugger.dart';
import 'package:qfli_go/go_tools_page.dart';
import 'package:qfli_go/main.dart' show goProfile;
import 'package:qfli_studio_core/editor/editor_analysis_controller.dart';
import 'package:qfli_studio_core/editor/editor_controller.dart';
import 'package:qfli_studio_core/editor/editor_debug_controller.dart';
import 'package:qfli_studio_core/editor/editor_debug_widgets.dart';
import 'package:qfli_studio_core/editor/editor_diagnostics.dart';
import 'package:qfli_studio_core/editor/editor_output_panel.dart';
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/editor/editor_problems_bar.dart';
import 'package:qfli_studio_core/editor/project_history.dart';
import 'package:qfli_studio_core/editor/retained_editor_host.dart';
import 'package:qfli_studio_core/i18n/studio_localizations.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/pages/quick_tools_page.dart';
import 'package:qfli_studio_core/pages/tools_grid.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_studio_core/tools/offline_tools.dart';
import 'package:qfli_studio_core/workspace/saved_workspace.dart';
import 'package:qfli_studio_core/workspace/workspace_store.dart';
import 'package:re_editor/re_editor.dart';

import 'go_native_ide_acceptance.dart' show loadedGoNativeAuditRuntime;

const _uiOperations = [
  'editor-unsaved-waves-problems',
  'editor-gutter-debug-panels',
  'direct-tools-real-source-projects',
  'named-multi-root-sidebar-retention',
];

/// Real product widgets, real Go adapters and real local files on the target.
/// The returned barrier tracks actual body cleanup after a framework timeout.
Future<void> Function() registerGoProductUiAcceptance({
  required IntegrationTestWidgetsFlutterBinding binding,
  bool requireEmbeddedRuntime = false,
  Future<Map<String, Object?>> Function()? runtimeIdentity,
  Future<void> Function()? beforeAudit,
}) {
  Completer<void>? activeBody;
  _ProductUiAudit? activeAudit;
  final embedded = goRuntimeBackendFor(Platform.operatingSystem) ==
      GoRuntimeBackend.embeddedInterpreter;
  testWidgets(
    'packaged Go editor, panels and direct tools use the real runtime',
    (tester) async {
      final body = Completer<void>();
      activeBody = body;
      final audit = _ProductUiAudit(
        tester, binding, runtimeIdentity ?? loadedGoNativeAuditRuntime,
      );
      activeAudit = audit;
      try {
        // A previous framework observation timeout cannot release its runtime.
        if (beforeAudit != null) await beforeAudit();
        final report = await audit.run();
        expect(report['success'], isTrue,
            reason: 'Go product UI audit: ${report['reportPath']}');
      } finally {
        if (audit.released && !body.isCompleted) body.complete();
      }
    },
    // Go product UI acceptance requires bundled Android/OHOS/iOS FFI unless
    // the hosted caller explicitly requires its supplied native runtime.
    skip: !embedded && !requireEmbeddedRuntime,
    timeout: const Timeout(Duration(minutes: 6)),
  );
  return () async {
    final body = activeBody;
    final audit = activeAudit; // Keep actual controllers/fixtures reachable.
    if (body != null) await body.future;
    if (audit?.retainedFixtures.isNotEmpty == true) {
      throw StateError('Actual Go UI fixture ownership has not drained');
    }
  };
}

class _ProductUiAudit {
  _ProductUiAudit(this.tester, this.binding, this.readRuntimeIdentity);
  final WidgetTester tester;
  final IntegrationTestWidgetsFlutterBinding binding;
  final Future<Map<String, Object?>> Function() readRuntimeIdentity;
  final records = <Map<String, Object?>>[];
  final errors = <String>[];
  final pending = <String>[];
  final retainedFixtures = <_UiFixture>[];
  final boundaryKey = GlobalKey();
  late Directory root;
  late String originalCwd;
  Map<String, Object?>? runtime;
  bool released = false;
  bool blocked = false;

  Future<Map<String, Object?>> run() async {
    originalCwd = Directory.current.path;
    try {
      root = (await tester.runAsync(
        () => Directory.systemTemp.createTemp('qfli-go-product-ui-'),
      ))!;
    } catch (_) {
      released = true; // No fixture/controller/native operation exists yet.
      rethrow;
    }
    final previous = StudioProfile.current;
    StudioProfile.current = goProfile;
    try {
      expect(goRuntimeBackendFor(Platform.operatingSystem),
          GoRuntimeBackend.embeddedInterpreter,
          reason: 'SDK host execution cannot establish target UI acceptance');
      expect(goProfile.codeAnalyzer, isA<GoCodeAnalyzer>());
      expect(goProfile.debugger, isA<GoStudioDebugger>());
      await _case(_uiOperations[0], _diagnostics);
      await _case(_uiOperations[1], _debugger);
      await _case(_uiOperations[2], _tools);
      await _case(_uiOperations[3], _workspace);
      if (Directory.current.path != originalCwd) {
        errors.add('Process working directory changed');
      }
      if (runtime == null) errors.add('Loaded runtime identity is missing');
    } catch (error, stack) {
      errors.add('$error\n$stack');
    } finally {
      StudioProfile.current = previous;
      released = !blocked && pending.isEmpty;
    }
    return publish(finalReport: true);
  }

  Future<void> _case(
    String id,
    Future<void> Function(_UiFixture fixture, Map<String, Object?> evidence) action,
  ) async {
    final evidence = <String, Object?>{};
    final record = <String, Object?>{
      'id': id, 'status': blocked ? 'not-run' : 'running',
      'passed': false, 'cleanupConfirmed': false, 'evidence': evidence,
    };
    records.add(record);
    if (blocked) return;
    _UiFixture? fixture;
    final clock = Stopwatch()..start();
    try {
      fixture = await tester.runAsync(
        () => _UiFixture.create(Directory(p.join(root.path, id))),
      );
      if (fixture == null) throw StateError('Target fixture creation failed');
      retainedFixtures.add(fixture);
      await action(fixture, evidence);
      final identity = (await tester.runAsync(readRuntimeIdentity))!;
      expect(identity['path'], isA<String>());
      expect(identity['sha256'], matches(RegExp(r'^[a-fA-F0-9]{64}$')));
      if (runtime != null) {
        expect(identity['path'], runtime!['path']);
        expect(identity['sha256'], runtime!['sha256']);
      }
      runtime = identity;
      record['status'] = 'passed';
      record['passed'] = true;
    } catch (error, stack) {
      record['status'] = 'failed';
      record['error'] = '$error';
      record['stack'] = '$stack';
    } finally {
      if (fixture != null) {
        try {
          await _cleanup(fixture, record);
        } catch (error, stack) {
          blocked = true;
          record['passed'] = false;
          record['status'] = 'cleanup-failed';
          record['cleanupError'] = '$error';
          record['cleanupStack'] = '$stack';
        }
      } else {
        record['cleanupConfirmed'] = true; // No runtime operation was started.
      }
      record['elapsedMs'] = clock.elapsedMilliseconds;
      await publish(finalReport: false);
    }
  }

  Future<void> _cleanup(_UiFixture fixture, Map<String, Object?> record) async {
    final mountedProblems = find.byType(EditorProblemsBar);
    if (mountedProblems.evaluate().isNotEmpty) {
      fixture.analysis ??= tester.widget<EditorProblemsBar>(mountedProblems.first).analysis;
    }
    final mountedGutter = find.byType(EditorDebugGutter);
    if (mountedGutter.evaluate().isNotEmpty) {
      fixture.debug ??= tester.widget<EditorDebugGutter>(mountedGutter.first).debug;
    }
    final debug = fixture.debug;
    if (debug != null) {
      final actionStatus = record['status'];
      fixture.trackCurrent();
      final closing = debug.close();
      var done = false;
      Object? failure;
      closing.then<void>((_) => done = true, onError: (Object error) {
        failure = error;
        done = true;
      });
      final observation = Stopwatch()..start();
      var lastPublication = Duration.zero;
      while (!done) {
        await _tick(tester);
        fixture.trackCurrent();
        if (observation.elapsed >= const Duration(seconds: 15) &&
            observation.elapsed - lastPublication >= const Duration(seconds: 5)) {
          lastPublication = observation.elapsed;
          final id = debug.snapshot?.sessionId ?? 'starting:${fixture.first.id}';
          if (!pending.contains(id)) pending.add(id);
          record['status'] = 'cleanup-pending';
          record['cleanupObservationTimeout'] = true;
          record['pendingSessionId'] = id;
          await publish(finalReport: false);
          // Preserve THIS close Future/controller and fixture; no next case.
        }
      }
      if (failure != null) throw StateError('Actual editor close failed: $failure');
      expect(debug.busy, isFalse);
      fixture.trackCurrent();
      for (final id in fixture.sessionIds) {
        await _registryReleased(tester, id);
        pending.remove(id);
      }
      pending.removeWhere((id) => id == 'starting:${fixture.first.id}');
      record['sessionIds'] = fixture.sessionIds;
      if (record['status'] == 'cleanup-pending') record['status'] = actionStatus;
    }
    final analyzer = fixture.analysis;
    if (analyzer != null) {
      // pending=false alone also describes the watchdog while its actual
      // native Future is still running. Only source-proven returned results
      // release ownership; unavailable analysis still fails the audit.
      await _observeDrain(record, 'editor-analysis:${fixture.first.id}',
          () => _analysisReturned(analyzer));
      record['analysisDrainConfirmed'] = true;
      if (!analyzer.checked) {
        record['analysisDrainUnavailableReason'] = analyzer.unavailableReason;
        record['passed'] = false;
        record['status'] = 'failed';
      }
    }
    if (find.byType(GoSourceToolPage).evaluate().isNotEmpty ||
        find.byType(GoModuleToolPage).evaluate().isNotEmpty) {
      // These labels stay busy until the actual tool Future's finally runs.
      // Preserve the mounted tool state rather than dispose it after a timeout.
      await _observeDrain(record, 'source-tool:${fixture.first.id}', () =>
          find.text('处理中…').evaluate().isEmpty &&
          find.text('检查中…').evaluate().isEmpty);
      record['toolDrainConfirmed'] = true;
    }
    await tester.pumpWidget(const SizedBox.shrink());
    await _tick(tester);
    for (final host in fixture.hosts) {
      host.dispose();
    }
    await _pumpFuture(tester, fixture.workspaces.settle(),
        reason: 'Actual named-workspace writes did not settle');
    for (final store in fixture.extraWorkspaces) {
      await _pumpFuture(tester, store.settle(),
          reason: 'Reloaded workspace writes did not settle');
      store.dispose();
    }
    fixture.auth.dispose();
    fixture.settings.dispose();
    fixture.projects.dispose();
    fixture.workspaces.dispose();
    // The report and screenshots remain under root; only fixture-owned data goes.
    var deleted = false;
    for (var attempt = 0; attempt < 100 && !deleted; attempt++) {
      try {
        await tester.runAsync(() => fixture.directory.delete(recursive: true));
        deleted = true;
      } on FileSystemException {
        await _tick(tester);
      }
    }
    expect(deleted, isTrue, reason: 'Fixture writes did not release their files');
    record['cleanupConfirmed'] = true;
    retainedFixtures.remove(fixture);
  }

  Future<void> _observeDrain(Map<String, Object?> record, String id,
      bool Function() complete) async {
    await tester.pump();
    final actionStatus = record['status'];
    final observation = Stopwatch()..start();
    var lastPublication = Duration.zero;
    while (!complete()) {
      await _tick(tester);
      if (observation.elapsed >= const Duration(seconds: 15) &&
          observation.elapsed - lastPublication >= const Duration(seconds: 5)) {
        lastPublication = observation.elapsed;
        if (!pending.contains(id)) pending.add(id);
        record['status'] = 'cleanup-pending';
        record['cleanupObservationTimeout'] = true;
        record['pendingOperationId'] = id;
        await publish(finalReport: false);
      }
    }
    pending.remove(id);
    if (record['status'] == 'cleanup-pending') record['status'] = actionStatus;
  }

  Widget app(Widget child, {RetainedEditorController? host}) => MaterialApp(
    locale: const Locale('zh', 'CN'),
    supportedLocales: StudioLocalizations.supportedLocales,
    localizationsDelegates: const [StudioLocalizations.delegate],
    navigatorObservers: host == null ? const [] : [host.navigatorObserver],
    builder: (context, content) => RepaintBoundary(
      key: boundaryKey,
      child: host == null ? content! : RetainedEditorHost(controller: host, child: content!),
    ),
    home: child,
  );

  Future<EditorController> mount(_UiFixture fixture, {
    SavedWorkspace? workspace, WorkspaceStore? workspaceStore,
  }) async {
    await tester.pumpWidget(app(EditorPage(
      project: fixture.first, auth: fixture.auth, store: fixture.projects,
      settings: fixture.settings,
      initialOpenPath: workspace == null ? fixture.entry.path : null,
      workspace: workspace,
      workspaceMembers: workspace == null ? const [] : [fixture.first, fixture.second],
      workspaceStore: workspaceStore ?? fixture.workspaces,
    )));
    await _until(tester, () => find.byType(EditorProblemsBar).evaluate().isNotEmpty &&
        editor.current != null, reason: 'Actual Go EditorPage did not open its source');
    fixture.analysis = analysis;
    fixture.debug = tester.widget<EditorDebugGutter>(find.byType(EditorDebugGutter).first).debug;
    return editor;
  }

  EditorAnalysisController get analysis => tester
      .widget<EditorProblemsBar>(find.byType(EditorProblemsBar).first).analysis;
  EditorController get editor => analysis.editor;

  Future<void> capture(String name, Map<String, Object?> evidence) async {
    await tester.pump();
    List<int>? bytes;
    var method = 'integration-test-binding';
    String? bindingFailure;
    try {
      bytes = await tester.runAsync(() => binding.takeScreenshot('go-product-$name'));
    } catch (error) {
      bindingFailure = '$error';
    }
    if (bytes == null || bytes.isEmpty) {
      method = 'mounted-repaint-boundary';
      final boundary = boundaryKey.currentContext!.findRenderObject()! as RenderRepaintBoundary;
      bytes = await tester.runAsync(() async {
        final image = await boundary.toImage(pixelRatio: 1);
        try {
          final data = await image.toByteData(format: ui.ImageByteFormat.png);
          if (data == null) {
            throw StateError('No screenshot bytes for $name');
          }
          return data.buffer.asUint8List();
        } finally {
          image.dispose();
        }
      });
    }
    final imageBytes = bytes;
    if (imageBytes == null) throw StateError('No screenshot bytes for $name');
    expect(imageBytes.length, greaterThan(100));
    final path = p.join(root.path, '$name.png');
    await tester.runAsync(() => File(path).writeAsBytes(imageBytes, flush: true));
    evidence['screenshot:$name'] = {
      'path': path, 'method': method, 'bytes': imageBytes.length,
      'sha256': _bytesHash(imageBytes),
      'bindingFailure': ?bindingFailure,
    };
  }

  Future<void> _diagnostics(_UiFixture fixture, Map<String, Object?> evidence) async {
    final marker = File(p.join(fixture.first.path, 'analyzer-must-not-run.marker'));
    final prefix = 'package main\r\nimport "os"\r\n'
        'func init() { _ = os.WriteFile(${jsonEncode(marker.path)}, []byte("ran"), 0600) }\r\n';
    final saved = '${prefix}func main() { println("saved") }\r\n';
    final unsaved = '${prefix}func main() { _ = "汉😀"; 💥 }\r\n';
    await tester.runAsync(() => fixture.entry.writeAsString(saved));
    await mount(fixture);
    final file = editor.current!;
    expect(analysis.analyzer, same(goProfile.codeAnalyzer));
    file.controller.text = unsaved;
    await _until(tester, () => analysis.checked && !analysis.pending &&
        analysis.problems.any((item) => unsaved.substring(item.startOffset, item.endOffset) == '💥'),
        reason: 'Real Go editor analysis did not return the illegal Unicode range');
    final diagnostic = analysis.problems.firstWhere((item) =>
        unsaved.substring(item.startOffset, item.endOffset) == '💥');
    expect(diagnostic.endOffset - diagnostic.startOffset, 2);
    expect(diagnostic.filePath, fixture.entry.path);
    expect(file.dirty, isTrue);
    final line = const LineSplitter().convert(unsaved).length - 1;
    final index = file.controller.codeLines.lineIndex2Index(line).index;
    final text = file.controller.codeLines[index].text;
    // Invoke the installed editing-controller hook, not diagnostics.decorate.
    final decorated = file.controller.buildTextSpan(
      context: tester.element(find.byType(CodeEditor).first), index: index,
      textSpan: TextSpan(text: text, style: const TextStyle(color: Colors.blue)),
      style: const TextStyle(),
    );
    final waves = _wavyText(decorated);
    expect(decorated.toPlainText(), text);
    expect(waves.join(), '💥');
    final gutter = tester.widget<EditorDiagnosticGutter>(find.byType(EditorDiagnosticGutter).first);
    expect(gutter.diagnostics, same(file.diagnostics));
    expect(file.diagnostics!.gutterSeverity(index), CodeDiagnosticSeverity.error);
    final gutterPaint = find.descendant(of: find.byType(EditorDiagnosticGutter), matching: find.byType(CustomPaint));
    expect(tester.getSize(gutterPaint).height, greaterThan(0));
    expect((Canvas canvas) => tester.widget<CustomPaint>(gutterPaint).painter!
        .paint(canvas, tester.getSize(gutterPaint)), paints..circle());
    await capture('editor-waves', evidence);
    await tester.tap(find.byKey(const ValueKey('editor-problems-status')));
    await _until(tester, () => find.byKey(const ValueKey('editor-problems-list')).evaluate().isNotEmpty,
        reason: 'Actual Problems status did not open its panel');
    final row = find.descendant(of: find.byKey(const ValueKey('editor-problems-list')),
        matching: find.byWidgetPredicate((widget) => widget is ListTile &&
            widget.title is Text && (widget.title! as Text).data == diagnostic.message)).first;
    await tester.ensureVisible(row);
    await tester.tapAt(tester.getTopLeft(row) + const Offset(24, 20));
    await tester.pump();
    final selection = file.controller.selection;
    expect(selection.baseIndex, index);
    expect(selection.extentIndex, index);
    expect(text.substring(selection.baseOffset, selection.extentOffset), '💥');
    expect(await tester.runAsync(fixture.entry.readAsString), saved);
    expect(await tester.runAsync(marker.exists), isFalse);
    await capture('problems-navigation', evidence);
    file.controller.text = '${prefix}func main() { _ = "汉😀" }\r\n';
    await _until(tester, () => analysis.checked && !analysis.pending &&
        analysis.problems.isEmpty && analysis.unavailableReason == null,
        reason: 'Real Go diagnostics did not clear after a valid unsaved edit');
    final cleared = file.controller.buildTextSpan(
      context: tester.element(find.byType(CodeEditor).first), index: index,
      textSpan: TextSpan(text: file.controller.codeLines[index].text), style: const TextStyle(),
    );
    expect(_wavyText(cleared), isEmpty);
    expect(file.diagnostics!.gutterSeverity(index), isNull);
    expect(find.byKey(const ValueKey('editor-problems-list')), findsNothing);
    expect(find.text('本地检查未发现问题'), findsWidgets);
    expect(await tester.runAsync(fixture.entry.readAsString), saved);
    expect(await tester.runAsync(marker.exists), isFalse);
    evidence.addAll({
      'savedSourceSha256': OfflineDigest.sha256(saved),
      'unsavedSourceSha256': OfflineDigest.sha256(unsaved),
      'diagnostic': {'message': diagnostic.message, 'start': diagnostic.startOffset,
        'end': diagnostic.endOffset, 'severity': diagnostic.severity.name},
      'installedWavyText': waves.join(), 'gutterPainted': true,
      'selection': [selection.baseIndex, selection.baseOffset, selection.extentIndex, selection.extentOffset],
      'diskUnchanged': true, 'initializerMarkerAbsent': true,
      'clearedAfterValidUnsavedRevision': true,
    });
    expect(tester.takeException(), isNull);
  }

  Future<void> _debugger(_UiFixture fixture, Map<String, Object?> evidence) async {
    final marker = File(p.join(fixture.first.path, 'continued.marker'));
    final source = 'package main\nimport ("fmt"; "os")\nfunc main() {\n'
        ' value := 42\n value += 1\n'
        ' _ = os.WriteFile(${jsonEncode(marker.path)}, []byte("continued"), 0600)\n'
        ' fmt.Println(value)\n}\n';
    await tester.runAsync(() => fixture.entry.writeAsString(source));
    final controller = await mount(fixture);
    final file = controller.current!;
    await _panel(tester, 'debug');
    final debug = tester.widget<EditorDebugPanel>(find.byType(EditorDebugPanel)).debug;
    fixture.debug = debug;
    expect(debug.debugger, same(goProfile.debugger));
    await _gutter(tester, 5);
    expect(debug.breakpoints.single.line, 5);
    await _tapKey(tester, 'editor-debug-start');
    await _until(tester, () => debug.paused && debug.selectedFrame?.location?.line == 5,
        reason: 'Real editor debug did not pause at its gutter breakpoint');
    fixture.trackCurrent();
    final firstId = debug.snapshot!.sessionId;
    final paused = debug.snapshot!;
    expect(debug.breakpoints, hasLength(1));
    expect(paused.breakpoints.single.status, DebugBreakpointStatus.verified);
    expect(debug.selectedFrame!.locals.any((value) => value.name == 'value' && value.value == '42'), isTrue);
    await _until(tester, () => file.controller.selection.extentIndex == 4,
        reason: 'Real pause did not navigate to source line 5');
    expect(debug.executionLocationFor(file)?.line, 5);
    expect(await tester.runAsync(marker.exists), isFalse);
    final value42 = find.descendant(of: find.byType(EditorDebugPanel),
        matching: find.byWidgetPredicate((widget) => widget is SelectableText &&
            (widget.data ?? '').contains('value (int) = 42')));
    await tester.ensureVisible(value42);
    expect(value42.hitTestable(), findsOneWidget);
    await capture('debug-paused-value42', evidence);
    await _tapKey(tester, 'editor-debug-stepOver');
    await _until(tester, () => debug.paused && debug.snapshot!.pauseToken != paused.pauseToken &&
        debug.selectedFrame?.location?.line == 6,
        reason: 'Actual UI step-over did not reach source line 6');
    expect(debug.selectedFrame!.locals.any((value) => value.name == 'value' && value.value == '43'), isTrue);
    expect(await tester.runAsync(marker.exists), isFalse);
    await _tapKey(tester, 'editor-debug-resume');
    await _until(tester, () => !debug.busy && debug.snapshot?.isTerminal == true,
        reason: 'Actual UI continue did not terminate and dispose its native session');
    expect(debug.snapshot!.phase, DebugPhase.terminated);
    expect(debug.snapshot!.stdout, '43\n');
    expect(await tester.runAsync(marker.readAsString), 'continued');
    await _registryReleased(tester, firstId);
    await _panel(tester, 'output');
    expect(find.byType(EditorOutputPanel), findsOneWidget);
    final stdout = find.byKey(const ValueKey('editor-debug-stdout'));
    await tester.ensureVisible(stdout);
    expect(_selectableText(tester, stdout), '43\n');
    expect(find.text('调试 stdout'), findsOneWidget);
    expect(find.byKey(const ValueKey('editor-run-output')), findsNothing);
    await capture('debug-output-attribution', evidence);

    // A genuine opaque callback supplies native boundary logs to Debug Console.
    // Its body is stopped before printing, then the actual Stop control drains it.
    const callback = 'package main\nimport ("fmt"; "sync")\nfunc main() {\n'
        ' pool := sync.Pool{New: func() interface{} {\n'
        '  value := 42\n  fmt.Println("callback", value)\n  return value\n }}\n'
        ' fmt.Println("result", pool.Get())\n}\n';
    file.controller.text = callback;
    await tester.pump();
    await _panel(tester, 'debug');
    await _gutter(tester, 5); // Remove the prior launch's gutter breakpoint.
    await _gutter(tester, 6);
    expect(debug.breakpoints.single.line, 6);
    await _tapKey(tester, 'editor-debug-start');
    await _until(tester, () => debug.paused && debug.selectedFrame?.location?.line == 6,
        reason: 'Real callback did not stop through the shared editor');
    fixture.trackCurrent();
    final callbackId = debug.snapshot!.sessionId;
    expect(callbackId, isNot(firstId));
    expect(await tester.runAsync(fixture.entry.readAsString), callback,
        reason: 'Disk-only Go debugger must save the actual dirty editor source');
    expect(file.dirty, isFalse);
    expect(debug.snapshot!.threads.any((thread) => thread.name.startsWith('Native callback ')), isTrue);
    expect(debug.selectedFrame!.locals, isEmpty);
    expect(debug.selectedFrame!.localsUnavailableReason,
        'Opaque native callback may capture values outside this stack; locals were not read');
    final callbackConsole = debug.snapshot!.console;
    expect(callbackConsole, contains('opaque native callback boundary'));
    await _panel(tester, 'debug_console');
    expect(find.byType(EditorDebugConsolePanel), findsOneWidget);
    final console = find.byKey(const ValueKey('editor-debug-console'));
    await tester.ensureVisible(console);
    expect(_selectableText(tester, console), callbackConsole);
    expect(find.text('调试器日志'), findsOneWidget);
    expect(find.byType(TextField), findsNothing,
        reason: 'Go Debug Console must not advertise fabricated expression evaluation');
    await capture('callback-debug-console', evidence);
    await _panel(tester, 'debug');
    await _tapKey(tester, 'editor-debug-stop');
    await _until(tester, () => !debug.busy && debug.snapshot?.isTerminal == true,
        reason: 'Actual editor Stop did not release its native callback session');
    await _registryReleased(tester, callbackId);
    evidence.addAll({
      'sourceSha256': OfflineDigest.sha256(source),
      'callbackSourceSha256': OfflineDigest.sha256(callback),
      'sessionIds': fixture.sessionIds, 'breakpointLine': 5, 'steppedLine': 6,
      'pausedValue': '42', 'steppedValue': '43', 'markerAbsentWhilePaused': true,
      'stdout': '43\n', 'outputAttribution': '调试 stdout',
      'callbackConsole': callbackConsole,
      'dirtySourceSavedBeforeDebug': true, 'nativeRegistryReleased': true,
    });
    expect(tester.takeException(), isNull);
  }

  Future<void> _tools(_UiFixture fixture, Map<String, Object?> evidence) async {
    fixture.projects.setBrowsedProject(fixture.second);
    var terminalOpened = false;
    await tester.pumpWidget(app(FunctionsTab(
      store: fixture.projects, onOpenTerminal: () => terminalOpened = true,
    )));
    await tester.pump();
    expect(find.byType(ToolsGrid), findsOneWidget);
    expect(find.text('专用'), findsNothing);
    for (final title in ['Go 格式化', '导入与符号', 'Go 模块检查', 'JSON 转 Go 结构体']) {
      await _reveal(tester, find.text(title));
      expect(find.text(title).hitTestable(), findsOneWidget);
    }
    await _reveal(tester, find.text('Go 格式化'));
    await tester.tap(find.text('Go 格式化'));
    await _until(tester, () => find.byType(GoSourceToolPage).evaluate().isNotEmpty,
        reason: 'Direct formatter card did not open its actual tool');
    expect(find.text(fixture.second.name), findsOneWidget);
    final input = find.byType(TextField).first;
    await tester.enterText(input, 'package main\nfunc');
    await _tapText(tester, '格式化', button: true);
    await _until(tester, () => find.textContaining('expected').evaluate().isNotEmpty,
        reason: 'Real formatter did not display its native parser error');
    expect(find.text('格式化结果'), findsNothing);
    const unformatted = 'package main;func main(){println("tool") }';
    const formatted = 'package main\n\nfunc main() { println("tool") }\n';
    await tester.enterText(input, unformatted);
    await _tapText(tester, '格式化', button: true);
    await _until(tester, () => find.text('格式化结果').evaluate().isNotEmpty,
        reason: 'Real direct formatter did not return a formatted result');
    await _tapText(tester, '用结果替换输入');
    expect(tester.widget<TextField>(input).controller!.text, formatted);
    expect(find.text('格式化结果'), findsNothing);
    await capture('direct-go-formatter', evidence);
    await tester.pageBack();
    await tester.pump(const Duration(milliseconds: 350));
    await _reveal(tester, find.text('导入与符号'));
    await tester.tap(find.text('导入与符号'));
    await _until(tester, () => find.byType(GoSourceToolPage).evaluate().isNotEmpty,
        reason: 'Direct inspector card did not open its actual tool');
    const inspection = 'package tool\nimport alias "fmt"\n'
        'type Widget struct{}\nfunc (Widget) Run() { alias.Println("未执行") }\n';
    await tester.enterText(find.byType(TextField).first, inspection);
    await _tapText(tester, '分析源码', button: true);
    await _until(tester, () => find.text('源码结构').evaluate().isNotEmpty,
        reason: 'Actual source inspector did not render its native report');
    final reports = tester.widgetList<SelectableText>(find.byType(SelectableText))
        .map((widget) => widget.data ?? '').join('\n');
    expect(reports, contains('alias'));
    expect(reports, contains('Widget'));
    expect(reports, contains('Run'));
    await capture('direct-go-inspector', evidence);
    await tester.pageBack();
    await tester.pump(const Duration(milliseconds: 350));
    await _reveal(tester, find.text('Go 模块检查'));
    await tester.tap(find.text('Go 模块检查'));
    await _until(tester, () => find.byType(GoModuleToolPage).evaluate().isNotEmpty,
        reason: 'Direct module card did not open');
    expect(find.text(fixture.second.name), findsOneWidget);
    await _tapText(tester, '检查依赖');
    await _until(tester, () => find.textContaining('module local.test/second').evaluate().isNotEmpty,
        reason: 'Module tool did not inspect the actual current second project');
    await tester.tap(find.byType(DropdownButtonFormField<String>));
    await tester.pump(const Duration(milliseconds: 300));
    await tester.tap(find.text(fixture.first.name).last);
    await tester.pump(const Duration(milliseconds: 300));
    expect(fixture.projects.lastBrowsedProjectId, fixture.first.id);
    expect(find.textContaining('module local.test/second'), findsNothing);
    await _tapText(tester, '检查依赖');
    await _until(tester, () => find.textContaining('module local.test/first').evaluate().isNotEmpty,
        reason: 'Module tool failed to switch its owning project');
    await capture('direct-go-project-owner', evidence);
    expect(await tester.runAsync(fixture.entry.readAsString), _UiFixture.firstSource);
    expect(await tester.runAsync(fixture.secondaryEntry.readAsString), _UiFixture.secondSource);
    expect(terminalOpened, isFalse);
    evidence.addAll({
      'factory': 'actual goProfile.toolsTabBuilder -> createGoIdeTools',
      'unformattedSourceSha256': OfflineDigest.sha256(unformatted),
      'formattedSource': formatted, 'inspectionSourceSha256': OfflineDigest.sha256(inspection),
      'inspectionReport': reports, 'firstProjectPath': fixture.first.path,
      'secondProjectPath': fixture.second.path, 'projectSwitchObserved': true,
      'sourceFilesUnchanged': true,
    });
    expect(tester.takeException(), isNull);
  }

  Future<void> _workspace(_UiFixture fixture, Map<String, Object?> evidence) async {
    late SavedWorkspace saved;
    await tester.runAsync(() async {
      final result = await fixture.workspaces.save(
        name: 'Go UI workbench', members: [fixture.first, fixture.second], primary: fixture.first,
      );
      if (result.error != null || result.workspace == null) {
        throw StateError('Real named-workspace save failed: ${result.error}');
      }
      saved = result.workspace!;
      await fixture.workspaces.saveSession(saved, WorkspaceSessionSnapshot(
        primaryPath: fixture.first.path,
        documents: [
          ProjectDocumentSession(projectPath: fixture.first.path, relativePath: 'src/main.go',
            cursor: const FileCursor(baseIndex: 3, baseOffset: 2, extentIndex: 3, extentOffset: 2)),
          ProjectDocumentSession(projectPath: fixture.second.path, relativePath: 'cmd/worker.go',
            cursor: const FileCursor(baseIndex: 3, baseOffset: 4, extentIndex: 3, extentOffset: 4),
            isActive: true),
        ],
        expandedDirs: {fixture.first.path: ['src'], fixture.second.path: ['cmd']},
        rootExpanded: {fixture.first.path: true, fixture.second.path: true},
      ));
      await fixture.workspaces.load(force: true);
      saved = fixture.workspaces.byId(saved.id)!;
    });
    final host = RetainedEditorController();
    fixture.hosts.add(host);
    await tester.pumpWidget(app(const Scaffold(body: Text('Go target workspace host')), host: host));
    host.open(
      project: fixture.first, auth: fixture.auth, store: fixture.projects,
      settings: fixture.settings, workspace: saved,
      workspaceProjects: [fixture.first, fixture.second], workspaceStore: fixture.workspaces,
    );
    await _until(tester, () => find.byType(EditorProblemsBar).evaluate().isNotEmpty &&
        editor.files.length == 2 && editor.current?.projectRootPath == fixture.second.path,
        reason: 'Retained actual Go editor did not restore both named owners');
    fixture.analysis = analysis;
    fixture.debug = tester.widget<EditorDebugGutter>(find.byType(EditorDebugGutter).first).debug;
    final controller = editor;
    _expectOwners(fixture, controller, cursors: true);
    final files = controller.files.toList();
    await _openTree(tester);
    await _expandedRoots(tester, fixture);
    await capture('named-two-root-tree', evidence);
    await tester.tap(find.byTooltip('收起文件树'));
    await tester.pump(const Duration(milliseconds: 300));
    await _openTree(tester);
    await _expandedRoots(tester, fixture);
    final dirty = '${_UiFixture.secondSource}// retained target edit\n';
    controller.current!.controller.text = dirty;
    const liveCursor = CodeLineSelection.collapsed(index: 3, offset: 5);
    controller.current!.controller.selection = liveCursor;
    await tester.pump();
    expect(controller.current!.dirty, isTrue);
    await tester.tap(find.byTooltip('暂时收起编辑器'));
    final restore = find.text('返回编辑器 · ${saved.name}');
    await _until(tester, () => restore.hitTestable().evaluate().isNotEmpty,
        reason: 'Actual retained Go editor did not expose its named restore control');
    await tester.tap(restore);
    await _until(tester, () => find.byType(EditorProblemsBar).evaluate().isNotEmpty,
        reason: 'Actual retained Go editor did not restore');
    expect(editor, same(controller));
    expect(editor.files[0], same(files[0]));
    expect(editor.files[1], same(files[1]));
    expect(editor.current!.controller.text, dirty);
    expect(editor.current!.controller.selection.baseIndex, liveCursor.baseIndex);
    expect(editor.current!.controller.selection.baseOffset, liveCursor.baseOffset);
    expect(editor.current!.controller.selection.extentIndex, liveCursor.extentIndex);
    expect(editor.current!.controller.selection.extentOffset, liveCursor.extentOffset);
    expect(editor.current!.dirty, isTrue);
    if (find.byTooltip('打开文件树').evaluate().isNotEmpty) await _openTree(tester);
    await _expandedRoots(tester, fixture);
    expect(await tester.runAsync(fixture.secondaryEntry.readAsString), _UiFixture.secondSource);
    await capture('named-retained-dirty-editor', evidence);

    // Dirty buffers survive retention; ordinary persisted source remains on disk.
    // Restore its clean bytes before whole-page reconstruction, preserving cursor.
    editor.current!.controller.text = _UiFixture.secondSource;
    editor.current!.controller.selection = liveCursor;
    await _until(tester, () => analysis.checked && !analysis.pending,
        reason: 'Actual workspace analysis must finish before page reconstruction');
    await _pumpFuture(tester, fixture.debug!.close(), reason: 'Workspace editor debug controller did not close');
    await tester.pumpWidget(const SizedBox.shrink());
    await _tick(tester);
    host.dispose();
    fixture.hosts.remove(host);
    await _pumpFuture(tester, fixture.workspaces.settle(), reason: 'Named session did not persist');
    final reloaded = WorkspaceStore(root: Directory(p.join(fixture.directory.path, 'workspaces')));
    fixture.extraWorkspaces.add(reloaded);
    await tester.runAsync(() => reloaded.load());
    final reopened = reloaded.byId(saved.id)!;
    final reopenedEditor = await mount(fixture, workspace: reopened, workspaceStore: reloaded);
    await _until(tester, () => reopenedEditor.files.length == 2,
        reason: 'Disk reconstruction did not reopen both project owners');
    _expectOwners(fixture, reopenedEditor, cursors: false);
    expect(reopenedEditor.current!.controller.selection.baseIndex, liveCursor.baseIndex);
    expect(reopenedEditor.current!.controller.selection.baseOffset, liveCursor.baseOffset);
    expect(reopenedEditor.current!.controller.selection.extentIndex, liveCursor.extentIndex);
    expect(reopenedEditor.current!.controller.selection.extentOffset, liveCursor.extentOffset);
    await _openTree(tester);
    await _expandedRoots(tester, fixture);
    expect(await tester.runAsync(fixture.entry.readAsString), _UiFixture.firstSource);
    expect(await tester.runAsync(fixture.secondaryEntry.readAsString), _UiFixture.secondSource);
    final workspaceJson = (await tester.runAsync(() => File(
      p.join(fixture.directory.path, 'workspaces', '${saved.id}.json'),
    ).readAsString()))!;
    expect(workspaceJson, isNot(contains('println')));
    evidence.addAll({
      'workspaceId': saved.id, 'workspaceName': saved.name,
      'owners': [fixture.first.path, fixture.second.path],
      'documents': reopened.session.documents.map((document) => document.toJson()).toList(),
      'expandedDirectories': reopened.session.expandedDirs,
      'sidebarRecreation': true, 'retainedControllerAndTabsPreserved': true,
      'retainedDirtyBufferAndCursorPreserved': true,
      'diskReconstruction': true, 'sourceBytesUnchanged': true,
      'workspaceFileSha256': OfflineDigest.sha256(workspaceJson),
      'entryScope': 'actual named-session API plus retained editor; Home CRUD is separate',
    });
    await capture('named-disk-reconstructed', evidence);
    expect(tester.takeException(), isNull);
  }

  Future<Map<String, Object?>> publish({required bool finalReport}) async {
    final observed = records.map((record) => record['id']).toList();
    final covered = observed.length == _uiOperations.length &&
        _uiOperations.every((id) => observed.where((value) => value == id).length == 1);
    final report = <String, Object?>{
      'schemaVersion': 1, 'kind': 'actual-go-product-ui',
      'deviceExecution': goRuntimeBackendFor(Platform.operatingSystem) == GoRuntimeBackend.embeddedInterpreter,
      'os': Platform.operatingSystem, 'productKey': goProfile.productKey,
      'final': finalReport, 'requiredOperationIds': _uiOperations,
      'records': records, 'runtime': runtime, 'errors': errors,
      'pendingCleanup': pending, 'runtimeOwnershipReleased': released,
      'workingDirectory': originalCwd,
      'reportPath': p.join(root.path, 'product-ui-report.json'),
      'success': finalReport && covered && errors.isEmpty && runtime != null && released &&
          pending.isEmpty && !blocked && records.every((record) =>
              record['status'] == 'passed' && record['passed'] == true && record['cleanupConfirmed'] == true),
    };
    await tester.runAsync(() => File(report['reportPath']! as String)
        .writeAsString('${jsonEncode(report)}\n', flush: true));
    binding.reportData = {...?binding.reportData, 'goProductUiAudit': report};
    debugPrintSynchronously('QFLI_GO_PRODUCT_UI_AUDIT ${jsonEncode(report)}');
    return report;
  }
}

Future<void> _tick(WidgetTester tester) async {
  await tester.pump(const Duration(milliseconds: 20));
  await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 10)));
}

bool _analysisReturned(EditorAnalysisController analysis) {
  if (analysis.pending) return false;
  if (analysis.checked) return true;
  final reason = analysis.unavailableReason;
  // GoSourceTools.inspect creates the first prefix only after awaiting its
  // backend. EditorAnalysisController creates the second only after analyze
  // throws. The watchdog and unknown states must retain the real controller.
  return reason != null &&
      (reason.startsWith('Go source analysis: ') ||
          reason.startsWith('本地检查暂时不可用：'));
}

Future<void> _until(WidgetTester tester, bool Function() ready, {
  required String reason, Duration timeout = const Duration(seconds: 15),
}) async {
  final clock = Stopwatch()..start();
  while (!ready() && clock.elapsed < timeout) {
    await _tick(tester);
  }
  expect(ready(), isTrue, reason: reason);
}

Future<T> _pumpFuture<T>(WidgetTester tester, Future<T> future, {required String reason}) async {
  var done = false;
  late T result;
  Object? failure;
  StackTrace? failureStack;
  future.then<void>((value) { result = value; done = true; },
      onError: (Object error, StackTrace stack) { failure = error; failureStack = stack; done = true; });
  await _until(tester, () => done, reason: reason);
  if (failure != null) Error.throwWithStackTrace(failure!, failureStack!);
  return result;
}

Future<void> _panel(WidgetTester tester, String value) async {
  await tester.tap(find.byTooltip('更多'));
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 300));
  final item = find.byWidgetPredicate((widget) => widget is PopupMenuItem<String> && widget.value == value);
  await tester.ensureVisible(item);
  await tester.tap(item);
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 300));
}

Future<void> _tapKey(WidgetTester tester, String key) async {
  final target = find.byKey(ValueKey(key));
  await tester.ensureVisible(target);
  expect(target.hitTestable(), findsOneWidget);
  await tester.tap(target);
  await tester.pump();
}

Future<void> _tapText(WidgetTester tester, String text, {bool button = false}) async {
  final target = button ? find.widgetWithText(FilledButton, text) : find.text(text);
  await tester.ensureVisible(target);
  await tester.tap(target);
  await tester.pump();
}

Future<void> _reveal(WidgetTester tester, Finder target) async {
  // Start each direct-card lookup at the beginning; a previous card can have
  // left this lazy grid below the next requested item on a small target.
  final scrollable = find.byType(Scrollable).first;
  final state = tester.state<ScrollableState>(scrollable);
  state.position.jumpTo(state.position.minScrollExtent);
  await tester.pump();
  if (target.evaluate().isEmpty || target.hitTestable().evaluate().isEmpty) {
    await tester.scrollUntilVisible(target, 200, scrollable: find.byType(Scrollable).first);
  }
  await tester.ensureVisible(target);
}

Future<void> _gutter(WidgetTester tester, int line) async {
  final gutter = tester.widget<EditorDebugGutter>(find.byType(EditorDebugGutter).first);
  await _until(tester, () => gutter.lineBounds(line) != null,
      reason: 'Actual debug gutter has no visible geometry for line $line');
  final point = gutter.lineBounds(line)!;
  expect(gutter.lineAt(point.center), line);
  await tester.tapAt(tester.getTopLeft(find.byKey(gutter.hitTargetKey)) + point.center);
  await tester.pump();
}

Future<void> _registryReleased(WidgetTester tester, String id) async {
  expect(id, startsWith('go:'));
  final response = await tester.runAsync(() => const NativeGoDebugBackend().invoke(
    operation: 'poll', sessionId: int.parse(id.split(':').last),
  ));
  expect(response, isNotNull);
  expect(response!['ok'], isFalse, reason: 'Native registry still accepts UI session $id');
}

String _selectableText(WidgetTester tester, Finder target) {
  final widget = tester.widget<SelectableText>(target);
  return widget.data ?? widget.textSpan?.toPlainText() ?? '';
}

List<String> _wavyText(TextSpan span, [TextStyle inherited = const TextStyle()]) {
  final style = inherited.merge(span.style);
  return [
    if (span.text != null && style.decorationStyle == TextDecorationStyle.wavy &&
        style.decoration?.contains(TextDecoration.underline) == true) span.text!,
    for (final child in span.children ?? const <InlineSpan>[])
      if (child is TextSpan) ..._wavyText(child, style),
  ];
}

String _bytesHash(List<int> bytes) => OfflineDigest.sha256Bytes(bytes)
    .map((byte) => byte.toRadixString(16).padLeft(2, '0')).join();

Future<void> _openTree(WidgetTester tester) async {
  await tester.tap(find.byTooltip('打开文件树'));
  await _until(tester, () => find.byTooltip('工作区项目').hitTestable().evaluate().isNotEmpty,
      reason: 'Actual named-workspace sidebar did not open');
}

Future<void> _expandedRoots(WidgetTester tester, _UiFixture fixture) async {
  Finder entry(Project project, String name) => find.descendant(
    of: find.byKey(ValueKey('workspace-root-${project.path}')), matching: find.text(name),
  );
  await _until(tester, () => entry(fixture.first, 'main.go').hitTestable().evaluate().isNotEmpty &&
      entry(fixture.second, 'worker.go').hitTestable().evaluate().isNotEmpty,
      reason: 'Actual sidebar did not restore independently expanded src/cmd roots');
}

void _expectOwners(_UiFixture fixture, EditorController editor, {required bool cursors}) {
  expect(editor.files.map((file) => file.path), [fixture.entry.path, fixture.secondaryEntry.path]);
  expect(editor.files.map((file) => file.projectRootPath), [fixture.first.path, fixture.second.path]);
  expect(editor.files.map((file) => file.ownerProjectName), [fixture.first.name, fixture.second.name]);
  expect(editor.files.map((file) => file.projectType), ['go', 'go']);
  expect(editor.files.map((file) => file.controller.text), [_UiFixture.firstSource, _UiFixture.secondSource]);
  expect(editor.current!.projectRootPath, fixture.second.path);
  for (var index = 0; index < editor.files.length; index++) {
    expect(editor.files[index].dirty, isFalse);
    if (cursors) {
      final selection = editor.files[index].controller.selection;
      final offset = index == 0 ? 2 : 4;
      expect(selection.baseIndex, 3);
      expect(selection.extentIndex, 3);
      expect(selection.baseOffset, offset);
      expect(selection.extentOffset, offset);
    }
  }
}

class _UiFixture {
  _UiFixture(this.directory, this.first, this.second, this.projects, this.workspaces)
      : auth = AuthStore(storageFile: File(p.join(directory.path, 'auth.json'))),
        settings = SettingsStore(storageFile: File(p.join(directory.path, 'settings.json')));
  final Directory directory;
  final Project first;
  final Project second;
  final ProjectStore projects;
  final WorkspaceStore workspaces;
  final AuthStore auth;
  final SettingsStore settings;
  final hosts = <RetainedEditorController>[];
  final extraWorkspaces = <WorkspaceStore>[];
  final sessionIds = <String>[];
  EditorAnalysisController? analysis;
  EditorDebugController? debug;
  File get entry => File(p.join(first.path, 'src', 'main.go'));
  File get secondaryEntry => File(p.join(second.path, 'cmd', 'worker.go'));
  static const firstSource = 'package main\n\nfunc main() {\n  println("go-first")\n}\n';
  static const secondSource = 'package main\n\nfunc main() {\n  println("go-second")\n}\n';

  void trackCurrent() {
    final id = debug?.snapshot?.sessionId;
    if (id != null && !sessionIds.contains(id)) sessionIds.add(id);
  }

  static Future<_UiFixture> create(Directory directory) async {
    await directory.create();
    final first = Project.create(name: 'Go UI first', path: p.join(directory.path, 'first'), type: 'go', language: 'Go');
    final second = Project.create(name: 'Go UI second', path: p.join(directory.path, 'second'), type: 'go', language: 'Go');
    await Directory(p.join(first.path, 'src')).create(recursive: true);
    await Directory(p.join(second.path, 'cmd')).create(recursive: true);
    await File(p.join(first.path, 'src', 'main.go')).writeAsString(firstSource);
    await File(p.join(second.path, 'cmd', 'worker.go')).writeAsString(secondSource);
    await File(p.join(first.path, 'go.mod')).writeAsString('module local.test/first\ngo 1.24\n');
    await File(p.join(second.path, 'go.mod')).writeAsString('module local.test/second\ngo 1.24\n');
    final registry = File(p.join(directory.path, 'projects.json'));
    await registry.writeAsString(jsonEncode({'projects': [first.toJson(), second.toJson()]}));
    final projects = ProjectStore(storageFile: registry);
    await projects.load();
    final workspaces = WorkspaceStore(root: Directory(p.join(directory.path, 'workspaces')));
    await workspaces.load();
    final fixture = _UiFixture(directory, first, second, projects, workspaces);
    fixture.settings.minimap = false;
    fixture.settings.autoSave = false;
    return fixture;
  }
}
