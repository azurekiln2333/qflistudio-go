import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_platform.dart';
import 'package:qfli_go/go_runner.dart';
import 'package:qfli_go/go_terminal_delegate.dart';
import 'package:qfli_go/main.dart' show goProfile;
import 'package:qfli_studio_core/editor/terminal_pane.dart';
import 'package:qfli_studio_core/pages/terminax_terminal_page.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/terminal/shell/sandbox_shell_backend.dart';

/// Regression coverage for the Go product's terminal command hook.
///
/// The Go profile did not install `terminalCommandDelegate`, so both terminal
/// surfaces reported "内置终端不支持该命令" for `go ...` even though the Go
/// toolchain and interpreter were already wired for the Run button. These tests
/// pin the wiring at the delegate boundary, plus the honest desktop/mobile
/// capability split and the two terminal contexts that read the profile field.
final String _sdk =
    Platform.environment['QFLI_GO_TEST_EXECUTABLE'] ?? 'go';
final bool _sdkAvailable = () {
  try {
    return Process.runSync(_sdk, ['version']).exitCode == 0;
  } on ProcessException {
    return false;
  }
}();

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory project;
  late StudioProfile? previous;

  setUp(() {
    previous = StudioProfile.current;
    project = Directory.systemTemp.createTempSync('qfli_go_terminal_');
  });

  tearDown(() {
    StudioProfile.current = previous;
    if (project.existsSync()) project.deleteSync(recursive: true);
  });

  void write(String relative, String content) {
    final file = File(p.join(project.path, relative));
    file.parent.createSync(recursive: true);
    file.writeAsStringSync(content);
  }

  _CapturingBackend backend({String? cwd}) =>
      _CapturingBackend(cwd ?? project.path);

  group('档位接线', () {
    test('go 档位安装了终端命令委托', () {
      // This is the actual defect: without the field both terminal surfaces
      // read `null` and every `go` line falls through to the sandbox's
      // unsupported message.
      expect(goProfile.terminalCommandDelegate, isNotNull);
    });
  });

  group('桌面终端委托（真实 SDK）', () {
    late GoTerminalDelegate delegate;

    setUp(() {
      delegate = GoTerminalDelegate(
        toolchain: GoToolchain(executable: _sdk),
        backend: GoRuntimeBackend.officialSdk,
      );
    });

    test(
      'go version 走真实工具链并透出帮助/版本',
      () async {
        final capture = backend();
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, 'go version'), isTrue);
        expect(capture.exitCode, 0);
        expect(capture.lines.join('\n'), contains('go version'));
      },
      skip: !_sdkAvailable,
    );

    test(
      '裸 go 转发到真实 SDK（保留真实退出码与帮助）',
      () async {
        final capture = backend();
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, 'go'), isTrue);
        // Go itself exits 2 and prints usage; the delegate must not fabricate a
        // different status or an empty success.
        expect(capture.exitCode, isNot(0));
        expect(capture.lines, isNotEmpty);
      },
      skip: !_sdkAvailable,
    );

    test(
      'go help 与 go env 是真实命令，不是空实现',
      () async {
        final capture = backend();
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, 'go help'), isTrue);
        expect(capture.exitCode, 0);
        expect(capture.lines.join('\n'), contains('Go is a tool'));
      },
      skip: !_sdkAvailable,
    );

    test(
      'go run 选中文件与多文件包都产出预期输出',
      () async {
        write('go.mod', 'module example.com/qfli/term\n\ngo 1.27.0\n');
        write('src/helper.go', 'package main\nfunc message() string { return "ready" }\n');
        write(
          'src/main.go',
          'package main\nimport "fmt"\nfunc main() { fmt.Println(message()) }\n',
        );

        // Multi-file package: `go run .` in the source directory keeps the
        // helper, exactly as Go itself resolves it.
        final packageRun = _CapturingBackend(p.join(project.path, 'src'));
        addTearDown(packageRun.shutdown);
        expect(await delegate.handle(packageRun, 'go run .'), isTrue);
        expect(packageRun.exitCode, 0, reason: packageRun.lines.join('\n'));
        expect(packageRun.lines, contains('ready'));

        // Single-file mode compiles only the named file, matching Go's own
        // behavior; the terminal must not silently add the helper.
        write(
          'solo/main.go',
          'package main\nimport "fmt"\nfunc main() { fmt.Println("solo") }\n',
        );
        final soloRun = _CapturingBackend(p.join(project.path, 'solo'));
        addTearDown(soloRun.shutdown);
        expect(await delegate.handle(soloRun, 'go run main.go'), isTrue);
        expect(soloRun.exitCode, 0, reason: soloRun.lines.join('\n'));
        expect(soloRun.lines, contains('solo'));
      },
      skip: !_sdkAvailable,
    );

    test(
      'go run . 忠实报告两个 main 的真实编译错误',
      () async {
        // The editor Run button applies an overlay to select one entry; the
        // terminal is a faithful `go` prompt, so the real duplicate-main error
        // must surface instead of being hidden.
        write('go.mod', 'module example.com/qfli/dup\n\ngo 1.27.0\n');
        write('src/main.go', 'package main\nfunc main() {}\n');
        write('src/main2.go', 'package main\nfunc main() {}\n');
        final capture = _CapturingBackend(p.join(project.path, 'src'));
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, 'go run .'), isTrue);
        expect(capture.exitCode, isNot(0));
        expect(capture.lines.join('\n'), contains('redeclared'));
      },
      skip: !_sdkAvailable,
    );

    test(
      'go run 失败时保留真实编译诊断',
      () async {
        write('src/main.go', 'package main\nfunc main() { unknown() }\n');
        final capture = backend();
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, 'go run src/main.go'), isTrue);
        expect(capture.exitCode, isNot(0));
        expect(capture.lines.join('\n'), contains('undefined: unknown'));
      },
      skip: !_sdkAvailable,
    );

    test(
      'go test/vet/fmt 在桌面端真实可用',
      () async {
        write('go.mod', 'module example.com/qfli/term\n\ngo 1.27.0\n');
        write('src/main.go', 'package main\nfunc main() {}\n');
        write(
          'src/helper.go',
          'package main\nfunc message() string { return "ready" }\n',
        );
        write(
          'src/helper_test.go',
          'package main\nimport "testing"\n'
              'func TestMessage(t *testing.T) { if message() != "ready" { t.Fatal("x") } }\n',
        );
        final capture = backend();
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, 'go test ./...'), isTrue);
        expect(capture.exitCode, 0, reason: capture.lines.join('\n'));
        expect(capture.lines.join('\n'), contains('ok'));
      },
      skip: !_sdkAvailable,
    );

    test(
      'go 命令在沙盒 cd 后的目录执行',
      () async {
        write('nested/main.go', 'package main\nimport "fmt"\nfunc main() { fmt.Println("nested") }\n');
        final capture = backend();
        addTearDown(capture.shutdown);
        await capture.execute('cd nested');
        expect(await delegate.handle(capture, 'go run main.go'), isTrue);
        expect(capture.exitCode, 0, reason: capture.lines.join('\n'));
        expect(capture.lines, contains('nested'));
      },
      skip: !_sdkAvailable,
    );

    test('取消运行会停止进程并返回非零状态', () async {
      write(
        'src/main.go',
        'package main\nimport ("fmt"; "time")\n'
            'func main() { fmt.Println("running"); time.Sleep(30 * time.Second) }\n',
      );
      final cancelable = _CancelableBackend(project.path);
      addTearDown(cancelable.shutdown);
      final started = Completer<void>();
      cancelable.onLine = (line) {
        if (line == 'running' && !started.isCompleted) started.complete();
      };
      final done = delegate.handle(cancelable, 'go run src/main.go');
      await started.future.timeout(const Duration(seconds: 20));
      await cancelable.cancel!.call().timeout(const Duration(seconds: 5));
      expect(await done, isTrue);
      expect(cancelable.exitCode, isNot(0));
      expect(cancelable.lines, contains('running'));
    }, skip: !_sdkAvailable);

    test('非 go 命令与复合行都不被接管', () async {
      final capture = backend();
      addTearDown(capture.shutdown);
      for (final command in <String>[
        'ls',
        'git status',
        // A tool whose name merely has a `go` stem must not be claimed.
        'go.txt',
        'go-land build',
        "./go-helper",
        'go run main.go | head',
        'go test ./... > out.txt',
        'go run "unterminated',
      ]) {
        expect(
          await delegate.handle(capture, command),
          isFalse,
          reason: 'must not claim: $command',
        );
      }
      expect(capture.lines, isEmpty);
    });

    test(
      '绝对路径操作数可直接运行',
      () async {
        write(
          'abs/main.go',
          'package main\nimport "fmt"\nfunc main() { fmt.Println("absolute") }\n',
        );
        final capture = backend();
        addTearDown(capture.shutdown);
        final absolute = p.join(project.path, 'abs', 'main.go');
        expect(await delegate.handle(capture, 'go run $absolute'), isTrue);
        expect(capture.exitCode, 0, reason: capture.lines.join('\n'));
        expect(capture.lines, contains('absolute'));
      },
      skip: !_sdkAvailable,
    );

    test(
      '带空格与中文的项目路径与操作数正常执行',
      () async {
        // Non-ASCII and spaced paths must survive tokenization (quoted operand),
        // absolute-path resolution and the real SDK invocation.
        write(
          '中文 目录/main.go',
          'package main\nimport "fmt"\nfunc main() { fmt.Println("unicode"); fmt.Println("中文输出") }\n',
        );
        final dir = p.join(project.path, '中文 目录');
        final capture = _CapturingBackend(dir);
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, 'go run "main.go"'), isTrue);
        expect(capture.exitCode, 0, reason: capture.lines.join('\n'));
        expect(capture.lines, containsAllInOrder(['unicode', '中文输出']));
      },
      skip: !_sdkAvailable,
    );

    test(
      '目录操作数按入口解析运行多文件包',
      () async {
        write('go.mod', 'module example.com/qfli/dir\n\ngo 1.27.0\n');
        write(
          'pkg/helper.go',
          'package main\nfunc message() string { return "dir-ok" }\n',
        );
        write(
          'pkg/main.go',
          'package main\nimport "fmt"\nfunc main() { fmt.Println(message()) }\n',
        );
        // `go run pkg` resolves the package directory and keeps its helper.
        final capture = backend();
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, 'go run ./pkg'), isTrue);
        expect(capture.exitCode, 0, reason: capture.lines.join('\n'));
        expect(capture.lines, contains('dir-ok'));
      },
      skip: !_sdkAvailable,
    );
  });

  group('不支持的平台', () {
    test('裸 go 与子命令都明确报告无运行时', () async {
      final delegate = GoTerminalDelegate(
        backend: GoRuntimeBackend.unavailable,
      );
      for (final command in <String>['go', 'go version', 'go run main.go']) {
        final capture = backend();
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, command), isTrue);
        expect(capture.exitCode, kProgramNotRunExitCode);
        expect(capture.lines.join('\n'), contains('没有可用的 Go 运行时'));
      }
    });
  });

  group('移动端内嵌解释器能力边界', () {
    late GoTerminalDelegate delegate;

    setUp(() {
      delegate = GoTerminalDelegate(
        backend: GoRuntimeBackend.embeddedInterpreter,
        // The stub bridge reports the mobile boundary without loading FFI.
        runner: const GoProgramRunner(
          toolchain: GoToolchain(processesSupported: false),
        ),
      );
    });

    test('go build/test/fmt/vet/mod 明确拒绝而不是空成功', () async {
      for (final command in <String>[
        'go build .',
        'go test ./...',
        'go fmt ./...',
        'go vet ./...',
        'go mod tidy',
      ]) {
        final capture = backend();
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, command), isTrue);
        expect(
          capture.exitCode,
          kProgramNotRunExitCode,
          reason: '$command must report not-run',
        );
        expect(
          capture.lines.join('\n'),
          contains('内置解释器只支持 go run'),
        );
      }
    });

    test('go run 带额外参数或模式被拒绝', () async {
      final capture = backend();
      addTearDown(capture.shutdown);
      expect(await delegate.handle(capture, 'go run -race main.go'), isTrue);
      expect(capture.exitCode, kProgramNotRunExitCode);
      expect(capture.lines.join('\n'), contains('go run <单个'));
    });

    test('go run 单文件由解释器接管（非拒绝，非空实现）', () async {
      // On the test host the embedded library is not loadable, so the shared
      // bridge reports an honest not-run boundary through stderr; the point is
      // that `go run <file>` is claimed by the interpreter path and never
      // fabricates an empty success.
      write('src/main.go', 'package main\nfunc main() {}\n');
      final capture = _CapturingBackend(p.join(project.path, 'src'));
      addTearDown(capture.shutdown);
      expect(await delegate.handle(capture, 'go run main.go'), isTrue);
      expect(capture.exitCode, isNot(0));
      expect(capture.lines, isNotEmpty);
    });

    test('go run 目录操作数缺少入口时报诚实错误', () async {
      // The interpreter's `go run <dir>` uses the editor Run-button entry
      // resolution; a directory with no Go entry must report that honestly
      // instead of running an empty package.
      Directory(p.join(project.path, 'empty')).createSync(recursive: true);
      final capture = _CapturingBackend(p.join(project.path, 'empty'));
      addTearDown(capture.shutdown);
      expect(await delegate.handle(capture, 'go run .'), isTrue);
      expect(capture.exitCode, kProgramNotRunExitCode);
      expect(capture.lines.join('\n'), contains('没有可运行的 Go 入口'));
    });

    test('go run 越出沙盒的目标报诚实错误而不抛异常', () async {
      final confined = _CapturingBackend(p.join(project.path, 'inner'));
      Directory(p.join(project.path, 'inner')).createSync(recursive: true);
      addTearDown(confined.shutdown);
      expect(
        await delegate.handle(confined, 'go run ../outside.go'),
        isTrue,
      );
      expect(confined.exitCode, kProgramNotRunExitCode);
      expect(confined.lines.join('\n'), contains('不能越出沙盒目录'));
    });

    test('go run 沙盒内子目录的相对路径可正常解析', () async {
      // A subdirectory target reached from the sandbox root is inside the
      // boundary and must resolve, matching the sandbox file-command rules.
      StudioProfile.current = goProfile;
      write('go.mod', 'module example.com/qfli/subpath\n\ngo 1.27.0\n');
      write(
        'sub/main.go',
        'package main\nimport "fmt"\nfunc main() { fmt.Println("subpath-ok") }\n',
      );
      final resolved = GoTerminalDelegate(
        backend: GoRuntimeBackend.embeddedInterpreter,
        runner: GoProgramRunner(toolchain: GoToolchain(executable: _sdk)),
      );
      final capture = _CapturingBackend(project.path);
      addTearDown(capture.shutdown);
      expect(await resolved.handle(capture, 'go run sub/main.go'), isTrue);
      expect(capture.exitCode, 0, reason: capture.lines.join('\n'));
      expect(capture.lines, contains('subpath-ok'));
    }, skip: !_sdkAvailable);

    test('go run 目录操作数按配置入口解析后交给运行器', () async {
      // The mobile `go run <dir>` resolves the entry the same way the Run
      // button does, which includes the active profile's entry names. On this
      // host the injected runner still runs through the desktop SDK, so the
      // assertion proves the resolved entry reached the runner
      // (src/main.go, not the hardcoded main.go).
      StudioProfile.current = goProfile;
      write('go.mod', 'module example.com/qfli/mobiledir\n\ngo 1.27.0\n');
      write(
        'src/helper.go',
        'package main\nfunc message() string { return "mobile-dir" }\n',
      );
      write(
        'src/main.go',
        'package main\nimport "fmt"\nfunc main() { fmt.Println(message()) }\n',
      );
      final resolved = GoTerminalDelegate(
        backend: GoRuntimeBackend.embeddedInterpreter,
        runner: GoProgramRunner(toolchain: GoToolchain(executable: _sdk)),
      );
      final capture = _CapturingBackend(project.path);
      addTearDown(capture.shutdown);
      expect(await resolved.handle(capture, 'go run src'), isTrue);
      expect(capture.exitCode, 0, reason: capture.lines.join('\n'));
      expect(capture.lines, contains('mobile-dir'));
    }, skip: !_sdkAvailable);

    test('裸 go 与 go version 在移动端无通用命令', () async {
      for (final command in <String>['go', 'go version']) {
        final capture = backend();
        addTearDown(capture.shutdown);
        expect(await delegate.handle(capture, command), isTrue);
        expect(capture.exitCode, kProgramNotRunExitCode);
      }
    });
  });

  group('两个终端界面都读取档位委托', () {
    testWidgets('独立终端页使用 go 档位委托', (tester) async {
      StudioProfile.current = goProfile;
      final executed = <String>[];
      // Wrap the real profile delegate so the widget test can observe the call
      // without depending on a real shell; the assertion is that the shared
      // page installs the profile field, not that the delegate body runs.
      StudioProfile.current = _withRecordingDelegate(goProfile, executed);
      final store = ProjectStore();
      addTearDown(store.dispose);
      await _mountStandalone(tester, store);
      await _pumpIoUntil(tester, () => tester.any(find.byType(TextField)));
      await _drive(tester, 'go version');
      await _pumpIoUntil(tester, () => executed.isNotEmpty);
      expect(executed, ['go version']);
      expect(tester.takeException(), isNull);
    });

    testWidgets('编辑器 TerminalPane 使用 go 档位委托', (tester) async {
      StudioProfile.current = goProfile;
      final executed = <String>[];
      StudioProfile.current = _withRecordingDelegate(goProfile, executed);
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: TerminalPane(
              workingDirectory: project.path,
              auth: AuthStore(),
              onlineEnabled: false,
            ),
          ),
        ),
      );
      await tester.pump();
      await _pumpIoUntil(tester, () => tester.any(find.byType(TextField)));
      await _drive(tester, 'go version');
      await _pumpIoUntil(tester, () => executed.isNotEmpty);
      expect(executed, ['go version']);
      expect(tester.takeException(), isNull);
    });
  });
}

/// Returns [base] with a terminal delegate that records every `go ...` line and
/// reports a clean exit, so a widget test can prove the profile field reached
/// the shared terminal without launching a real process.
StudioProfile _withRecordingDelegate(
  StudioProfile base,
  List<String> executed,
) => StudioProfile(
  id: base.id,
  appTitle: base.appTitle,
  templates: base.templates,
  runner: base.runner,
  isOffline: base.isOffline,
  offlineOnly: base.offlineOnly,
  supportedFileExtensions: base.supportedFileExtensions,
  entryFileNames: base.entryFileNames,
  terminalCommandDelegate: (backend, command) async {
    if (!command.startsWith('go ')) return false;
    executed.add(command);
    await backend.runStreams(
      title: command,
      stdout: Stream<String>.value('go version go1.27.1'),
      stderr: const Stream<String>.empty(),
      exitCode: Future<int>.value(0),
    );
    return true;
  },
);

Future<void> _mountStandalone(WidgetTester tester, ProjectStore store) async {
  addTearDown(() async {
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 20)),
    );
  });
  await tester.pumpWidget(MaterialApp(home: TerminaxTerminalPage(store: store)));
  await tester.pump();
}

Future<void> _drive(WidgetTester tester, String command) async {
  final field = find.byType(TextField).last;
  await tester.showKeyboard(field);
  await tester.enterText(field, command);
  await tester.testTextInput.receiveAction(TextInputAction.done);
}

Future<void> _pumpIoUntil(
  WidgetTester tester,
  bool Function() condition, {
  int attempts = 400,
}) async {
  for (var attempt = 0; attempt < attempts; attempt++) {
    await tester.pump(const Duration(milliseconds: 20));
    if (condition()) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  expect(condition(), isTrue, reason: 'The terminal operation did not finish.');
}

/// Minimal backend that captures the streamed output and exit status.
class _CapturingBackend extends SandboxShellBackend {
  _CapturingBackend(String root) : super(sandboxRoot: root);

  final lines = <String>[];
  int? exitCode;

  @override
  Future<void> runStreams({
    required String title,
    required Stream<String> stdout,
    required Stream<String> stderr,
    required Future<int> exitCode,
    Future<void> Function()? cancel,
  }) async {
    // Drain both pipes concurrently: draining one to completion first can
    // deadlock a process that fills the other pipe's buffer.
    final outDone = stdout.listen(lines.add).asFuture<void>();
    final errDone = stderr.listen(lines.add).asFuture<void>();
    await Future.wait<void>([outDone, errDone]);
    this.exitCode = await exitCode;
  }
}

/// Backend that exposes the delegate's cancellation handle and streams lines as
/// they arrive, so a running-program cancellation can be observed.
class _CancelableBackend extends SandboxShellBackend {
  _CancelableBackend(String root) : super(sandboxRoot: root);

  final lines = <String>[];
  int? exitCode;
  Future<void> Function()? cancel;
  void Function(String line)? onLine;

  @override
  Future<void> runStreams({
    required String title,
    required Stream<String> stdout,
    required Stream<String> stderr,
    required Future<int> exitCode,
    Future<void> Function()? cancel,
  }) async {
    this.cancel = cancel;
    final outDone = stdout.listen((line) {
      lines.add(line);
      onLine?.call(line);
    }).asFuture<void>();
    final errDone = stderr.listen(lines.add).asFuture<void>();
    await Future.wait<void>([outDone, errDone]);
    this.exitCode = await exitCode;
  }
}
