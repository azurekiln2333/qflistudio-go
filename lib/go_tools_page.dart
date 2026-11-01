import 'package:flutter/material.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/pages/tools_grid.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/widgets/tool_widgets.dart';

import 'go_tools.dart';

/// Embeds directly in FunctionsTab. Each card opens its own working tool.
class GoToolsTab extends StatelessWidget {
  const GoToolsTab({
    super.key,
    required this.store,
    required this.onOpenTerminal,
    this.tools,
    this.extraTools = const [],
  });

  final ProjectStore store;
  final VoidCallback onOpenTerminal;
  final GoTools? tools;
  final List<ToolDefinition> extraTools;

  @override
  Widget build(BuildContext context) {
    final backend = tools ?? GoTools();
    return ToolsGrid(
      onOpenTerminal: onOpenTerminal,
      sections: [
        ToolSection(
          title: 'Go',
          icon: Icons.code,
          tools: [
            ToolDefinition(
              title: 'Go 格式化',
              description: '格式化粘贴的代码或项目源文件',
              icon: Icons.format_align_left,
              builder: (_) => GoSourceToolPage(store: store, tools: backend),
            ),
            ToolDefinition(
              title: '导入与符号',
              description: '查看包名、导入和源码声明位置',
              icon: Icons.account_tree_outlined,
              builder: (_) => GoSourceToolPage(
                store: store,
                tools: backend,
                inspectOnly: true,
              ),
            ),
            ToolDefinition(
              title: 'Go 模块检查',
              description: '检查当前项目依赖、vendor 与本地替换',
              icon: Icons.inventory_2_outlined,
              builder: (_) => GoModuleToolPage(store: store, tools: backend),
            ),
            ToolDefinition(
              title: 'JSON 转 Go 结构体',
              description: '推断嵌套类型、数组和 JSON 字段标签',
              icon: Icons.data_object,
              builder: (_) => const GoJsonStructToolPage(),
            ),
            ...extraTools,
          ],
        ),
      ],
    );
  }
}

class _ProjectPicker extends StatelessWidget {
  const _ProjectPicker({
    required this.store,
    required this.selectedId,
    required this.onChanged,
  });
  final ProjectStore store;
  final String? selectedId;
  final ValueChanged<Project> onChanged;

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: store,
    builder: (context, _) {
      final projects = GoTools.localProjects(store);
      if (projects.isEmpty) return const Text('暂无本地 Go 项目，可先粘贴代码使用源码工具。');
      final selected = projects
          .where((project) => project.id == selectedId)
          .firstOrNull;
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: DropdownButtonFormField<String>(
          key: ValueKey('go-project-${selected?.id}'),
          initialValue: selected?.id,
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
          onChanged: (id) {
            final project = projects.firstWhere((project) => project.id == id);
            store.setBrowsedProject(project);
            onChanged(project);
          },
        ),
      );
    },
  );
}

class GoSourceToolPage extends StatefulWidget {
  const GoSourceToolPage({
    super.key,
    required this.store,
    required this.tools,
    this.inspectOnly = false,
  });
  final ProjectStore store;
  final GoTools tools;
  final bool inspectOnly;

  @override
  State<GoSourceToolPage> createState() => _GoSourceToolPageState();
}

class _GoSourceToolPageState extends State<GoSourceToolPage> {
  final _source = TextEditingController();
  Project? _project;
  List<String> _files = const [];
  String? _file;
  String? _error;
  GoToolSourceResult? _result;
  bool _busy = false;
  int _revision = 0;

  @override
  void initState() {
    super.initState();
    _project = GoTools.currentProject(widget.store);
  }

  @override
  void dispose() {
    _source.dispose();
    super.dispose();
  }

  void _changed() {
    _revision++;
    setState(() {
      _result = null;
      _error = null;
    });
  }

  Future<void> _loadFiles() async {
    final project = _project;
    if (project == null) return;
    await _perform(() async {
      final files = await widget.tools.sourceFiles(project);
      if (!mounted || _project?.id != project.id) return;
      setState(() {
        _files = files;
        _file = null;
        if (files.isEmpty) _error = '项目没有可读取的 Go 源文件';
      });
    });
  }

  Future<void> _loadSource() async {
    final project = _project;
    final file = _file;
    if (project == null || file == null) return;
    final revision = _revision;
    await _perform(() async {
      final source = await widget.tools.readSource(project, file);
      if (!mounted || revision != _revision || _project?.id != project.id) {
        return;
      }
      _source.text = source;
      _changed();
    });
  }

  Future<void> _run() async {
    final source = _source.text;
    if (source.trim().isEmpty) {
      setState(() => _error = '请粘贴代码或读取项目源文件');
      return;
    }
    final revision = _revision;
    final filePath = _file ?? 'snippet.go';
    await _perform(() async {
      final result = widget.inspectOnly
          ? await widget.tools.inspect(source, filePath)
          : await widget.tools.format(source, filePath);
      if (!mounted || revision != _revision) return;
      setState(() {
        _result = result;
        _error =
            result.unavailableReason ??
            (result.errors.isEmpty ? null : result.errors.join('\n'));
      });
    });
  }

  Future<void> _perform(Future<void> Function() action) async {
    if (_busy) return;
    final revision = _revision;
    setState(() {
      _busy = true;
      _error = null;
      _result = null;
    });
    try {
      await action();
    } catch (error) {
      if (mounted && revision == _revision) {
        setState(
          () => _error = error is FormatException ? error.message : '$error',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => ToolScaffold(
    title: widget.inspectOnly ? '导入与符号' : 'Go 格式化',
    description: widget.inspectOnly
        ? '只解析当前输入，查看导入与声明；不执行代码，也不进行类型检查。'
        : '使用 Go 格式化器处理当前输入。结果可复制或放回输入框，项目文件需在编辑器中保存。',
    children: [
      _ProjectPicker(
        store: widget.store,
        selectedId: _project?.id,
        onChanged: (project) {
          _project = project;
          _files = const [];
          _file = null;
          _changed();
        },
      ),
      Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          OutlinedButton.icon(
            onPressed: _busy || _project == null ? null : _loadFiles,
            icon: const Icon(Icons.folder_open),
            label: const Text('列出源文件'),
          ),
          if (_files.isNotEmpty)
            OutlinedButton.icon(
              onPressed: _busy || _file == null ? null : _loadSource,
              icon: const Icon(Icons.file_open_outlined),
              label: const Text('读取所选文件'),
            ),
        ],
      ),
      if (_files.isNotEmpty)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: DropdownButtonFormField<String>(
            key: ValueKey('go-source-${_project?.id}'),
            initialValue: _file,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Go 源文件'),
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
            onChanged: _busy
                ? null
                : (value) {
                    _file = value;
                    _changed();
                  },
          ),
        ),
      ToolField(
        controller: _source,
        label: 'Go 源码',
        maxLines: 12,
        onChanged: (_) => _changed(),
      ),
      const SizedBox(height: 8),
      FilledButton.icon(
        onPressed: _busy ? null : _run,
        icon: Icon(
          widget.inspectOnly
              ? Icons.account_tree_outlined
              : Icons.format_align_left,
        ),
        label: Text(_busy ? '处理中…' : (widget.inspectOnly ? '分析源码' : '格式化')),
      ),
      ToolError(_error),
      if (_result?.formattedSource case final String output) ...[
        const SizedBox(height: 16),
        _CodeResult(title: '格式化结果', text: output),
        OutlinedButton(
          onPressed: () {
            _source.text = output;
            _changed();
          },
          child: const Text('用结果替换输入'),
        ),
      ],
      if (_result?.report case final String report) ...[
        const SizedBox(height: 16),
        _CodeResult(title: '源码结构', text: report),
      ],
    ],
  );
}

class GoModuleToolPage extends StatefulWidget {
  const GoModuleToolPage({super.key, required this.store, required this.tools});
  final ProjectStore store;
  final GoTools tools;

  @override
  State<GoModuleToolPage> createState() => _GoModuleToolPageState();
}

class _GoModuleToolPageState extends State<GoModuleToolPage> {
  Project? _project;
  String? _report;
  String? _error;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _project = GoTools.currentProject(widget.store);
  }

  Future<void> _inspect() async {
    final project = _project;
    if (project == null || _busy) return;
    setState(() {
      _busy = true;
      _report = null;
      _error = null;
    });
    try {
      final report = await widget.tools.inspectModule(project);
      if (mounted && _project?.id == project.id) {
        setState(() => _report = report.text);
      }
    } catch (error) {
      if (mounted && _project?.id == project.id) {
        setState(
          () => _error = error is FormatException ? error.message : '$error',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => ToolScaffold(
    title: 'Go 模块检查',
    description:
        '读取所选项目根目录的 go.mod、vendor 清单和项目内本地替换。这里只检查元数据；实际运行仍取决于当前运行时支持。',
    children: [
      _ProjectPicker(
        store: widget.store,
        selectedId: _project?.id,
        onChanged: (project) => setState(() {
          _project = project;
          _report = null;
          _error = null;
        }),
      ),
      if (_project case final Project project)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: SelectableText(project.path),
        ),
      FilledButton.icon(
        onPressed: _busy || _project == null ? null : _inspect,
        icon: const Icon(Icons.manage_search),
        label: Text(_busy ? '检查中…' : '检查依赖'),
      ),
      ToolError(_error),
      if (_report case final String report) ...[
        const SizedBox(height: 16),
        _CodeResult(title: '本地模块报告', text: report),
      ],
    ],
  );
}

class GoJsonStructToolPage extends StatefulWidget {
  const GoJsonStructToolPage({super.key});

  @override
  State<GoJsonStructToolPage> createState() => _GoJsonStructToolPageState();
}

class _GoJsonStructToolPageState extends State<GoJsonStructToolPage> {
  final _input = TextEditingController();
  final _name = TextEditingController(text: 'Payload');
  GoJsonStruct? _result;
  String? _error;

  @override
  void dispose() {
    _input.dispose();
    _name.dispose();
    super.dispose();
  }

  void _changed(String _) => setState(() {
    _result = null;
    _error = null;
  });

  void _generate() {
    setState(() {
      _result = null;
      _error = null;
      try {
        _result = GoJsonStruct.generate(
          _input.text,
          typeName: _name.text.trim(),
        );
      } on FormatException catch (error) {
        _error = error.message;
      }
    });
  }

  @override
  Widget build(BuildContext context) => ToolScaffold(
    title: 'JSON 转 Go 结构体',
    description: '从完整 JSON 对象推断字段和数组元素类型，保留原 JSON 键。结果基于样本推断，请确认可选字段和数值范围。',
    children: [
      ToolField(controller: _name, label: 'Go 类型名', onChanged: _changed),
      ToolField(
        controller: _input,
        label: 'JSON 对象',
        maxLines: 12,
        onChanged: _changed,
      ),
      const SizedBox(height: 8),
      FilledButton.icon(
        onPressed: _generate,
        icon: const Icon(Icons.transform),
        label: const Text('生成结构体'),
      ),
      ToolError(_error),
      if (_result case final GoJsonStruct result) ...[
        const SizedBox(height: 16),
        _CodeResult(title: 'Go 类型声明', text: result.source),
        for (final note in result.notes)
          Padding(padding: const EdgeInsets.only(top: 8), child: Text(note)),
      ],
    ],
  );
}

/// A vertical result avoids fixed label columns on phones and large text.
class _CodeResult extends StatelessWidget {
  const _CodeResult({required this.title, required this.text});
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) => ToolResultCard(
    children: [
      Wrap(
        spacing: 8,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleSmall),
          IconButton(
            tooltip: '复制$title',
            onPressed: () => Copy.copy(context, text),
            icon: const Icon(Icons.copy_all_outlined),
          ),
        ],
      ),
      SelectableText(
        text,
        style: const TextStyle(
          fontFamily: 'monospace',
          fontSize: 13,
          height: 1.5,
        ),
      ),
    ],
  );
}
