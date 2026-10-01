import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_platform.dart';
import 'package:qfli_go/go_runner.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  final unsupported =
      goRuntimeBackendFor(Platform.operatingSystem) !=
      GoRuntimeBackend.embeddedInterpreter;

  testWidgets('bundled Go interpreter runs a multi-file program', (_) async {
    final project = await Directory.systemTemp.createTemp('qfli_go_native_');
    try {
      final source = Directory(p.join(project.path, 'src'));
      await source.create();
      final entry = File(p.join(source.path, 'main.go'));
      await entry.writeAsString('''package main
import "fmt"
func main() { fmt.Println(message()) }
''');
      await File(p.join(source.path, 'helper.go')).writeAsString(
        'package main\nfunc message() string { return "ready" }\n',
      );

      final result = await const GoProgramRunner().run(
        projectPath: project.path,
        entryFile: entry.path,
      );
      expect(result, isNotNull);
      final output = result!.stdout.join('\n');
      final errors = result.stderr.join('\n');
      expect(await result.exitCode, 0, reason: await errors);
      expect(await output, 'ready');
    } finally {
      await project.delete(recursive: true);
    }
  }, skip: unsupported);

  testWidgets('bundled Go interpreter reports program and worker panics', (
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

  testWidgets('bundled Go interpreter cancels an infinite program', (_) async {
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
      await Future<void>.delayed(const Duration(milliseconds: 300));
      await result.cancel!();
      expect(await result.exitCode.timeout(const Duration(seconds: 5)), 1);
      expect(await errors, contains('canceled'));
      await output;
    } finally {
      await project.delete(recursive: true);
    }
  }, skip: unsupported);
}
