import 'dart:async';

import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/widgets/tool_widgets.dart';

import 'go_debugger.dart';
import 'go_tools.dart';

class GoDebuggerPage extends StatefulWidget {
  const GoDebuggerPage({
    super.key,
    required this.store,
    this.debugger,
    this.tools,
  });
  final ProjectStore store;
  final GoDebugger? debugger;
  final GoTools? tools;

  @override
  State<GoDebuggerPage> createState() => _GoDebuggerPageState();
}

class _GoDebuggerPageState extends State<GoDebuggerPage> {
  late final GoDebugger _debugger = widget.debugger ?? GoDebugger();
  late final GoTools _tools = widget.tools ?? GoTools();
  final _breakpoints = TextEditingController();
  Project? _project;
  List<String> _files = const [];
  String? _entry;
  GoDebugSession? _session;
  Timer? _timer;
  String? _error;
  bool _loadingFiles = false;
  bool _busy = false;
  bool _polling = false;
  bool _pollFailed = false;
  int _projectRevision = 0;

  @override
  void initState() {
    super.initState();
    _project = GoTools.currentProject(widget.store);
    unawaited(_loadFiles());
  }

  @override
  void dispose() {
    _timer?.cancel();
    final session = _session;
    if (session != null) {
      session.removeListener(_updated);
      unawaited(_release(session));
    }
    _breakpoints.dispose();
    super.dispose();
  }

  Future<void> _release(GoDebugSession session) async {
    try {
      await session.close();
    } catch (error) {
      debugPrint('Go 调试会话清理失败：$error');
    } finally {
      session.dispose();
    }
  }

  Future<void> _loadFiles() async {
    final project = _project;
    if (project == null) return;
    final revision = ++_projectRevision;
    setState(() {
      _loadingFiles = true;
      _files = const [];
      _entry = null;
      _error = null;
    });
    try {
      final files = await _tools.sourceFiles(project);
      if (!mounted || revision != _projectRevision) return;
      setState(() {
        _files = files;
        _entry =
            files.where((file) => p.basename(file) == 'main.go').firstOrNull ??
            files.firstOrNull;
        if (files.isEmpty) _error = '所选项目没有 Go 源文件';
      });
    } catch (error) {
      if (mounted && revision == _projectRevision) {
        setState(() => _error = '$error');
      }
    } finally {
      if (mounted && revision == _projectRevision) {
        setState(() => _loadingFiles = false);
      }
    }
  }

  void _updated() {
    if (mounted) {
      if (_session?.snapshot.terminal ?? false) _timer?.cancel();
      setState(() {});
    }
  }

  Future<void> _poll() async {
    final session = _session;
    if (session == null || _polling || session.closed) return;
    _polling = true;
    try {
      await session.poll();
      if (mounted && _pollFailed && identical(session, _session)) {
        setState(() {
          _pollFailed = false;
          _error = null;
        });
      }
    } catch (error) {
      if (mounted && identical(session, _session)) {
        setState(() {
          _pollFailed = true;
          _error = '$error';
        });
      }
    } finally {
      _polling = false;
    }
  }

  Future<void> _start() async {
    final project = _project;
    final entry = _entry;
    if (project == null || entry == null || _busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final breakpoints = GoDebugBreakpoints.parse(
        _breakpoints.text,
        entryFile: entry,
      );
      final previous = _session;
      if (previous != null) {
        _timer?.cancel();
        previous.removeListener(_updated);
        await previous.close();
        previous.dispose();
        _session = null;
      }
      final session = await _debugger.start(
        projectPath: project.path,
        entryFile: p.join(project.path, entry),
        breakpoints: breakpoints,
      );
      if (!mounted) {
        await _release(session);
        return;
      }
      _session = session;
      session.addListener(_updated);
      _timer = Timer.periodic(
        const Duration(milliseconds: 150),
        (_) => unawaited(_poll()),
      );
      await _poll();
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _command(GoDebugCommand command) async {
    final session = _session;
    if (session == null || _busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await session.command(command);
      await _poll();
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = _session;
    final snapshot = session?.snapshot;
    final active = snapshot != null && !snapshot.terminal;
    final paused = snapshot?.state == 'paused';
    final stopped = snapshot?.stoppedEvent;
    return ToolScaffold(
      title: 'Go 调试',
      description:
          '在本地运行已保存的 Go 项目，支持断点、单步、调用栈与局部变量。入口包的初始化也受调试控制；源码依赖的初始化在准备阶段完成。',
      children: [
        ListenableBuilder(
          listenable: widget.store,
          builder: (context, _) {
            final projects = GoTools.localProjects(widget.store);
            if (projects.isEmpty) return const Text('请先创建或导入一个本地 Go 项目。');
            return DropdownButtonFormField<String>(
              key: ValueKey('go-debug-project-${_project?.id}'),
              initialValue: projects.any((item) => item.id == _project?.id)
                  ? _project?.id
                  : null,
              isExpanded: true,
              decoration: const InputDecoration(labelText: '本地 Go 项目'),
              items: [
                for (final project in projects)
                  DropdownMenuItem(
                    value: project.id,
                    child: Text(
                      project.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
              onChanged: active || _busy
                  ? null
                  : (id) {
                      _project = projects.firstWhere((item) => item.id == id);
                      widget.store.setBrowsedProject(_project!);
                      unawaited(_loadFiles());
                    },
            );
          },
        ),
        const SizedBox(height: 12),
        if (_loadingFiles) const LinearProgressIndicator(),
        if (_files.isNotEmpty)
          DropdownButtonFormField<String>(
            key: ValueKey('go-debug-entry-${_project?.id}-${_files.join('|')}'),
            initialValue: _entry,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Go 入口文件'),
            items: [
              for (final file in _files)
                DropdownMenuItem(
                  value: file,
                  child: Text(
                    file,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
            onChanged: active || _busy
                ? null
                : (value) => setState(() => _entry = value),
          ),
        ToolField(
          controller: _breakpoints,
          label: '断点',
          hint: '行号或 相对路径:行号，每行一个',
          maxLines: 3,
        ),
        const Text('断点在启动时设置。运行中的源码修改需保存后重新启动调试。'),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            FilledButton.icon(
              onPressed: _busy || active || _loadingFiles || _entry == null
                  ? null
                  : _start,
              icon: const Icon(Icons.bug_report_outlined),
              label: Text(_busy && session == null ? '准备中…' : '启动调试'),
            ),
            OutlinedButton.icon(
              onPressed: _busy || !paused
                  ? null
                  : () => _command(GoDebugCommand.continueExecution),
              icon: const Icon(Icons.play_arrow),
              label: const Text('继续'),
            ),
            OutlinedButton.icon(
              onPressed: _busy || snapshot?.state != 'running'
                  ? null
                  : () => _command(GoDebugCommand.pause),
              icon: const Icon(Icons.pause),
              label: const Text('暂停'),
            ),
            OutlinedButton(
              onPressed: _busy || !paused
                  ? null
                  : () => _command(GoDebugCommand.stepOver),
              child: const Text('单步跳过'),
            ),
            OutlinedButton(
              onPressed: _busy || !paused
                  ? null
                  : () => _command(GoDebugCommand.stepInto),
              child: const Text('单步进入'),
            ),
            OutlinedButton(
              onPressed: _busy || !paused
                  ? null
                  : () => _command(GoDebugCommand.stepOut),
              child: const Text('单步跳出'),
            ),
            OutlinedButton.icon(
              onPressed: _busy || !active
                  ? null
                  : () => _command(GoDebugCommand.stop),
              icon: const Icon(Icons.stop),
              label: const Text('停止'),
            ),
          ],
        ),
        ToolError(_error),
        if (snapshot != null) ...[
          const SizedBox(height: 16),
          Text(
            '状态：${_stateLabel(snapshot.state)}',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          for (final breakpoint in snapshot.breakpoints)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                '${breakpoint.valid ? '●' : '○'} ${breakpoint.file}:${breakpoint.line}  ${breakpoint.valid ? '已验证' : '该行没有可执行断点'}',
              ),
            ),
          if (paused && stopped != null) ...[
            const SizedBox(height: 16),
            Text(
              '${stopped.kind.nameFor(stopped.goroutineId)} · ${_reasonLabel(stopped.reason)}',
            ),
            if (stopped.opaqueNativeBoundary)
              const Padding(
                padding: EdgeInsets.only(top: 8),
                child: Text('调用栈在原生回调边界结束，外部调用者不可用。'),
              ),
            for (final frame in stopped.frames) ...[
              const SizedBox(height: 8),
              ToolResultCard(
                children: [
                  SelectableText(
                    '${frame.name} · ${frame.file}:${frame.line}:${frame.column}',
                  ),
                  if (frame.opaqueNativeBoundary &&
                      !stopped.opaqueNativeBoundary)
                    const Padding(
                      padding: EdgeInsets.only(top: 8),
                      child: Text('调用栈在原生回调边界结束，外部调用者不可用。'),
                    ),
                  if (frame.localsUnavailableReason.isNotEmpty ||
                      frame.variables.isEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(
                        frame.localsUnavailableReason.isNotEmpty
                            ? frame.localsUnavailableReason
                            : frame.opaqueNativeBoundary ||
                                  stopped.opaqueNativeBoundary
                            ? '原生回调边界的局部变量不可用。'
                            : '此栈帧没有可展示的局部变量',
                      ),
                    ),
                  for (final variable in frame.variables)
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: SelectableText(
                        '${variable.name} (${variable.type}) = ${variable.value}',
                        style: const TextStyle(fontFamily: 'monospace'),
                      ),
                    ),
                ],
              ),
            ],
          ],
          if (snapshot.stdout.isNotEmpty) ...[
            const SizedBox(height: 16),
            _DebugOutput(title: '标准输出', text: snapshot.stdout),
          ],
          if (snapshot.stderr.isNotEmpty) ...[
            const SizedBox(height: 16),
            _DebugOutput(title: '标准错误', text: snapshot.stderr),
          ],
          if (snapshot.outputTruncated)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text('输出过长，保留最近 64 KiB。'),
            ),
          if (snapshot.events.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text('调试事件', style: Theme.of(context).textTheme.titleSmall),
            if (snapshot.droppedThrough > 0) const Text('较早的调试事件已移出缓冲区。'),
            for (final event in snapshot.events.reversed.take(20))
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: SelectableText(
                  '${event.sequence} · ${_reasonLabel(event.reason)}'
                  '${event.goroutineId > 0 ? ' · ${event.kind.nameFor(event.goroutineId)}' : ''}'
                  '${event.frames.isEmpty ? '' : ' · ${event.frames.first.file}:${event.frames.first.line}'}'
                  '${event.opaqueNativeBoundary || event.frames.any((frame) => frame.opaqueNativeBoundary) ? '\n调用栈在原生回调边界结束，外部调用者不可用。' : ''}'
                  '${event.message.isEmpty ? '' : '\n${event.message}'}',
                ),
              ),
          ],
        ],
      ],
    );
  }
}

class _DebugOutput extends StatelessWidget {
  const _DebugOutput({required this.title, required this.text});
  final String title;
  final String text;
  @override
  Widget build(BuildContext context) => ToolResultCard(
    title: title,
    children: [
      SelectableText(
        text,
        style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
      ),
    ],
  );
}

String _stateLabel(String state) => switch (state) {
  'starting' => '准备中',
  'paused' => '已暂停',
  'running' => '运行中',
  'stopping' => '正在停止',
  'terminated' => '已结束',
  'failed' => '失败',
  'closed' => '已关闭',
  _ => state,
};
String _reasonLabel(String reason) => switch (reason) {
  'entry' => '入口暂停',
  'breakpoint' => '命中断点',
  'pause' => '暂停完成',
  'stepInto' => '单步进入',
  'stepOver' => '单步跳过',
  'stepOut' => '单步跳出',
  'failed' => '调试失败',
  'terminated' => '程序结束',
  _ => reason,
};
