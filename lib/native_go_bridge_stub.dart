import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/studio_profile.dart';

import 'native_go_result.dart';

export 'native_go_result.dart';

NativeGoExecution startNativeGo({
  required String projectPath,
  required String entryFile,
}) => NativeGoExecution(
  result: Future.value(
    const NativeGoResult(
      stdout: '',
      stderr: '当前平台无法加载 Go 运行时。',
      exitCode: kProgramNotRunExitCode,
    ),
  ),
  cancel: () async {},
);

Future<ProgramRunResult> runNativeGo({
  required String projectPath,
  required String entryFile,
}) async => ProgramRunResult(
  title: entryFile.endsWith('_test.go')
      ? 'go test ${p.basename(entryFile)}'
      : 'go run ${p.basename(entryFile)}',
  stdout: const Stream<String>.empty(),
  stderr: Stream<String>.value('当前平台无法加载 Go 运行时。'),
  exitCode: Future<int>.value(kProgramNotRunExitCode),
);
