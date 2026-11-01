import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'native_go_debug_stub.dart'
    if (dart.library.ffi) 'native_go_debug_ffi.dart'
    as native;

enum GoDebugCommand {
  continueExecution('continue'),
  stepInto('stepInto'),
  stepOver('stepOver'),
  stepOut('stepOut'),
  pause('pause'),
  stop('stop');

  const GoDebugCommand(this.wireName);
  final String wireName;
}

/// Native callbacks have logical execution owners, not physical goroutine IDs.
enum GoDebugExecutionKind {
  goroutine('Goroutine'),
  nativeCallback('Native callback');

  const GoDebugExecutionKind(this.label);
  final String label;

  String nameFor(int id) => '$label $id';
}

class GoDebugException implements Exception {
  const GoDebugException(this.message);
  final String message;
  @override
  String toString() => message;
}

abstract interface class GoDebugBackend {
  Future<Map<String, dynamic>> invoke({
    required String operation,
    required int sessionId,
    Map<String, Object?> request = const {},
    int afterSequence = 0,
  });
}

class NativeGoDebugBackend implements GoDebugBackend {
  const NativeGoDebugBackend();
  @override
  Future<Map<String, dynamic>> invoke({
    required String operation,
    required int sessionId,
    Map<String, Object?> request = const {},
    int afterSequence = 0,
  }) async {
    final encoded = await native.invokeGoDebug(
      operation: operation,
      sessionId: sessionId,
      requestJson: jsonEncode(request),
      afterSequence: afterSequence,
    );
    final decoded = jsonDecode(encoded);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Go 调试器响应不是对象');
    }
    return decoded;
  }
}

int _nextDebugSessionId = DateTime.now().microsecondsSinceEpoch;

class GoDebugger {
  GoDebugger({GoDebugBackend? backend})
    : backend = backend ?? const NativeGoDebugBackend();
  final GoDebugBackend backend;

  Future<GoDebugSession> start({
    required String projectPath,
    required String entryFile,
    Map<String, List<int>> breakpoints = const {},
  }) async {
    final id = ++_nextDebugSessionId;
    try {
      final response = await backend.invoke(
        operation: 'start',
        sessionId: id,
        request: {
          'projectPath': projectPath,
          'entryFile': entryFile,
          'breakpoints': breakpoints,
        },
      );
      final snapshot = GoDebugSnapshot.fromJson(response, expectedId: id);
      return GoDebugSession._(id, backend, snapshot);
    } catch (error) {
      // Release a session even if its response was malformed after registration.
      try {
        await backend.invoke(operation: 'close', sessionId: id);
      } catch (_) {
        /* The original load/start error is authoritative. */
      }
      if (error is GoDebugException) rethrow;
      throw GoDebugException('无法启动 Go 调试器：$error');
    }
  }
}

class GoDebugSession extends ChangeNotifier {
  GoDebugSession._(this.id, this._backend, this._snapshot);
  final int id;
  final GoDebugBackend _backend;
  GoDebugSnapshot _snapshot;
  Future<void> _pending = Future<void>.value();
  Future<void>? _closing;
  bool _closed = false;
  bool _disposed = false;
  GoDebugSnapshot get snapshot => _snapshot;
  bool get closed => _closed;

  Future<T> _serialize<T>(Future<T> Function() action) {
    final result = _pending.then((_) => action());
    _pending = result.then<void>((_) {}, onError: (Object _, StackTrace _) {});
    return result;
  }

  Future<GoDebugSnapshot> poll() => _serialize(() async {
    if (_closed) return _snapshot;
    final response = await _backend.invoke(
      operation: 'poll',
      sessionId: id,
      afterSequence: _snapshot.sequence,
    );
    return _accept(response);
  });

  Future<GoDebugSnapshot> command(GoDebugCommand command, {int? goroutineId}) =>
      _serialize(() async {
        if (_closed || _closing != null) {
          throw const GoDebugException('调试会话正在关闭或已关闭');
        }
        final response = await _backend.invoke(
          operation: 'command',
          sessionId: id,
          request: {'command': command.wireName, 'goroutineId': ?goroutineId},
        );
        return _accept(response);
      });

  GoDebugSnapshot _accept(Map<String, dynamic> response) {
    final incoming = GoDebugSnapshot.fromJson(response, expectedId: id);
    if (incoming.sequence < _snapshot.sequence) return _snapshot;
    final history = {
      for (final event in _snapshot.events) event.sequence: event,
      for (final event in incoming.events) event.sequence: event,
    }.values.toList()..sort((a, b) => a.sequence.compareTo(b.sequence));
    _snapshot = incoming.withEvents(
      history.skip(history.length > 128 ? history.length - 128 : 0).toList(),
    );
    if (!_disposed) notifyListeners();
    return _snapshot;
  }

  Future<void> close() {
    if (_closing != null) return _closing!;
    return _closing = _serialize(() async {
      var stopDispatched = _snapshot.terminal;
      while (!_snapshot.terminal) {
        try {
          if (!stopDispatched) {
            _accept(
              await _backend.invoke(
                operation: 'command',
                sessionId: id,
                request: const {'command': 'stop'},
              ),
            );
            stopDispatched = true;
          }
          if (!_snapshot.terminal) {
            _accept(
              await _backend.invoke(
                operation: 'poll',
                sessionId: id,
                afterSequence: _snapshot.sequence,
              ),
            );
          }
        } catch (_) {
          // Observation/transport failure is not evidence of worker exit.
          // Keep ownership and retry the same session until exit is observed.
        }
        if (!_snapshot.terminal) {
          await Future<void>.delayed(const Duration(milliseconds: 25));
        }
      }
      while (true) {
        try {
          final response = await _backend.invoke(
            operation: 'close',
            sessionId: id,
          );
          _accept(response);
          break;
        } catch (_) {
          await Future<void>.delayed(const Duration(milliseconds: 25));
        }
      }
      _closed = true;
    });
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}

class GoDebugSnapshot {
  const GoDebugSnapshot({
    required this.sessionId,
    required this.state,
    required this.sequence,
    this.droppedThrough = 0,
    this.events = const [],
    this.breakpoints = const [],
    this.stdout = '',
    this.stderr = '',
    this.outputTruncated = false,
    this.stdoutTruncated = false,
    this.stderrTruncated = false,
    this.threads = const [],
    this.threadsTruncated = false,
  });
  final int sessionId;
  final String state;
  final int sequence;
  final int droppedThrough;
  final List<GoDebugEvent> events;
  final List<GoDebugBreakpoint> breakpoints;
  final String stdout;
  final String stderr;
  final bool outputTruncated;
  final bool stdoutTruncated;
  final bool stderrTruncated;
  final List<GoDebugThread> threads;
  final bool threadsTruncated;
  bool get terminal => {'terminated', 'failed', 'closed'}.contains(state);
  GoDebugEvent? get stoppedEvent =>
      events.where((event) => event.frames.isNotEmpty).lastOrNull;

  factory GoDebugSnapshot.fromJson(
    Map<String, dynamic> json, {
    required int expectedId,
  }) {
    if (json['ok'] != true) {
      throw GoDebugException(
        json['error'] is String ? json['error'] as String : 'Go 调试操作失败',
      );
    }
    if (json['sessionId'] != expectedId) {
      throw const GoDebugException('Go 调试结果的会话身份不匹配');
    }
    final state = json['state'];
    if (state is! String ||
        !{
          'starting',
          'paused',
          'running',
          'stopping',
          'terminated',
          'failed',
          'closed',
        }.contains(state)) {
      throw const FormatException('Go 调试状态无效');
    }
    return GoDebugSnapshot(
      sessionId: expectedId,
      state: state,
      sequence: _integer(json, 'sequence'),
      droppedThrough: _integer(json, 'droppedThrough'),
      events: List.unmodifiable(
        _objects(json['events']).map(GoDebugEvent.fromJson),
      ),
      breakpoints: List.unmodifiable(
        _objects(json['breakpoints']).map(GoDebugBreakpoint.fromJson),
      ),
      stdout: _string(json, 'stdout'),
      stderr: _string(json, 'stderr'),
      outputTruncated: json['outputTruncated'] == true,
      stdoutTruncated:
          (json['stdoutTruncated'] ?? json['outputTruncated']) == true,
      stderrTruncated:
          (json['stderrTruncated'] ?? json['outputTruncated']) == true,
      threads: List.unmodifiable(
        _objects(json['threads']).map(GoDebugThread.fromJson),
      ),
      threadsTruncated: json['threadsTruncated'] == true,
    );
  }
  GoDebugSnapshot withEvents(List<GoDebugEvent> history) => GoDebugSnapshot(
    sessionId: sessionId,
    state: state,
    sequence: sequence,
    droppedThrough: droppedThrough,
    events: List.unmodifiable(history),
    breakpoints: breakpoints,
    stdout: stdout,
    stderr: stderr,
    outputTruncated: outputTruncated,
    stdoutTruncated: stdoutTruncated,
    stderrTruncated: stderrTruncated,
    threads: threads,
    threadsTruncated: threadsTruncated,
  );
}

class GoDebugEvent {
  const GoDebugEvent({
    required this.sequence,
    required this.reason,
    this.goroutineId = 0,
    this.kind = GoDebugExecutionKind.goroutine,
    this.opaqueNativeBoundary = false,
    this.frames = const [],
    this.message = '',
    this.framesTruncated = false,
  });
  final int sequence;
  final String reason;
  final int goroutineId;
  final GoDebugExecutionKind kind;
  final bool opaqueNativeBoundary;
  final List<GoDebugFrame> frames;
  final String message;
  final bool framesTruncated;
  factory GoDebugEvent.fromJson(Map<String, dynamic> json) => GoDebugEvent(
    sequence: _integer(json, 'sequence'),
    reason: _string(json, 'reason'),
    goroutineId: _integer(json, 'goroutineId'),
    kind: _executionKind(json),
    opaqueNativeBoundary: _optionalBoolean(json, 'opaqueNativeBoundary'),
    frames: List.unmodifiable(
      _objects(json['frames']).map(GoDebugFrame.fromJson),
    ),
    message: _string(json, 'message'),
    framesTruncated: json['framesTruncated'] == true,
  );
}

class GoDebugFrame {
  const GoDebugFrame({
    required this.name,
    required this.file,
    required this.line,
    required this.column,
    this.variables = const [],
    this.localsUnavailableReason = '',
    this.localsTruncated = false,
    this.opaqueNativeBoundary = false,
  });
  final String name;
  final String file;
  final int line;
  final int column;
  final List<GoDebugVariable> variables;
  final String localsUnavailableReason;
  final bool localsTruncated;
  final bool opaqueNativeBoundary;
  factory GoDebugFrame.fromJson(Map<String, dynamic> json) => GoDebugFrame(
    name: _string(json, 'name'),
    file: _string(json, 'file'),
    line: _integer(json, 'line'),
    column: _integer(json, 'column'),
    variables: List.unmodifiable(
      _objects(json['variables']).map(GoDebugVariable.fromJson),
    ),
    localsUnavailableReason: _string(json, 'localsUnavailableReason'),
    localsTruncated: json['localsTruncated'] == true,
    opaqueNativeBoundary: _optionalBoolean(json, 'opaqueNativeBoundary'),
  );
}

class GoDebugThread {
  const GoDebugThread({
    required this.id,
    required this.paused,
    this.kind = GoDebugExecutionKind.goroutine,
  });
  final int id;
  final bool paused;
  final GoDebugExecutionKind kind;
  factory GoDebugThread.fromJson(Map<String, dynamic> json) =>
      GoDebugThread(
        id: _integer(json, 'id'),
        paused: json['paused'] == true,
        kind: _executionKind(json),
      );
}

class GoDebugVariable {
  const GoDebugVariable({
    required this.name,
    required this.type,
    required this.value,
  });
  final String name;
  final String type;
  final String value;
  factory GoDebugVariable.fromJson(Map<String, dynamic> json) =>
      GoDebugVariable(
        name: _string(json, 'name'),
        type: _string(json, 'type'),
        value: _string(json, 'value'),
      );
}

class GoDebugBreakpoint {
  const GoDebugBreakpoint({
    required this.file,
    required this.line,
    required this.actualLine,
    required this.valid,
  });
  final String file;
  final int line;
  final int actualLine;
  final bool valid;
  factory GoDebugBreakpoint.fromJson(Map<String, dynamic> json) =>
      GoDebugBreakpoint(
        file: _string(json, 'file'),
        line: _integer(json, 'line'),
        actualLine: _integer(json, 'actualLine'),
        valid: json['valid'] == true,
      );
}

GoDebugExecutionKind _executionKind(Map<String, dynamic> json) {
  if (!json.containsKey('kind')) return GoDebugExecutionKind.goroutine;
  return switch (json['kind']) {
    'goroutine' => GoDebugExecutionKind.goroutine,
    'nativeCallback' => GoDebugExecutionKind.nativeCallback,
    _ => throw const FormatException('Go 调试执行类型无效'),
  };
}

bool _optionalBoolean(Map<String, dynamic> json, String key) {
  if (!json.containsKey(key)) return false;
  final value = json[key];
  if (value is! bool) throw FormatException('Go 调试布尔值无效：$key');
  return value;
}

Iterable<Map<String, dynamic>> _objects(Object? value) {
  if (value == null) return const [];
  if (value is! List) throw const FormatException('Go 调试列表格式无效');
  return value.map((item) {
    if (item is! Map<String, dynamic>) {
      throw const FormatException('Go 调试记录格式无效');
    }
    return item;
  });
}

int _integer(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null) return 0;
  if (value is! int || value < 0) throw FormatException('Go 调试数值无效：$key');
  return value;
}

String _string(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null) return '';
  if (value is! String) throw FormatException('Go 调试文本无效：$key');
  return value;
}

class GoDebugBreakpoints {
  static Map<String, List<int>> parse(
    String input, {
    required String entryFile,
  }) {
    final result = <String, List<int>>{};
    for (final token in input.split(RegExp(r'[,;\n]'))) {
      final value = token.trim();
      if (value.isEmpty) continue;
      final colon = value.lastIndexOf(':');
      final file = colon < 0 ? entryFile : value.substring(0, colon).trim();
      final line = int.tryParse(
        colon < 0 ? value : value.substring(colon + 1).trim(),
      );
      if (file.isEmpty || line == null || line < 1 || line > 1000000) {
        throw GoDebugException('断点格式无效：$value');
      }
      final lines = result.putIfAbsent(file, () => []);
      if (!lines.contains(line)) lines.add(line);
      if (result.values.fold<int>(0, (sum, lines) => sum + lines.length) >
          256) {
        throw const GoDebugException('最多设置 256 个断点');
      }
    }
    for (final lines in result.values) {
      lines.sort();
    }
    return result;
  }
}
