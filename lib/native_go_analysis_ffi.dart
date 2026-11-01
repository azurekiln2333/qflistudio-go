import 'dart:ffi';
import 'dart:io';
import 'dart:isolate';

import 'package:ffi/ffi.dart';
import 'package:path/path.dart' as p;

typedef _AnalyzeNative = Pointer<Utf8> Function(Pointer<Utf8>);
typedef _AnalyzeDart = Pointer<Utf8> Function(Pointer<Utf8>);
typedef _FreeNative = Void Function(Pointer<Utf8>);
typedef _FreeDart = void Function(Pointer<Utf8>);

Future<String> analyzeNativeGo(String requestJson) =>
    Isolate.run(() => _invoke('QfliGoAnalyze', requestJson));

Future<String> formatNativeGo(String requestJson) =>
    Isolate.run(() => _invoke('QfliGoFormat', requestJson));

DynamicLibrary openGoRuntimeLibrary() {
  final override = Platform.environment['QFLI_GO_RUNTIME_LIBRARY'];
  if (override != null && override.isNotEmpty) {
    return DynamicLibrary.open(override);
  }
  if (Platform.isIOS) return DynamicLibrary.process();
  if (Platform.isAndroid || Platform.operatingSystem == 'ohos') {
    return DynamicLibrary.open('libqfli_go_runtime.so');
  }
  final fileName = Platform.isWindows
      ? 'qfli_go_runtime.dll'
      : Platform.isMacOS
      ? 'libqfli_go_runtime.dylib'
      : 'libqfli_go_runtime.so';
  final executableDirectory = p.dirname(Platform.resolvedExecutable);
  final candidates = [
    p.join(executableDirectory, fileName),
    if (Platform.isMacOS)
      p.normalize(p.join(executableDirectory, '..', 'Frameworks', fileName)),
    if (Platform.isLinux) p.join(executableDirectory, 'lib', fileName),
    fileName,
  ];
  Object? lastError;
  for (final candidate in candidates) {
    try {
      return DynamicLibrary.open(candidate);
    } catch (error) {
      lastError = error;
    }
  }
  throw StateError('Go source runtime is unavailable: $lastError');
}

String _invoke(String symbol, String requestJson) {
  final library = openGoRuntimeLibrary();
  final invoke = library.lookupFunction<_AnalyzeNative, _AnalyzeDart>(symbol);
  final release = library.lookupFunction<_FreeNative, _FreeDart>('QfliGoFree');
  final request = requestJson.toNativeUtf8();
  try {
    final response = invoke(request);
    if (response == nullptr) {
      throw StateError('Go source runtime returned no result');
    }
    try {
      return response.toDartString();
    } finally {
      release(response);
    }
  } finally {
    malloc.free(request);
  }
}
