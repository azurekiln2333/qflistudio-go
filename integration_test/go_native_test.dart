import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_platform.dart';
import 'package:qfli_go/go_runner.dart';
import 'package:qfli_go/go_terminal_delegate.dart';
import 'package:qfli_go/main.dart' show goProfile;
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/terminal/shell/sandbox_shell_backend.dart';

import 'go_native_ide_acceptance.dart';
import 'go_product_ui_acceptance.dart';

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  StudioProfile? originalProfile;
  setUp(() {
    originalProfile = StudioProfile.current;
    // This integration target replaces main(), so install the real product
    // profile explicitly. Directory runs use its Go entry-file candidates.
    StudioProfile.current = goProfile;
  });
  tearDown(() => StudioProfile.current = originalProfile);

  final unsupported =
      goRuntimeBackendFor(Platform.operatingSystem) !=
      GoRuntimeBackend.embeddedInterpreter;

  Future<void> Function() waitForNativeBodies = () async {};
  void nativeTestWidgets(
    String description,
    Future<void> Function(WidgetTester tester) body, {
    required bool skip,
  }) {
    final previous = waitForNativeBodies;
    Completer<void>? ownershipReleased;
    waitForNativeBodies = () async {
      await previous();
      final released = ownershipReleased;
      if (released != null) await released.future;
    };
    testWidgets(description, (tester) async {
      final released = Completer<void>();
      ownershipReleased = released;
      await previous();
      try {
        await body(tester);
      } finally {
        // Framework observation expiry cannot release this body's native work.
        released.complete();
      }
    }, skip: skip);
  }

  nativeTestWidgets('bundled Go interpreter runs a multi-file program', (_) async {
    final project = await Directory.systemTemp.createTemp('qfli_go_native_');
    try {
      final source = Directory(p.join(project.path, 'src'));
      await source.create();
      final mainEntry = File(p.join(source.path, 'main.go'));
      await mainEntry.writeAsString('''package main
import "fmt"
func main() { fmt.Println("main", message()) }
''');
      final main2Entry = File(p.join(source.path, 'main2.go'));
      await main2Entry.writeAsString('''package main
import "fmt"
func main() { fmt.Println("main2", message()) }
''');
      await File(p.join(source.path, 'helper.go')).writeAsString(
        'package main\nfunc message() string { return "ready" }\n',
      );

      Future<(int, String, String, String)> run(String entry) async {
        final result = await const GoProgramRunner().run(
          projectPath: project.path,
          entryFile: entry,
        );
        expect(result, isNotNull);
        final output = result!.stdout.join('\n');
        final errors = result.stderr.join('\n');
        return (
          await result.exitCode,
          await output,
          await errors,
          result.title,
        );
      }

      final main = await run(mainEntry.path);
      expect(main.$1, 0, reason: main.$3);
      expect(main.$2, 'main ready');
      expect(main.$4, 'go run main.go');

      final main2 = await run(main2Entry.path);
      expect(main2.$1, 0, reason: main2.$3);
      expect(main2.$2, 'main2 ready');
      expect(main2.$4, 'go run main2.go');

      final again = await run(mainEntry.path);
      expect(again.$1, 0, reason: again.$3);
      expect(again.$2, 'main ready');
      expect(again.$4, 'go run main.go');

      // A helper selected as the entry is rejected, never runs another main.
      final helper = await run(p.join(source.path, 'helper.go'));
      expect(helper.$1, isNot(0));
      expect(helper.$3, contains('no main function'));
      expect(helper.$2, isEmpty);
      expect(helper.$4, 'go run helper.go');
    } finally {
      await project.delete(recursive: true);
    }
  }, skip: unsupported);

  nativeTestWidgets('bundled Go interpreter reports program and worker panics', (
    _,
  ) async {
    final project = await Directory.systemTemp.createTemp('qfli_go_panic_');
    try {
      final entry = File(p.join(project.path, 'main.go'));
      for (final source in [
        'package main\nfunc main() { panic("boom") }\n',
        'package main\nfunc main() { go func() { panic("boom") }(); select {} }\n',
        'package main\nimport "os"\nfunc main() { os.Exit(2) }\n',
      ]) {
        await entry.writeAsString(source);
        final result = (await const GoProgramRunner().run(
          projectPath: project.path,
          entryFile: entry.path,
        ))!;
        final output = result.stdout.join('\n');
        final errors = result.stderr.join('\n');
        expect(await result.exitCode, 1);
        expect(
          await errors,
          contains(source.contains('os.Exit') ? 'os.Exit(2)' : 'boom'),
        );
        await output;
      }
    } finally {
      await project.delete(recursive: true);
    }
  }, skip: unsupported);

  nativeTestWidgets('bundled Go interpreter cancels an infinite program', (_) async {
    final project = await Directory.systemTemp.createTemp('qfli_go_cancel_');
    try {
      final entry = File(p.join(project.path, 'main.go'));
      await entry.writeAsString('package main\nfunc main() { for {} }\n');
      final result = (await const GoProgramRunner().run(
        projectPath: project.path,
        entryFile: entry.path,
      ))!;
      final output = result.stdout.join('\n');
      final errors = result.stderr.join('\n');
      final actualExit = result.exitCode;
      await Future<void>.delayed(const Duration(milliseconds: 300));
      int? exitCode;
      try {
        await result.cancel!();
      } finally {
        exitCode = await _awaitNativeTerminal(
          actualExit,
          observation: const Duration(seconds: 5),
          binding: binding,
          caseId: 'native-infinite-program-cancel',
          fixturePath: project.path,
        );
      }
      expect(exitCode, 1);
      expect(await errors, contains('canceled'));
      await output;
    } finally {
      await project.delete(recursive: true);
    }
  }, skip: unsupported);

  nativeTestWidgets(
    'terminal delegate runs go run through the sandbox on device',
    (_) async {
      // Drives the real product path: the shared SandboxShellBackend with the
      // Go delegate installed, exactly as both terminal surfaces do. This
      // exercises the embedded interpreter through the FFI boundary rather than
      // calling GoProgramRunner directly.
      final project = await Directory.systemTemp.createTemp('qfli_go_term_');
      try {
        await File(p.join(project.path, 'helper.go')).writeAsString(
          'package main\nfunc message() string { return "term" }\n',
        );
        await File(p.join(project.path, 'main.go')).writeAsString(
          'package main\nimport "fmt"\n'
          'func main() { fmt.Println("terminal", message()) }\n',
        );

        Future<_TerminalRun> run(String command) async {
          final backend = SandboxShellBackend(
            sandboxRoot: project.path,
            startDirectory: project.path,
            delegate: goTerminalCommandDelegate,
          );
          final lines = <String>[];
          final sub = backend.output.listen((chunk) => lines.add(chunk.text));
          try {
            await backend.execute(command);
            return _TerminalRun(lines, backend.lastExitCode);
          } finally {
            await sub.cancel();
            await backend.shutdown();
          }
        }

        // A file operand runs the selected entry.
        final fileRun = await run('go run main.go');
        expect(fileRun.exitCode, 0, reason: fileRun.lines.join('\n'));
        expect(fileRun.lines.join('\n'), contains('terminal term'));

        // A directory operand resolves the configured entry inside it.
        final dirRun = await run('go run .');
        expect(dirRun.exitCode, 0, reason: dirRun.lines.join('\n'));
        expect(dirRun.lines.join('\n'), contains('terminal term'));

        // A helper without main is a real compile error, not a fallback.
        await File(
          p.join(project.path, 'helper2.go'),
        ).writeAsString('package main\nfunc helper() {}\n');
        final errorRun = await run('go run helper2.go');
        expect(errorRun.exitCode, isNot(0));
        expect(errorRun.lines.join('\n'), contains('no main function'));

        // An unsupported subcommand is refused honestly, never an empty success.
        final buildRun = await run('go build .');
        expect(buildRun.exitCode, kProgramNotRunExitCode);
        expect(buildRun.lines.join('\n'), contains('go run'));
      } finally {
        await project.delete(recursive: true);
      }
    },
    skip: unsupported,
  );

  nativeTestWidgets('terminal delegate interrupts a running go run program', (
    _,
  ) async {
    final project = await Directory.systemTemp.createTemp('qfli_go_termint_');
    try {
      // The embedded native bridge buffers stdout until the program finishes,
      // so a stdout line cannot signal "main started" before cancellation. Use a
      // marker file the program writes after entering main; Dart polls for it,
      // then interrupts. The path is a Go-quoted string literal so device paths
      // with separators or non-ASCII characters survive exactly.
      final marker = p.join(project.path, 'started.marker');
      final markerLiteral = jsonEncode(marker);
      await File(p.join(project.path, 'main.go')).writeAsString(
        'package main\nimport "os"\n'
        'func main() {\n'
        '\t_ = os.WriteFile($markerLiteral, []byte("started"), 0o644)\n'
        '\tfor {}\n'
        '}\n',
      );
      final backend = SandboxShellBackend(
        sandboxRoot: project.path,
        startDirectory: project.path,
        delegate: goTerminalCommandDelegate,
      );
      final lines = <String>[];
      final sub = backend.output.listen((chunk) => lines.add(chunk.text));
      Future<void>? execution;
      var executionFinished = false;
      try {
        execution = backend.execute('go run main.go');
        // Attach an error observer now while the marker wait runs. Awaiting the
        // original future below still preserves its error and actual lifetime.
        unawaited(execution.then<void>((_) {
          executionFinished = true;
        }, onError: (Object error, StackTrace stack) {
          executionFinished = true;
        }));
        // Explicit bounded wait: the marker proves main really ran, without
        // depending on buffered stdout.
        var markerSeen = false;
        final deadline = DateTime.now().add(const Duration(seconds: 30));
        while (DateTime.now().isBefore(deadline)) {
          if (File(marker).existsSync()) {
            markerSeen = true;
            break;
          }
          await Future<void>.delayed(const Duration(milliseconds: 100));
        }
        expect(
          markerSeen,
          isTrue,
          reason: 'the program did not enter main before the timeout',
        );
        await backend.interrupt();
        await _awaitNativeTerminal(
          execution,
          observation: const Duration(seconds: 20),
          binding: binding,
          caseId: 'terminal-go-run-interrupt',
          fixturePath: project.path,
        );
        // The interrupt is reported through the backend; a cancelled command's
        // status is not a program result.
        expect(lines.join('\n'), contains('^C'));
        expect(backend.lastExitCode, isNull);
      } finally {
        try {
          // shutdown only disposes the shell's output; it does not await its
          // delegated native execution. A failed marker assertion also needs
          // an interrupt followed by an actual drain before fixture deletion.
          if (execution != null && !executionFinished) {
            await backend.interrupt();
          }
        } finally {
          try {
            if (execution != null) await execution;
          } finally {
            await sub.cancel();
            await backend.shutdown();
          }
        }
      }
    } finally {
      await project.delete(recursive: true);
    }
  }, skip: unsupported);

  final waitForApi = registerGoNativeIdeAcceptance(
    binding: binding,
    beforeAudit: waitForNativeBodies,
  );
  registerGoProductUiAcceptance(
    binding: binding,
    beforeAudit: waitForApi,
  );
}

Future<T> _awaitNativeTerminal<T>(
  Future<T> completion, {
  required Duration observation,
  required IntegrationTestWidgetsFlutterBinding binding,
  required String caseId,
  required String fixturePath,
}) async {
  try {
    return await completion.timeout(observation);
  } on TimeoutException {
    final ownership = <String, Object?>{
      'caseId': caseId,
      'fixturePath': fixturePath,
      'nativeRunId': null,
      'nativeRunIdUnavailableReason': 'Product run/terminal handles do not expose the native numeric run ID',
      'dartResultFutureIdentity': identityHashCode(completion),
      'dartIdentityIsNativeHandle': false,
      'status': 'HOLD-native-result-pending',
      'terminalObserved': false,
      'releaseConfirmed': false,
    };
    void publish() {
      binding.reportData = {
        ...?binding.reportData,
        'goNativeExecutionOwnership': Map<String, Object?>.from(ownership),
      };
      // ignore: avoid_print
      print('QFLI_GO_NATIVE_EXECUTION_OWNERSHIP ${jsonEncode(ownership)}');
    }
    publish();
    await completion;
    ownership.addAll({
      'status': 'drained-after-timeout',
      'terminalObserved': true,
      'releaseConfirmed': true,
    });
    publish();
    throw TimeoutException(
      '$caseId exceeded its observation deadline; actual completion was drained',
      observation,
    );
  }
}

class _TerminalRun {
  const _TerminalRun(this.lines, this.exitCode);

  final List<String> lines;
  final int? exitCode;
}
