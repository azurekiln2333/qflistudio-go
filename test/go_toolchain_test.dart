import 'dart:async';
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

  Future<(int, String, String)> runEntry(String entryFile) async {
    final result = await GoToolchain(executable: sdk).execute(
      action: GoToolAction.run,
      projectPath: project.path,
      entryFile: entryFile,
    );
    expect(result.title, 'go run ${p.basename(entryFile)}');
    final output = result.stdout.join('\n');
    final errors = result.stderr.join('\n');
    return (await result.exitCode, await output, await errors);
  }

  test('missing SDK reports not-run, not a program failure', () async {
    File(
      p.join(File(entry).parent.path, 'main2.go'),
    ).writeAsStringSync('package main\nfunc main() {}\n');
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
    'entry preparation failures are not reported as missing runtime',
    () async {
      final result = await const GoToolchain(executable: '__missing_go_sdk__')
          .execute(
            action: GoToolAction.run,
            projectPath: project.path,
            entryFile: p.join(project.path, 'missing', 'main.go'),
          );
      expect(await result.exitCode, 1);
      expect(await result.stderr.join(), contains('无法准备 Go 入口'));
      expect(result.title, 'go run main.go');
    },
  );

  test(
    'Go filename casing and Windows entry spelling select the same source',
    () async {
      final source = File(entry).parent;
      final alternate = File(p.join(source.path, 'other_TEST.go'));
      alternate.writeAsStringSync(
        'package main\nimport "fmt"\nfunc main() { fmt.Println("suffix", message()) }\n',
      );
      File(
        p.join(source.path, 'ignored.GO'),
      ).writeAsStringSync('invalid Go source');
      final normal = await runEntry(entry);
      expect(normal.$1, 0, reason: normal.$3);
      expect(normal.$2, 'ready');
      final other = await runEntry(alternate.path);
      expect(other.$1, 0, reason: other.$3);
      expect(other.$2, 'suffix ready');
      if (Platform.isWindows) {
        final upper = await runEntry(p.join(source.path, 'MAIN.GO'));
        expect(upper.$1, 0, reason: upper.$3);
        expect(upper.$2, 'ready');
      }
    },
    skip: !available,
  );

  test(
    'symlink entries are selected and never used as a helper fallback',
    () async {
      final source = File(entry).parent;
      final target = File(p.join(source.path, 'alternate.txt'))
        ..writeAsStringSync(
          'package main\nimport "fmt"\nfunc main() { fmt.Println("linked", message()) }\n',
        );
      final alternate = Link(p.join(source.path, 'alternate.go'));
      try {
        alternate.createSync(target.path);
      } on FileSystemException catch (error) {
        markTestSkipped('Symlinks unavailable: ${error.message}');
        return;
      }
      final normal = await runEntry(entry);
      expect(normal.$1, 0, reason: normal.$3);
      expect(normal.$2, 'ready');
      final linked = await runEntry(alternate.path);
      expect(linked.$1, 0, reason: linked.$3);
      expect(linked.$2, 'linked ready');
      final helper = await runEntry(p.join(source.path, 'helper.go'));
      expect(helper.$1, 1, reason: helper.$3);
      expect(helper.$2, isEmpty);
      expect(helper.$3, contains('function main is undeclared'));
    },
    skip: !available,
  );

  test(
    'selected ignored sources fail with the real missing-main diagnostic',
    () async {
      final ignored = File(p.join(File(entry).parent.path, '_ignored.go'))
        ..writeAsStringSync('package main\nfunc main() {}\n');
      final result = await runEntry(ignored.path);
      expect(result.$1, 1, reason: result.$3);
      expect(result.$2, isEmpty);
      expect(result.$3, contains('function main is undeclared'));
    },
    skip: !available,
  );

  test(
    'retained helper syntax and encoding errors reach the compiler',
    () async {
      final helper = File(p.join(File(entry).parent.path, 'helper.go'));
      File(
        p.join(File(entry).parent.path, 'main2.go'),
      ).writeAsStringSync('package main\nfunc main() {}\n');
      helper.writeAsStringSync('package main\nfunc message(\n');
      final syntax = await runEntry(entry);
      expect(syntax.$1, 1);
      expect(syntax.$2, isEmpty);
      expect(syntax.$3, contains('helper.go'));
      expect(syntax.$3, contains('syntax error'));
      helper.writeAsBytesSync([...'package main\n'.codeUnits, 0xff]);
      final encoding = await runEntry(entry);
      expect(encoding.$1, 1);
      expect(encoding.$2, isEmpty);
      expect(encoding.$3, contains('UTF-8'));
    },
    skip: !available,
  );

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

  test(
    'run selects the chosen main among coexisting entries with helpers',
    () async {
      final source = Directory(p.join(project.path, 'src'));
      // A local package import and an embedded asset must survive the overlay.
      Directory(p.join(source.path, 'localpkg')).createSync();
      File(p.join(source.path, 'localpkg', 'pkg.go')).writeAsStringSync(
        'package localpkg\nfunc Name() string { return "pkg" }\n',
      );
      File(p.join(source.path, 'asset.txt')).writeAsStringSync('asset');
      // A platform-excluded file must remain excluded by the compiler.
      final otherOS = Platform.isWindows ? 'linux' : 'windows';
      File(
        p.join(source.path, 'only_$otherOS.go'),
      ).writeAsBytesSync([...'package main\n'.codeUnits, 0xff]);
      File(
        p.join(source.path, 'go.mod'),
      ).writeAsStringSync('module example.com/qfli/coexist\n\ngo 1.27.0\n');
      File(p.join(source.path, 'helper.go')).writeAsStringSync(
        'package main\nfunc message() string { return "helper" }\n',
      );

      String mainSource(String label) =>
          '''package main

import (
  _ "embed"
  "fmt"

  "example.com/qfli/coexist/localpkg"
)

//go:embed asset.txt
var asset string

func main() { fmt.Println("$label", message(), localpkg.Name(), asset) }
''';

      final mainEntry = File(p.join(source.path, 'main.go'))
        ..writeAsStringSync(mainSource('main'));
      final main2Entry = File(p.join(source.path, 'main2.go'))
        ..writeAsStringSync(mainSource('main2'));

      final toolchain = GoToolchain(executable: sdk);

      Future<(int, String, String)> run(String entryFile) async {
        final result = await toolchain.execute(
          action: GoToolAction.run,
          projectPath: project.path,
          entryFile: entryFile,
        );
        expect(result.title, 'go run ${p.basename(entryFile)}');
        final output = result.stdout.join('\n');
        final errors = result.stderr.join('\n');
        return (await result.exitCode, await output, await errors);
      }

      final metadata = File(p.join(project.path, '.qfli', 'project.json'));
      metadata.parent.createSync(recursive: true);
      metadata.writeAsStringSync('{"entryFile":"src/main.go"}');
      final snapshots = {
        for (final file in [mainEntry, main2Entry, metadata])
          file.path: file.readAsBytesSync(),
      };

      final main = await run(mainEntry.path);
      expect(main.$1, 0, reason: main.$3);
      expect(main.$2, 'main helper pkg asset');

      final main2 = await run(main2Entry.path);
      expect(main2.$1, 0, reason: main2.$3);
      expect(main2.$2, 'main2 helper pkg asset');

      final again = await run(mainEntry.path);
      expect(again.$1, 0, reason: again.$3);
      expect(again.$2, 'main helper pkg asset');
      for (final snapshot in snapshots.entries) {
        expect(File(snapshot.key).readAsBytesSync(), snapshot.value);
      }

      // Package tools retain their original multi-main package diagnostics.
      final build = await toolchain.execute(
        action: GoToolAction.build,
        projectPath: project.path,
        entryFile: main2Entry.path,
      );
      final buildOutput = build.stdout.drain<void>();
      final buildErrors = build.stderr.join('\n');
      expect(await build.exitCode, 1);
      expect(await buildErrors, contains('redeclared'));
      await buildOutput;

      // Selecting a helper with no main is rejected by the real compiler and
      // never runs another file's main.
      final helperEntry = File(p.join(source.path, 'helper.go'));
      final rejected = await run(helperEntry.path);
      expect(rejected.$1, 1);
      expect(rejected.$3, contains('function main is undeclared'));
      expect(rejected.$2, isEmpty);

      // A malformed selected source reaches the compiler for a real diagnostic.
      final brokenEntry = File(p.join(source.path, 'broken.go'));
      brokenEntry.writeAsStringSync('package main\nfunc main() {\n');
      final unfinishedOther = await run(mainEntry.path);
      expect(unfinishedOther.$1, 0, reason: unfinishedOther.$3);
      expect(unfinishedOther.$2, 'main helper pkg asset');
      final malformed = await run(brokenEntry.path);
      expect(malformed.$1, 1);
      expect(malformed.$2, isEmpty);
      expect(malformed.$3, contains('syntax error'));

      // Genuine compiler diagnostics stay visible through the overlay.
      mainEntry.writeAsStringSync(
        'package main\nimport "fmt"\nfunc main() { fmt.Println(missingSymbol) }\n',
      );
      final broken = await run(mainEntry.path);
      expect(broken.$1, isNot(0));
      expect(broken.$3, contains('undefined: missingSymbol'));
    },
    skip: !available,
  );

  test(
    'cancellation stops the SDK program and closes its output pipes',
    () async {
      File(
        p.join(File(entry).parent.path, 'main2.go'),
      ).writeAsStringSync('package main\nfunc main() {}\n');
      File(entry).writeAsStringSync('''package main
import (
  "fmt"
  "time"
)
func main() {
  fmt.Println("running")
  time.Sleep(30 * time.Second)
  fmt.Println("finished")
}
''');
      final result = await GoToolchain(executable: sdk).execute(
        action: GoToolAction.run,
        projectPath: project.path,
        entryFile: entry,
      );
      final started = Completer<void>();
      final outputClosed = Completer<void>();
      final output = <String>[];
      final subscription = result.stdout.listen((line) {
        output.add(line);
        if (line == 'running' && !started.isCompleted) started.complete();
      }, onDone: outputClosed.complete);
      final errorsClosed = result.stderr.drain<void>();
      var cancelled = false;
      try {
        await started.future.timeout(const Duration(seconds: 15));
        await result.cancel!().timeout(const Duration(seconds: 5));
        cancelled = true;
        expect(await result.exitCode, isNot(0));
        await Future.wait([
          outputClosed.future,
          errorsClosed,
        ]).timeout(const Duration(seconds: 5));
        expect(output, ['running']);
      } finally {
        if (!cancelled) await result.cancel!();
        await subscription.cancel();
      }
    },
    skip: !available,
  );
}
