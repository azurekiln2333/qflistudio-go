import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/studio_profile.dart';

import 'go_entry_selector.dart';
import 'go_platform.dart';
import 'native_go_bridge_stub.dart'
    if (dart.library.ffi) 'native_go_bridge_ffi.dart'
    as native;

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
        (!kIsWeb &&
            goRuntimeBackendFor(Platform.operatingSystem) ==
                GoRuntimeBackend.officialSdk))) {
      return _unavailable('当前平台无法启动本地 Go 工具链。');
    }

    final entryDirectory = p.dirname(p.absolute(entryFile));
    final projectDirectory = p.absolute(projectPath);
    final moduleDirectory = _findModule(entryDirectory, projectDirectory);
    final workingDirectory = switch (action) {
      GoToolAction.run || GoToolAction.build => entryDirectory,
      _ => moduleDirectory ?? projectDirectory,
    };

    if (action == GoToolAction.modTidy && moduleDirectory == null) {
      return _unavailable('项目没有 go.mod，无法执行 go mod tidy。');
    }

    // Only the run action cares about which file is the entry. build, test,
    // fmt, vet and modTidy keep their package-wide semantics.
    Directory? overlayDirectory;
    try {
      final List<String> args;
      if (action == GoToolAction.run) {
        final competing = GoEntrySelector.competingMainSiblings(
          entryDirectory: entryDirectory,
          entryFile: p.absolute(entryFile),
        );
        if (competing.isEmpty) {
          // Ordinary single-entry package: keep the original command so the
          // selected source (including a no-main file) is diagnosed by the
          // real compiler.
          args = ['run', '.'];
        } else {
          overlayDirectory = await Directory.systemTemp.createTemp(
            'qfli_go_overlay_',
          );
          final overlay = GoEntrySelector.writeOverlay(
            directory: overlayDirectory,
            excluded: competing,
          );
          args = ['run', '-overlay', overlay.path, '.'];
        }
      } else if (action == GoToolAction.build) {
        args = ['build', '-o', _binaryPath(projectDirectory), '.'];
      } else {
        args = switch (action) {
          GoToolAction.test => ['test', './...'],
          GoToolAction.format => ['fmt', './...'],
          GoToolAction.vet => ['vet', './...'],
          GoToolAction.modTidy => ['mod', 'tidy'],
          _ => const <String>[],
        };
      }

      if (action == GoToolAction.build) {
        await Directory(
          p.join(projectDirectory, 'build'),
        ).create(recursive: true);
      }

      final Process process;
      try {
        process = await Process.start(
          executable,
          args,
          workingDirectory: workingDirectory,
          environment: moduleDirectory == null ? {'GO111MODULE': 'off'} : null,
        );
      } on ProcessException catch (error) {
        await _release(overlayDirectory);
        return _unavailable(
          '无法启动 Go 工具链：${error.message}。请安装 Go SDK 并确认 go 在 PATH 中。',
        );
      }

      // The overlay temp directory outlives the process so the compiler can
      // read the map, then is released after exit or cancellation.
      return ProgramRunResult(
        title: _titleFor(action, args, entryFile),
        stdout: _lines(process.stdout),
        stderr: _lines(process.stderr),
        exitCode: process.exitCode.whenComplete(
          () => _release(overlayDirectory),
        ),
        cancel: () => _cancel(process),
      );
    } catch (error) {
      await _release(overlayDirectory);
      if (action == GoToolAction.run && error is FileSystemException) {
        return ProgramRunResult(
          title: 'go run ${p.basename(entryFile)}',
          stdout: const Stream<String>.empty(),
          stderr: Stream<String>.value('无法准备 Go 入口：${error.message}'),
          exitCode: Future<int>.value(1),
        );
      }
      rethrow;
    }
  }

  /// Runs one raw `go <args...>` invocation typed in the built-in terminal.
  ///
  /// This is the terminal counterpart of [execute]: the shared sandbox already
  /// knows the current working directory ([workingDirectory]), so the Go tool
  /// runs there with the user's own arguments. Unlike [execute] it never
  /// rewrites the command (no package selection, no overlay): a terminal is a
  /// faithful `go` prompt, and package semantics stay with Go itself.
  ///
  /// [arguments] includes the leading `go` token; [workingDirectory] is the
  /// sandbox cwd. Returns `null` when the platform cannot launch the official
  /// SDK so the caller reports an honest capability boundary instead of a fake
  /// process.
  Future<ProgramRunResult?> runTerminalCommand({
    required String workingDirectory,
    required List<String> arguments,
  }) async {
    if (arguments.isEmpty) return null;
    final supportsProcesses =
        processesSupported ??
        (!kIsWeb &&
            goRuntimeBackendFor(Platform.operatingSystem) ==
                GoRuntimeBackend.officialSdk);
    if (!supportsProcesses) return null;
    final rest = arguments.sublist(1);

    final Process process;
    try {
      process = await Process.start(
        executable,
        rest,
        workingDirectory: workingDirectory,
      );
    } on ProcessException catch (error) {
      return ProgramRunResult(
        title: rest.isEmpty ? 'go' : 'go ${rest.first}',
        stdout: const Stream<String>.empty(),
        stderr: Stream<String>.value(
          '无法启动 Go 工具链：${error.message}。请安装 Go SDK 并确认 go 在 PATH 中。',
        ),
        exitCode: Future<int>.value(kProgramNotRunExitCode),
      );
    }

    // The in-app terminal has no interactive stdin. Close the child's stdin so
    // a command that inspects it (bare `go`, `go help`, a program reading
    // stdin) sees EOF and exits instead of blocking forever on an inherited
    // handle.
    try {
      await process.stdin.close();
    } on IOException {
      // Already closed or not piped; the run continues normally.
    }

    return ProgramRunResult(
      title: rest.isEmpty ? 'go' : 'go ${rest.join(' ')}',
      stdout: _lines(process.stdout),
      stderr: _lines(process.stderr),
      exitCode: process.exitCode,
      cancel: () => _cancel(process),
    );
  }

  static String _binaryPath(String projectDirectory) {
    final name = p.basename(projectDirectory);
    return p.join(
      projectDirectory,
      'build',
      Platform.isWindows ? '$name.exe' : name,
    );
  }

  /// A short terminal title. Run shows only the selected file, never the
  /// temporary overlay path.
  static String _titleFor(
    GoToolAction action,
    List<String> args,
    String entryFile,
  ) {
    if (action == GoToolAction.run) return 'go run ${p.basename(entryFile)}';
    return 'go ${args.join(' ')}';
  }

  static Stream<String> _lines(Stream<List<int>> stream) =>
      stream.transform(utf8.decoder).transform(const LineSplitter());

  /// Removes a per-run overlay directory once its process is done.
  static Future<void> _release(Directory? overlay) async {
    if (overlay == null) return;
    try {
      await overlay.delete(recursive: true);
    } on FileSystemException {
      // Best-effort cleanup of our own temp directory.
    }
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
    if (!kIsWeb &&
        goRuntimeBackendFor(Platform.operatingSystem) ==
            GoRuntimeBackend.embeddedInterpreter) {
      return native.runNativeGo(projectPath: projectPath, entryFile: entryFile);
    }
    return toolchain.execute(
      action: GoToolAction.run,
      projectPath: projectPath,
      entryFile: entryFile,
    );
  }
}
