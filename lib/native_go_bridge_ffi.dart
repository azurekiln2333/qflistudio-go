import 'dart:convert';
import 'dart:ffi';
import 'dart:io';
import 'dart:isolate';

import 'package:ffi/ffi.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';

typedef _RunNative =
    Pointer<Utf8> Function(Uint64, Pointer<Utf8>, Pointer<Utf8>);
typedef _RunDart = Pointer<Utf8> Function(int, Pointer<Utf8>, Pointer<Utf8>);
typedef _FreeNative = Void Function(Pointer<Utf8>);
typedef _FreeDart = void Function(Pointer<Utf8>);
typedef _CancelNative = Void Function(Uint64);
typedef _CancelDart = void Function(int);

int _nextRunId = 0;

DynamicLibrary _openRuntime() => Platform.isIOS
    ? DynamicLibrary.process()
    : DynamicLibrary.open('libqfli_go_runtime.so');

Future<ProgramRunResult> runNativeGo({
  required String projectPath,
  required String entryFile,
}) async {
  final id = ++_nextRunId;
  var finished = false;
  final response = Isolate.run(() => _invoke(id, projectPath, entryFile))
      .then((encoded) {
        final data = jsonDecode(encoded) as Map<String, dynamic>;
        return (
          stdout: data['stdout'] as String,
          stderr: data['stderr'] as String,
          exitCode: data['exitCode'] as int,
        );
      })
      .catchError((Object error) {
        return (
          stdout: '',
          stderr: '无法加载 Go 运行时：$error',
          exitCode: kProgramNotRunExitCode,
        );
      })
      .whenComplete(() => finished = true);

  return ProgramRunResult(
    title: '运行 Go',
    stdout: response.asStream().expand(
      (result) => const LineSplitter().convert(result.stdout),
    ),
    stderr: response.asStream().expand(
      (result) => const LineSplitter().convert(result.stderr),
    ),
    exitCode: response.then((result) => result.exitCode),
    cancel: () async {
      if (!finished) _cancel(id);
    },
  );
}

String _invoke(int id, String projectPath, String entryFile) {
  final library = _openRuntime();
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
    final library = _openRuntime();
    library.lookupFunction<_CancelNative, _CancelDart>('QfliGoCancel')(id);
  } catch (_) {
    // The run future reports the load failure through stderr.
  }
}
