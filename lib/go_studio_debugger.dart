import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/debug_session.dart';

import 'go_debugger.dart';

/// Offline interpreted Go debugging. Imports retain Yaegi's initialization
/// semantics; the entry package pauses before its own initializers execute.
class GoStudioDebugger implements StudioDebugger {
  GoStudioDebugger({
    GoDebugger? debugger,
    this.pollInterval = const Duration(milliseconds: 40),
  }) : _debugger = debugger ?? GoDebugger();

  final GoDebugger _debugger;
  final Duration pollInterval;

  @override
  String get displayName => 'Go';

  @override
  DebugCapabilities get capabilities => const DebugCapabilities(
    breakpointUpdate: DebugBreakpointUpdate.launchOnly,
    outputDelivery: DebugOutputDelivery.live,
    supportsPause: true,
    supportsStepInto: true,
    supportsStepOver: true,
    supportsStepOut: true,
    supportsStopOnEntry: true,
    supportsStackFrames: true,
    supportsVariables: true,
  );

  @override
  bool supportsLanguage(String language) => language.toLowerCase() == 'go';

  @override
  Future<DebugSession> launch(DebugLaunchRequest request) async {
    if (!supportsLanguage(request.language)) {
      throw const GoDebugException('Go 调试器仅支持 Go 源代码');
    }
    if (request.documents.isNotEmpty) {
      throw const GoDebugException('Go 调试需要先保存全部文件；不支持未保存的文档快照');
    }
    if (!p.isAbsolute(request.projectPath)) {
      throw const GoDebugException('调试项目必须使用绝对路径');
    }
    final root = p.normalize(
      await Directory(request.projectPath).resolveSymbolicLinks(),
    );
    if (root.runes.length > 4096) throw const GoDebugException('项目路径过长');
    final entry = await _validateSource(root, request.entryFilePath);
    if (request.breakpoints.length > 256) {
      throw const GoDebugException('最多设置 256 个断点');
    }
    final breakpoints = <DebugBreakpoint>[];
    final nativeBreakpoints = <String, List<int>>{};
    final seen = <String>{};
    for (final breakpoint in request.breakpoints) {
      final file = await _validateSource(root, breakpoint.filePath);
      final lines = await File(file).readAsLines();
      if (breakpoint.line < 1 ||
          breakpoint.line > lines.length ||
          breakpoint.line > 1000000) {
        throw GoDebugException('断点行号超出源文件范围：${breakpoint.line}');
      }
      final key = '${p.canonicalize(file)}:${breakpoint.line}';
      if (!seen.add(key)) throw const GoDebugException('存在重复断点');
      breakpoints.add(DebugBreakpoint(filePath: file, line: breakpoint.line));
      nativeBreakpoints
          .putIfAbsent(
            p.relative(file, from: root).replaceAll('\\', '/'),
            () => [],
          )
          .add(breakpoint.line);
    }
    final native = await _debugger.start(
      projectPath: root,
      entryFile: entry,
      breakpoints: nativeBreakpoints,
    );
    final session = _GoStudioDebugSession(
      native,
      root,
      breakpoints,
      request.stopOnEntry,
      pollInterval,
    );
    session.start();
    return session;
  }

  static Future<String> _validateSource(String root, String path) async {
    if (!p.isAbsolute(path) || path.runes.length > 4096) {
      throw const GoDebugException('调试源文件必须使用有效的绝对路径');
    }
    final file = p.normalize(await File(path).resolveSymbolicLinks());
    if (!p.isWithin(root, file) ||
        p.extension(file) != '.go' ||
        !await File(file).exists()) {
      throw const GoDebugException('调试文件必须是项目内的 Go 源文件');
    }
    return file;
  }
}

/// Bounds: 128 threads, 32 frames, 100 scalar locals/frame; no child handles.
/// Text limits are Unicode code points: output 65536, console 8192, messages
/// 2048, source paths 4096, names/types/values 512. Native byte bounds apply too.
final class _GoStudioDebugSession implements DebugSession {
  _GoStudioDebugSession(
    this._native,
    this._root,
    this._requested,
    this._stopOnEntry,
    this._interval,
  ) : _snapshot = DebugSnapshot(
        sessionId: 'go:${_native.id}',
        revision: 0,
        phase: DebugPhase.starting,
      );

  final GoDebugSession _native;
  final String _root;
  final List<DebugBreakpoint> _requested;
  final bool _stopOnEntry;
  final Duration _interval;
  final _updates = StreamController<DebugSnapshot>.broadcast();
  final _done = Completer<void>();
  Future<void> _pending = Future<void>.value();
  Future<void>? _stopping;
  Future<void>? _disposing;
  Future<void>? _cleanup;
  DebugSnapshot _snapshot;
  String? _fingerprint;
  String? _pauseKey;
  int _generation = 0;
  bool _entryHandled = false;
  bool _stopRequested = false;

  @override
  String get id => 'go:${_native.id}';
  @override
  DebugSnapshot get snapshot => _snapshot;
  @override
  Stream<DebugSnapshot> get updates => _updates.stream;
  @override
  Future<void> get done => _done.future;

  Future<T> _serialize<T>(Future<T> Function() action) {
    final result = _pending.then((_) => action());
    _pending = result.then<void>((_) {}, onError: (Object _, StackTrace _) {});
    return result;
  }

  void start() {
    _publish();
    unawaited(_poll());
  }

  Future<void> _poll() async {
    while (!_done.isCompleted) {
      try {
        await _serialize(() async {
          if (_cleanup != null) return;
          await _native.poll();
          _publish();
          if (!_entryHandled && _native.snapshot.state == 'paused') {
            _entryHandled = true;
            if (!_stopOnEntry &&
                !_stopRequested &&
                _native.snapshot.stoppedEvent?.reason == 'entry') {
              final thread = _snapshot.threads
                  .where((thread) => thread.isPaused)
                  .firstOrNull;
              if (thread != null) {
                await _native.command(
                  GoDebugCommand.continueExecution,
                  goroutineId: _nativeThread(thread.id),
                );
                _pauseKey = null;
                _publish();
              }
            }
          }
        });
      } catch (_) {
        // Keep observing the same worker. A transient failed observation cannot
        // establish termination or release the runtime's native registration.
      }
      if (!_done.isCompleted) await Future<void>.delayed(_interval);
    }
  }

  @override
  Future<List<DebugBreakpointResult>> setBreakpoints(
    List<DebugBreakpoint> breakpoints,
  ) async {
    throw const GoDebugException('Go 断点只能在启动调试时设置；请停止后重新启动');
  }

  @override
  Future<void> command(
    DebugCommand command, {
    DebugPauseToken? pauseToken,
    String? threadId,
  }) => _serialize(() async {
    if (_stopRequested || _snapshot.isTerminal || _cleanup != null) {
      throw const GoDebugException('调试会话已结束或正在停止');
    }
    DebugThread? thread;
    if (threadId != null) {
      thread = _snapshot.threads
          .where((value) => value.id == threadId)
          .firstOrNull;
      if (thread == null) throw const GoDebugException('未知调试线程');
    }
    if (command == DebugCommand.pause) {
      if (_snapshot.phase != DebugPhase.running || pauseToken != null) {
        throw const GoDebugException('仅运行中的会话可以暂停');
      }
    } else {
      if (_snapshot.phase != DebugPhase.paused ||
          pauseToken == null ||
          pauseToken != _snapshot.pauseToken) {
        throw const GoDebugException('暂停令牌已失效或不属于此会话');
      }
      thread ??= _snapshot.threads.where((value) => value.isPaused).firstOrNull;
      if (thread == null || !thread.isPaused) {
        throw const GoDebugException('线程未暂停');
      }
    }
    await _native.command(switch (command) {
      DebugCommand.resume => GoDebugCommand.continueExecution,
      DebugCommand.pause => GoDebugCommand.pause,
      DebugCommand.stepInto => GoDebugCommand.stepInto,
      DebugCommand.stepOver => GoDebugCommand.stepOver,
      DebugCommand.stepOut => GoDebugCommand.stepOut,
    }, goroutineId: thread == null ? null : _nativeThread(thread.id));
    if (command != DebugCommand.pause) _pauseKey = null;
    _publish();
  });

  int _nativeThread(String threadId) => int.parse(threadId.split(':').last);

  @override
  Future<void> stop() => _stopping ??= () async {
    _stopRequested = true;
    if (!_snapshot.isTerminal) _publish();
    await _serialize(() async {
      if (_cleanup != null) return;
      try {
        await _native.command(GoDebugCommand.stop);
        _publish();
      } catch (_) {
        // close retries stop and observes actual terminal state before release.
      }
      _finish();
    });
    await done;
  }();

  @override
  Future<void> dispose() => _disposing ??= () async {
    await stop();
    await _updates.close();
  }();

  void _finish() {
    _cleanup ??= () async {
      await _native.close();
      _publish();
      _native.dispose();
      if (!_done.isCompleted) _done.complete();
    }();
  }

  void _publish() {
    final source = _native.snapshot;
    final phase = switch (source.state) {
      'closed' when _snapshot.phase == DebugPhase.failed => DebugPhase.failed,
      'terminated' || 'closed' => DebugPhase.terminated,
      'failed' => DebugPhase.failed,
      _ when _stopRequested => DebugPhase.stopping,
      'paused' => DebugPhase.paused,
      'running' => DebugPhase.running,
      'stopping' => DebugPhase.stopping,
      _ => DebugPhase.starting,
    };
    final nativeThreads = source.threads
        .where((thread) => thread.id > 0)
        .take(128)
        .toList();
    // Older native payloads carry the paused goroutine on the real stop event.
    final stoppedEvent = source.stoppedEvent;
    if (phase == DebugPhase.paused &&
        nativeThreads.isEmpty &&
        stoppedEvent != null) {
      if (stoppedEvent.goroutineId > 0) {
        nativeThreads.add(
          GoDebugThread(
            id: stoppedEvent.goroutineId,
            paused: true,
            kind: stoppedEvent.kind,
          ),
        );
      }
    }
    final pausedEvents = <GoDebugEvent>[];
    for (final thread in nativeThreads.where((thread) => thread.paused)) {
      final event = source.events
          .where(
            (event) =>
                event.goroutineId == thread.id && event.frames.isNotEmpty,
          )
          .lastOrNull;
      if (event != null) pausedEvents.add(event);
    }
    final key = phase == DebugPhase.paused
        ? pausedEvents
              .map((event) => '${event.goroutineId}:${event.sequence}')
              .join(',')
        : null;
    if (phase == DebugPhase.paused && (_pauseKey != key || _pauseKey == null)) {
      _generation++;
    }
    _pauseKey = key;
    final token = phase == DebugPhase.paused
        ? DebugPauseToken(sessionId: id, generation: _generation)
        : null;
    final threads = [
      for (final thread in nativeThreads)
        DebugThread(
          id: '$id:${token?.generation ?? 0}:${thread.id}',
          name: thread.kind.nameFor(thread.id),
          isPaused: phase == DebugPhase.paused && thread.paused,
        ),
    ];
    final frames = <DebugFrame>[];
    if (token != null) {
      for (final event in pausedEvents) {
        for (final (index, frame) in event.frames.indexed) {
          if (frames.length == 32) break;
          frames.add(
            DebugFrame(
              id: '$id:${token.generation}:${event.goroutineId}:$index',
              threadId: '$id:${token.generation}:${event.goroutineId}',
              name: _text(frame.name, 512),
              location: _location(frame.file, frame.line, frame.column),
              locals: frame.variables
                  .take(100)
                  .map(
                    (variable) => DebugVariable(
                      name: _text(variable.name, 512),
                      type: _text(variable.type, 512),
                      value: _text(variable.value, 512),
                      unavailableReason: variable.value.startsWith('<存在其他')
                          ? 'Other Go routines may modify shared values'
                          : variable.value.startsWith('<') &&
                                variable.value.endsWith('>')
                          ? 'Only scalar Go values are inspected'
                          : null,
                      truncated:
                          variable.name.runes.length > 512 ||
                          variable.type.runes.length > 512 ||
                          variable.value.runes.length > 512 ||
                          variable.value.endsWith('…'),
                    ),
                  )
                  .toList(),
              localsUnavailableReason: frame.localsUnavailableReason.isNotEmpty
                  ? _text(frame.localsUnavailableReason, 2048)
                  : frame.opaqueNativeBoundary || event.opaqueNativeBoundary
                  ? 'Locals are unavailable at an opaque native callback boundary'
                  : null,
              localsTruncated:
                  frame.localsTruncated || frame.variables.length > 100,
            ),
          );
        }
      }
    }
    final results = [
      for (final breakpoint in _requested)
        _breakpointResult(breakpoint, source),
    ];
    final consoleRaw = source.events
        .expand(
          (event) => [
            if (event.message.isNotEmpty) event.message,
            if (event.opaqueNativeBoundary ||
                event.frames.any((frame) => frame.opaqueNativeBoundary))
              '${event.kind.nameFor(event.goroutineId)}: Call stack ends at an '
                  'opaque native callback boundary; external caller unavailable.',
          ],
        )
        .join('\n');
    final message = phase == DebugPhase.failed
        ? _text(
            source.events
                    .where((event) => event.message.isNotEmpty)
                    .lastOrNull
                    ?.message ??
                'Go debugger failed',
            2048,
          )
        : null;
    final fingerprint = jsonEncode([
      phase.name,
      token?.generation,
      threads.map((thread) => [thread.id, thread.name, thread.isPaused]).toList(),
      frames
          .map(
            (frame) => [
              frame.id,
              frame.name,
              frame.location?.filePath,
              frame.location?.line,
              frame.location?.column,
              frame.locals
                  .map(
                    (variable) => [
                      variable.name,
                      variable.type,
                      variable.value,
                      variable.unavailableReason,
                      variable.truncated,
                    ],
                  )
                  .toList(),
              frame.localsUnavailableReason,
              frame.localsTruncated,
            ],
          )
          .toList(),
      results
          .map((result) => [result.status.name, result.actualLocation?.line])
          .toList(),
      source.stdout,
      source.stderr,
      consoleRaw,
      source.outputTruncated,
      source.stdoutTruncated,
      source.stderrTruncated,
      source.droppedThrough,
      source.threadsTruncated,
      pausedEvents.any((event) => event.framesTruncated),
      message,
    ]);
    if (_fingerprint == fingerprint) return;
    _fingerprint = fingerprint;
    _snapshot = DebugSnapshot(
      sessionId: id,
      revision: _snapshot.revision + 1,
      phase: phase,
      pauseToken: token,
      threads: threads,
      frames: frames,
      breakpoints: results,
      threadsTruncated: source.threadsTruncated || source.threads.length > 128,
      framesTruncated:
          pausedEvents.any((event) => event.framesTruncated) ||
          pausedEvents.fold<int>(0, (sum, event) => sum + event.frames.length) >
              32,
      stdout: _text(source.stdout, 65536, tail: true),
      stderr: _text(source.stderr, 65536, tail: true),
      console: _text(consoleRaw, 8192, tail: true),
      stdoutTruncated:
          source.stdoutTruncated || source.stdout.runes.length > 65536,
      stderrTruncated:
          source.stderrTruncated || source.stderr.runes.length > 65536,
      consoleTruncated:
          source.droppedThrough > 0 || consoleRaw.runes.length > 8192,
      message: message,
    );
    _updates.add(_snapshot);
    if (_snapshot.isTerminal) _finish();
  }

  DebugBreakpointResult _breakpointResult(
    DebugBreakpoint requested,
    GoDebugSnapshot source,
  ) {
    final result = source.breakpoints
        .where(
          (value) =>
              value.line == requested.line &&
              _location(
                    value.file,
                    value.actualLine > 0 ? value.actualLine : value.line,
                    0,
                  )?.filePath ==
                  requested.filePath,
        )
        .firstOrNull;
    if (result == null) {
      return DebugBreakpointResult(
        requested: requested,
        status: DebugBreakpointStatus.pending,
      );
    }
    final location = _location(result.file, result.actualLine, 0);
    return DebugBreakpointResult(
      requested: requested,
      status: result.valid && location != null
          ? DebugBreakpointStatus.verified
          : DebugBreakpointStatus.rejected,
      actualLocation: result.valid ? location : null,
      reason: result.valid && location != null
          ? null
          : 'No executable statement at the requested line',
    );
  }

  DebugSourceLocation? _location(String file, int line, int column) {
    if (file.isEmpty || file.runes.length > 4096 || line < 1) return null;
    if (file.startsWith('qfli-project/')) {
      file = file.substring('qfli-project/'.length);
    }
    try {
      final path = p.normalize(
        File(
          p.isAbsolute(file) ? file : p.join(_root, file),
        ).resolveSymbolicLinksSync(),
      );
      if (!p.isWithin(_root, path) ||
          p.extension(path) != '.go' ||
          !File(path).existsSync()) {
        return null;
      }
      return DebugSourceLocation(
        filePath: path,
        line: line,
        column: column > 0 ? column : null,
      );
    } on FileSystemException {
      return null;
    }
  }
}

String _text(String value, int limit, {bool tail = false}) {
  final runes = value.runes.toList();
  if (runes.length <= limit) return value;
  return String.fromCharCodes(
    tail ? runes.skip(runes.length - limit) : runes.take(limit),
  );
}
