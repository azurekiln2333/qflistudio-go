import 'dart:convert';
import 'dart:ffi';
import 'dart:isolate';

import 'package:ffi/ffi.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/studio_profile.dart';

import 'native_go_analysis_ffi.dart' show openGoRuntimeLibrary;
import 'native_go_result.dart';

export 'native_go_result.dart';

typedef _RunNative =
    Pointer<Utf8> Function(Uint64, Pointer<Utf8>, Pointer<Utf8>);
typedef _RunDart = Pointer<Utf8> Function(int, Pointer<Utf8>, Pointer<Utf8>);
typedef _FreeNative = Void Function(Pointer<Utf8>);
typedef _FreeDart = void Function(Pointer<Utf8>);
typedef _CancelNative = Void Function(Uint64);
typedef _CancelDart = void Function(int);

int _nextRunId = 0;

NativeGoExecution startNativeGo({
  required String projectPath,
  required String entryFile,
}) {
  final id = ++_nextRunId;
  var finished = false;
  final response = Isolate.run(() => _invoke(id, projectPath, entryFile))
      .then((encoded) {
        return NativeGoResult.decode(encoded);
      })
      .catchError((Object error) {
        return NativeGoResult(
          stdout: '',
          stderr: '无法加载 Go 运行时：$error',
          exitCode: kProgramNotRunExitCode,
        );
      })
      .whenComplete(() => finished = true);

  return NativeGoExecution(
    result: response,
    cancel: () async {
      if (!finished) _cancel(id);
    },
  );
}

Future<ProgramRunResult> runNativeGo({
  required String projectPath,
  required String entryFile,
}) async {
  final execution = startNativeGo(
    projectPath: projectPath,
    entryFile: entryFile,
  );
  final response = execution.result;

  return ProgramRunResult(
    title: entryFile.endsWith('_test.go')
        ? 'go test ${p.basename(entryFile)}'
        : 'go run ${p.basename(entryFile)}',
    stdout: response.asStream().expand(
      (result) => const LineSplitter().convert(result.stdout),
    ),
    stderr: response.asStream().expand(
      (result) => const LineSplitter().convert(result.stderr),
    ),
    exitCode: response.then((result) => result.exitCode),
    cancel: execution.cancel,
  );
}

String _invoke(int id, String projectPath, String entryFile) {
  final library = openGoRuntimeLibrary();
  final run = library.lookupFunction<_RunNative, _RunDart>('QfliGoRun');
  final release = library.lookupFunction<_FreeNative, _FreeDart>('QfliGoFree');
  final project = projectPath.toNativeUtf8();
  final entry = entryFile.toNativeUtf8();
  try {
    final result = run(id, project, entry);
    if (result == nullptr) {
      throw StateError('Go runtime returned no result');
    }
    try {
      return result.toDartString();
    } finally {
      release(result);
    }
  } finally {
    malloc.free(project);
    malloc.free(entry);
  }
}

void _cancel(int id) {
  try {
    final library = openGoRuntimeLibrary();
    library.lookupFunction<_CancelNative, _CancelDart>('QfliGoCancel')(id);
  } catch (_) {
    // The run future reports the load failure through stderr.
  }
}
