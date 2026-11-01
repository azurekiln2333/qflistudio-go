import 'dart:ffi';
import 'dart:io';
import 'dart:isolate';

import 'package:ffi/ffi.dart';
import 'package:path/path.dart' as p;

typedef _RequestNative = Pointer<Utf8> Function(Uint64, Pointer<Utf8>);
typedef _RequestDart = Pointer<Utf8> Function(int, Pointer<Utf8>);
typedef _PollNative = Pointer<Utf8> Function(Uint64, Uint64);
typedef _PollDart = Pointer<Utf8> Function(int, int);
typedef _CloseNative = Pointer<Utf8> Function(Uint64);
typedef _CloseDart = Pointer<Utf8> Function(int);
typedef _FreeNative = Void Function(Pointer<Utf8>);
typedef _FreeDart = void Function(Pointer<Utf8>);

Future<String> invokeGoDebug({
  required String operation,
  required int sessionId,
  String requestJson = '{}',
  int afterSequence = 0,
}) => Isolate.run(
  () => _invoke(operation, sessionId, requestJson, afterSequence),
);

DynamicLibrary _openRuntime() {
  final override = Platform.environment['QFLI_GO_RUNTIME_LIBRARY'];
  if (override != null && override.isNotEmpty) {
    return DynamicLibrary.open(override);
  }
  if (Platform.isIOS) return DynamicLibrary.process();
  if (Platform.isAndroid || Platform.operatingSystem == 'ohos') {
    return DynamicLibrary.open('libqfli_go_runtime.so');
  }
  final name = Platform.isWindows
      ? 'qfli_go_runtime.dll'
      : Platform.isMacOS
      ? 'libqfli_go_runtime.dylib'
      : 'libqfli_go_runtime.so';
  final directory = p.dirname(Platform.resolvedExecutable);
  Object? lastError;
  for (final candidate in [
    p.join(directory, name),
    if (Platform.isMacOS)
      p.normalize(p.join(directory, '..', 'Frameworks', name)),
    if (Platform.isLinux) p.join(directory, 'lib', name),
    name,
  ]) {
    try {
      return DynamicLibrary.open(candidate);
    } catch (error) {
      lastError = error;
    }
  }
  throw StateError('本地 Go 调试运行时不可用：$lastError');
}

String _invoke(String operation, int id, String json, int after) {
  final library = _openRuntime();
  final release = library.lookupFunction<_FreeNative, _FreeDart>('QfliGoFree');
  Pointer<Utf8> response;
  if (operation == 'start' || operation == 'command') {
    final request = json.toNativeUtf8();
    try {
      final symbol = operation == 'start'
          ? 'QfliGoDebugStart'
          : 'QfliGoDebugCommand';
      response = library.lookupFunction<_RequestNative, _RequestDart>(symbol)(
        id,
        request,
      );
    } finally {
      malloc.free(request);
    }
  } else if (operation == 'poll') {
    response = library.lookupFunction<_PollNative, _PollDart>(
      'QfliGoDebugPoll',
    )(id, after);
  } else if (operation == 'close') {
    response = library.lookupFunction<_CloseNative, _CloseDart>(
      'QfliGoDebugClose',
    )(id);
  } else {
    throw ArgumentError.value(operation, 'operation');
  }
  if (response == nullptr) throw StateError('Go 调试器返回了空结果');
  try {
    return response.toDartString();
  } finally {
    release(response);
  }
}
