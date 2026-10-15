import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/runner_service.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/terminal/shell/command_parser.dart';
import 'package:qfli_studio_core/terminal/shell/sandbox_shell_backend.dart';

import 'go_platform.dart';
import 'go_runner.dart';

/// The Go product's command hook for the shared in-app terminal.
///
/// Both terminal surfaces read [StudioProfile.terminalCommandDelegate]: the
/// standalone terminal page (`TerminaxTerminalPage`) and the editor's
/// `TerminalPane`. This is the single delegate both of them install, so `go ...`
/// behaves the same in either place.
///
/// The host is a language product with two different execution backends, so the
/// delegate claims exactly what the current backend can really do and refuses
/// the rest instead of faking output:
///
/// * Desktop (`official-go-sdk`): every `go` line, including a bare `go`, runs
///   through [GoToolchain.runTerminalCommand] in the sandbox cwd, so help text,
///   errors, exit codes and cancellation are the real toolchain's.
/// * Mobile (`embedded-go-runtime`): only an actual program run (`go run` with a
///   local file or directory) is supported by the embedded interpreter. The
///   interpreter has no `go build`/`test`/`fmt`/`vet`/`mod`, no module
///   downloads and no generic `go` prompt, so those lines are refused with an
///   honest message and a nonzero status rather than an empty success.
/// * Unsupported targets: every `go` line reports that no Go runtime is present.
///
/// Returns false for a non-`go` command and for any line the sandbox must own
/// (empty input, pipes, redirection, chaining, globs, quoting errors), so the
/// shared backend keeps its own honest diagnostics.
Future<bool> goTerminalCommandDelegate(
  SandboxShellBackend backend,
  String command,
) => GoTerminalDelegate().handle(backend, command);

/// The delegate implementation.
///
/// Split from [goTerminalCommandDelegate] so a test can inject a [GoToolchain]
/// with an explicit SDK path or a platform override, instead of the product
/// having to read a test environment variable.
class GoTerminalDelegate {
  const GoTerminalDelegate({
    this.toolchain = const GoToolchain(),
    this.backend,
    this.runner = const GoProgramRunner(),
  });

  /// Desktop toolchain used for the `go ...` line.
  final GoToolchain toolchain;

  /// Overrides the platform backend for tests; null uses the host platform.
  final GoRuntimeBackend? backend;

  /// Mobile program runner used for `go run`.
  final GoProgramRunner runner;

  Future<bool> handle(SandboxShellBackend backend, String command) async {
    // Match the sandbox's Windows-literal policy so a `C:\dir` operand survives
    // tokenization; classification and tokenization must agree.
    const policy = EscapePolicy.backslashLiteral;
    if (CommandParser.classify(command, escapePolicy: policy) !=
        CommandSyntax.simple) {
      return false;
    }
    final parsed = CommandParser.tokenize(command, escapePolicy: policy);
    if (!parsed.ok || parsed.tokens.isEmpty) return false;
    final tokens = parsed.tokens.map((token) => token.text).toList();
    // Accept exactly `go` / `go.exe`, not arbitrary tools whose name merely has
    // a `go` stem (`go.txt`, `go-land`).
    final tool = p.basename(tokens.first).toLowerCase();
    if (tool != 'go' && tool != 'go.exe') return false;

    final target =
        this.backend ??
        goRuntimeBackendFor(kIsWeb ? 'web' : Platform.operatingSystem);

    switch (target) {
      case GoRuntimeBackend.officialSdk:
        // A bare `go` is forwarded like every other line: the real SDK owns its
        // help text and its exit status (currently 2).
        return _runDesktopGo(backend, tokens);
      case GoRuntimeBackend.embeddedInterpreter:
        if (tokens.length == 1) {
          await backend.runStreams(
            title: 'go',
            stdout: const Stream<String>.empty(),
            stderr: Stream<String>.value(
              '移动端内置 Go 运行时只支持 go run 运行程序，没有通用的 go 命令。',
            ),
            exitCode: Future<int>.value(kProgramNotRunExitCode),
          );
          return true;
        }
        return _runEmbeddedGoRun(backend, tokens);
      case GoRuntimeBackend.unavailable:
        await backend.runStreams(
          title: tokens.length == 1
              ? 'go'
              : 'go ${tokens.sublist(1).join(' ')}',
          stdout: const Stream<String>.empty(),
          stderr: Stream<String>.value('当前平台没有可用的 Go 运行时。'),
          exitCode: Future<int>.value(kProgramNotRunExitCode),
        );
        return true;
    }
  }

  /// Desktop: forward the whole `go ...` line to the official SDK in the
  /// sandbox cwd. The toolchain owns package semantics, diagnostics and status.
  Future<bool> _runDesktopGo(
    SandboxShellBackend backend,
    List<String> arguments,
  ) async {
    final result = await toolchain.runTerminalCommand(
      workingDirectory: backend.cwd,
      arguments: arguments,
    );
    if (result == null) return false;
    await backend.runStreams(
      title: result.title,
      stdout: result.stdout,
      stderr: result.stderr,
      exitCode: result.exitCode,
      cancel: result.cancel,
    );
    return true;
  }

  /// Mobile: run the selected source with the embedded interpreter through the
  /// exact same [GoProgramRunner] path the editor Run button uses, so the two
  /// surfaces cannot drift. Anything the interpreter does not provide is
  /// refused with a real reason and the not-run exit code.
  Future<bool> _runEmbeddedGoRun(
    SandboxShellBackend backend,
    List<String> arguments,
  ) async {
    if (arguments.length < 2 || arguments[1] != 'run') {
      final subcommand = arguments.length >= 2 ? arguments[1] : '';
      await backend.runStreams(
        title: 'go ${arguments.sublist(1).join(' ')}',
        stdout: const Stream<String>.empty(),
        stderr: Stream<String>.value(
          subcommand.isEmpty
              ? '移动端内置 Go 运行时只支持 go run 运行程序，没有通用的 go 命令。'
              : '移动端内置 Go 运行时不含 go $subcommand；'
                    '内置解释器只支持 go run 运行单个程序。',
        ),
        exitCode: Future<int>.value(kProgramNotRunExitCode),
      );
      return true;
    }

    final runArguments = arguments.sublist(2);
    final operand = runArguments.length == 1 ? runArguments.single : null;
    if (operand == null ||
        operand.startsWith('-') ||
        operand.endsWith('_test.go')) {
      await backend.runStreams(
        title: 'go run',
        stdout: const Stream<String>.empty(),
        stderr: Stream<String>.value(
          '移动端内置解释器只支持 go run <单个 Go 源文件或目录>；'
          '不支持额外的命令行参数、模式或测试文件。',
        ),
        exitCode: Future<int>.value(kProgramNotRunExitCode),
      );
      return true;
    }

    // Resolve through the sandbox so the same boundary rules as file commands
    // apply: paths stay inside `sandboxRoot`, and an escape is reported as a
    // terminal error instead of throwing an uncaught exception. The project
    // root is the sandbox root (the interpreter restricts itself to it), so the
    // resolved target is always inside the runner's project.
    final String target;
    try {
      target = backend.resolveSandboxPath(operand);
    } on SandboxEscapeException {
      await backend.runStreams(
        title: 'go run $operand',
        stdout: const Stream<String>.empty(),
        stderr: Stream<String>.value('go run: 不能越出沙盒目录: $operand'),
        exitCode: Future<int>.value(kProgramNotRunExitCode),
      );
      return true;
    }

    final projectPath = backend.sandboxRoot;
    // A directory operand runs the configured project entry inside it, using
    // the same resolution as the editor Run button (configured entry, then the
    // profile entry names). A file operand runs that file.
    final String entryFile;
    if (Directory(target).existsSync()) {
      final resolved = RunnerService.findEntry(target);
      if (resolved == null) {
        await backend.runStreams(
          title: 'go run $operand',
          stdout: const Stream<String>.empty(),
          stderr: Stream<String>.value(
            '目录 $operand 中没有可运行的 Go 入口（未找到入口文件）。',
          ),
          exitCode: Future<int>.value(kProgramNotRunExitCode),
        );
        return true;
      }
      entryFile = resolved;
    } else {
      entryFile = target;
    }
    final result = await runner.run(
      projectPath: projectPath,
      entryFile: entryFile,
    );
    if (result == null) {
      await backend.runStreams(
        title: 'go run $operand',
        stdout: const Stream<String>.empty(),
        stderr: Stream<String>.value('无法运行 $operand：不是可运行的 Go 源文件。'),
        exitCode: Future<int>.value(kProgramNotRunExitCode),
      );
      return true;
    }
    await backend.runStreams(
      title: result.title,
      stdout: result.stdout,
      stderr: result.stderr,
      exitCode: result.exitCode,
      cancel: result.cancel,
    );
    return true;
  }
}
