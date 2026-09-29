import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_runner.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';

void main() {
  final sdk = Platform.environment['QFLI_GO_TEST_EXECUTABLE'] ?? 'go';
  final available = () {
    try {
      return Process.runSync(sdk, ['version']).exitCode == 0;
    } on ProcessException {
      return false;
    }
  }();

  late Directory project;
  late String entry;

  setUp(() {
    project = Directory.systemTemp.createTempSync('qfli_go_toolchain_');
    entry = p.join(project.path, 'src', 'main.go');
    File(entry).parent.createSync(recursive: true);
    File(entry).writeAsStringSync('''package main
import "fmt"
func main() { fmt.Println(message()) }
''');
    File(p.join(project.path, 'src', 'helper.go')).writeAsStringSync(
      'package main\nfunc message() string { return "ready" }\n',
    );
    File(p.join(project.path, 'src', 'helper_test.go')).writeAsStringSync(
      '''package main
import "testing"
func TestMessage(t *testing.T) {
  if message() != "ready" { t.Fatal("wrong message") }
}
''',
    );
  });

  tearDown(() {
    project.deleteSync(recursive: true);
  });

  test('missing SDK reports not-run, not a program failure', () async {
    final result = await const GoToolchain(executable: '__missing_go_sdk__')
        .execute(
          action: GoToolAction.run,
          projectPath: project.path,
          entryFile: entry,
        );
    expect(await result.stderr.join(), contains('Go SDK'));
    expect(await result.exitCode, kProgramNotRunExitCode);
  });

  test('unsupported platform reports not-run without launching Go', () async {
    final result = await const GoToolchain(processesSupported: false).execute(
      action: GoToolAction.run,
      projectPath: project.path,
      entryFile: entry,
    );
    expect(await result.stderr.join(), contains('当前平台'));
    expect(await result.exitCode, kProgramNotRunExitCode);
  });

  test(
    'official SDK runs, builds, tests and checks a multi-file project',
    () async {
      final toolchain = GoToolchain(executable: sdk);

      Future<(int, String, String)> execute(GoToolAction action) async {
        final result = await toolchain.execute(
          action: action,
          projectPath: project.path,
          entryFile: entry,
        );
        final output = result.stdout.join('\n');
        final errors = result.stderr.join('\n');
        return (await result.exitCode, await output, await errors);
      }

      final run = await execute(GoToolAction.run);
      expect(run.$1, 0, reason: run.$3);
      expect(run.$2, 'ready');

      final build = await execute(GoToolAction.build);
      expect(build.$1, 0, reason: build.$3);
      expect(
        File(
          p.join(
            project.path,
            'build',
            Platform.isWindows
                ? '${p.basename(project.path)}.exe'
                : p.basename(project.path),
          ),
        ).existsSync(),
        isTrue,
      );

      final tests = await execute(GoToolAction.test);
      expect(tests.$1, 0, reason: tests.$3);
      expect(tests.$2, contains('ok'));

      final format = await execute(GoToolAction.format);
      expect(format.$1, 0, reason: format.$3);

      final vet = await execute(GoToolAction.vet);
      expect(vet.$1, 0, reason: vet.$3);

      File(
        entry,
      ).writeAsStringSync('package main\nfunc main() { unknown() }\n');
      final invalid = await execute(GoToolAction.run);
      expect(invalid.$1, isNot(0));
      expect(invalid.$3, contains('undefined: unknown'));

      File(entry).writeAsStringSync(
        'package main\nimport "fmt"\nfunc main() { fmt.Println(message()) }\n',
      );
      File(
        p.join(project.path, 'go.mod'),
      ).writeAsStringSync('module example.com/qfli/test\n\ngo 1.27.0\n');
      final tidy = await execute(GoToolAction.modTidy);
      expect(tidy.$1, 0, reason: tidy.$3);
      final moduleRun = await execute(GoToolAction.run);
      expect(moduleRun.$1, 0, reason: moduleRun.$3);
      expect(moduleRun.$2, 'ready');
    },
    skip: !available,
  );
}
