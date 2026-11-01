import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/process_supervisor.dart';
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

  /// Applies to SDK children only; host/user Go configuration is never changed.
  static const offlineEnvironment = <String, String>{
    'GOPROXY': 'off',
    'GOSUMDB': 'off',
    'GONOPROXY': 'none',
    'GOVCS': '*:off',
    'GOTOOLCHAIN': 'local',
    // Go reads telemetry mode from its config file, not GOTELEMETRY. This
    // child marker makes the SDK skip its telemetry uploader startup.
    'GO_TELEMETRY_CHILD': '2',
  };

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
      if (action == GoToolAction.run && entryFile.endsWith('_test.go')) {
        // A selected test file runs its real package tests, fuzz seeds and
        // benchmarks through the official SDK, rather than looking for main.
        args = ['test', '-count=1', '-v', '-bench=.', '-benchmem', '.'];
      } else if (action == GoToolAction.run) {
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

      final _GoSdkProcess process;
      try {
        process = _GoSdkProcess(
          await ProcessSupervisor().start(
            executable,
            args,
            workingDirectory: workingDirectory,
            environment: {
              ...offlineEnvironment,
              if (moduleDirectory == null) 'GO111MODULE': 'off',
            },
          ),
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
        cancel: process.cancel,
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

    final policyError = _offlineCommandError(rest);
    if (policyError != null) return _unavailable(policyError);

    final _GoSdkProcess process;
    try {
      process = _GoSdkProcess(
        await ProcessSupervisor().start(
          executable,
          rest,
          workingDirectory: workingDirectory,
          environment: offlineEnvironment,
        ),
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
      cancel: process.cancel,
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
    if (action == GoToolAction.run) {
      final operation = entryFile.endsWith('_test.go') ? 'test' : 'run';
      return 'go $operation ${p.basename(entryFile)}';
    }
    return 'go ${args.join(' ')}';
  }

  static Stream<String> _lines(Stream<List<int>> stream) =>
      stream.transform(utf8.decoder).transform(const LineSplitter());

  static String? _offlineCommandError(List<String> arguments) {
    var index = 0;
    while (index < arguments.length) {
      if (arguments[index] == '-C') {
        index += 2;
      } else if (arguments[index].startsWith('-C=')) {
        index++;
      } else {
        break;
      }
    }
    if (index >= arguments.length) return null;
    final command = arguments[index];
    final rest = arguments.skip(index + 1);
    if (command == 'get' ||
        command == 'bug' ||
        command == 'telemetry' ||
        (command == 'mod' && rest.firstOrNull == 'download')) {
      return '离线版本不提供 go $command${command == 'mod' ? ' download' : ''}；不会下载依赖或打开网络服务。';
    }
    if (command == 'env' &&
        rest.any(
          (arg) =>
              arg == '-w' ||
              arg.startsWith('-w=') ||
              arg == '-u' ||
              arg.startsWith('-u='),
        )) {
      return '离线版本不支持 go env -w/-u 修改全局 Go 配置。';
    }
    return null;
  }

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
}

/// Retains SDK output from process attachment until the terminal subscribes.
/// ManagedProcess drains its pipes through broadcast streams, so a short
/// command can finish while the terminal is still awaiting stdin closure.
class _GoSdkProcess {
  _GoSdkProcess(this._process) {
    _process.stdout.listen(
      _stdout.add,
      onError: _stdout.addError,
      onDone: () => unawaited(_stdout.close()),
    );
    _process.stderr.listen(
      _stderr.add,
      onError: _stderr.addError,
      onDone: () => unawaited(_stderr.close()),
    );
  }

  final ManagedProcess _process;
  final _stdout = StreamController<List<int>>();
  final _stderr = StreamController<List<int>>();

  Stream<List<int>> get stdout => _stdout.stream;
  Stream<List<int>> get stderr => _stderr.stream;
  IOSink get stdin => _process.stdin;
  Future<int> get exitCode => _process.exitCode;
  Future<void> cancel() => _process.cancel();
}

class GoProgramRunner implements ProgramRunner {
  const GoProgramRunner({this.toolchain = const GoToolchain(), this.backend});

  final GoToolchain toolchain;
  final GoRuntimeBackend? backend;

  @override
  Future<ProgramRunResult?> run({
    required String projectPath,
    required String entryFile,
  }) {
    if (p.extension(entryFile).toLowerCase() != '.go') {
      return Future<ProgramRunResult?>.value(null);
    }
    final target =
        backend ??
        goRuntimeBackendFor(kIsWeb ? 'web' : Platform.operatingSystem);
    if (target == GoRuntimeBackend.embeddedInterpreter) {
      return native.runNativeGo(projectPath: projectPath, entryFile: entryFile);
    }
    if (target == GoRuntimeBackend.unavailable) {
      return Future<ProgramRunResult?>.value(
        GoToolchain._unavailable('当前平台没有可用的 Go 运行时。'),
      );
    }
    return toolchain.execute(
      action: GoToolAction.run,
      projectPath: projectPath,
      entryFile: entryFile,
    );
  }
}
