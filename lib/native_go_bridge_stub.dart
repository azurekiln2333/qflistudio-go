import 'package:qfli_studio_core/services/studio_profile.dart';

Future<ProgramRunResult> runNativeGo({
  required String projectPath,
  required String entryFile,
}) async => ProgramRunResult(
  title: 'Go 运行',
  stdout: const Stream<String>.empty(),
  stderr: Stream<String>.value('当前平台无法加载 Go 运行时。'),
  exitCode: Future<int>.value(kProgramNotRunExitCode),
);
