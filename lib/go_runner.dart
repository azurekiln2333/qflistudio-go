import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/studio_profile.dart';

enum GoToolAction { run, build, test, format, vet, modTidy }

/// Runs the official Go toolchain for a project on desktop platforms.
class GoToolchain {
  const GoToolchain({this.executable = 'go', this.processesSupported});

  final String executable;
  final bool? processesSupported;

  Future<ProgramRunResult> execute({
    required GoToolAction action,
    required String projectPath,
    required String entryFile,
  }) async {
    if (!(processesSupported ??
        (Platform.isWindows || Platform.isLinux || Platform.isMacOS))) {
      return _unavailable('当前平台无法启动本地 Go 工具链。');
    }

    final entryDirectory = p.dirname(p.absolute(entryFile));
    final projectDirectory = p.absolute(projectPath);
    final moduleDirectory = _findModule(entryDirectory, projectDirectory);
    final workingDirectory = switch (action) {
      GoToolAction.run || GoToolAction.build => entryDirectory,
      _ => moduleDirectory ?? projectDirectory,
    };
    final args = switch (action) {
      GoToolAction.run => ['run', '.'],
      GoToolAction.build => ['build', '-o', _binaryPath(projectDirectory), '.'],
      GoToolAction.test => ['test', './...'],
      GoToolAction.format => ['fmt', './...'],
      GoToolAction.vet => ['vet', './...'],
      GoToolAction.modTidy => ['mod', 'tidy'],
    };

    if (action == GoToolAction.modTidy && moduleDirectory == null) {
      return _unavailable('项目没有 go.mod，无法执行 go mod tidy。');
    }
    if (action == GoToolAction.build) {
      await Directory(
        p.join(projectDirectory, 'build'),
      ).create(recursive: true);
    }

    try {
      final process = await Process.start(
        executable,
        args,
        workingDirectory: workingDirectory,
        environment: moduleDirectory == null ? {'GO111MODULE': 'off'} : null,
      );
      return ProgramRunResult(
        title: 'go ${args.join(' ')}',
        stdout: process.stdout
            .transform(utf8.decoder)
            .transform(const LineSplitter()),
        stderr: process.stderr
            .transform(utf8.decoder)
            .transform(const LineSplitter()),
        exitCode: process.exitCode,
        cancel: () => _cancel(process),
      );
    } on ProcessException catch (error) {
      return _unavailable(
        '无法启动 Go 工具链：${error.message}。请安装 Go SDK 并确认 go 在 PATH 中。',
      );
    }
  }

  static String _binaryPath(String projectDirectory) {
    final name = p.basename(projectDirectory);
    return p.join(
      projectDirectory,
      'build',
      Platform.isWindows ? '$name.exe' : name,
    );
  }

  static String? _findModule(String entryDirectory, String projectDirectory) {
    var directory = entryDirectory;
    while (p.isWithin(projectDirectory, directory) ||
        p.equals(projectDirectory, directory)) {
      if (File(p.join(directory, 'go.mod')).existsSync()) return directory;
      if (p.equals(directory, projectDirectory)) break;
      directory = p.dirname(directory);
    }
    return null;
  }

  static ProgramRunResult _unavailable(String message) => ProgramRunResult(
    title: 'Go 工具链',
    stdout: const Stream<String>.empty(),
    stderr: Stream<String>.value(message),
    exitCode: Future<int>.value(kProgramNotRunExitCode),
  );

  static Future<void> _cancel(Process process) async {
    if (Platform.isWindows) {
      try {
        final result = await Process.run('taskkill', [
          '/PID',
          '${process.pid}',
          '/T',
          '/F',
        ]);
        if (result.exitCode == 0) {
          await process.exitCode;
          return;
        }
      } on ProcessException {
        // Fall through to the direct process handle.
      }
    }
    process.kill();
    await process.exitCode;
  }
}

class GoProgramRunner implements ProgramRunner {
  const GoProgramRunner({this.toolchain = const GoToolchain()});

  final GoToolchain toolchain;

  @override
  Future<ProgramRunResult?> run({
    required String projectPath,
    required String entryFile,
  }) {
    if (p.extension(entryFile).toLowerCase() != '.go') {
      return Future<ProgramRunResult?>.value(null);
    }
    return toolchain.execute(
      action: GoToolAction.run,
      projectPath: projectPath,
      entryFile: entryFile,
    );
  }
}
