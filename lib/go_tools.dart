import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/store/project_store.dart';

typedef GoToolSourceAction =
    Future<GoToolSourceResult> Function(String source, String filePath);

class GoToolSourceResult {
  const GoToolSourceResult({
    this.formattedSource,
    this.report,
    this.errors = const [],
    this.unavailableReason,
  });

  final String? formattedSource;
  final String? report;
  final List<String> errors;
  final String? unavailableReason;
}

/// Local, non-executing Go tools. No method launches a dependency resolver.
class GoTools {
  GoTools({this.formatter, this.inspector});

  final GoToolSourceAction? formatter;
  final GoToolSourceAction? inspector;
  static const maxFileBytes = 1024 * 1024;

  Future<GoToolSourceResult> format(String source, String filePath) async =>
      formatter == null
      ? const GoToolSourceResult(unavailableReason: '当前 Go 格式化后端不可用')
      : formatter!(source, filePath);

  Future<GoToolSourceResult> inspect(String source, String filePath) async =>
      inspector == null
      ? const GoToolSourceResult(unavailableReason: '当前 Go 源码分析后端不可用')
      : inspector!(source, filePath);

  static List<Project> localProjects(ProjectStore store) => store.projects
      .where(
        (project) =>
            !project.isCloud &&
            (project.type.toLowerCase() == 'go' ||
                project.language.toLowerCase() == 'go'),
      )
      .toList();

  static Project? currentProject(ProjectStore store) {
    final projects = localProjects(store);
    for (final project in projects) {
      if (project.id == store.lastBrowsedProjectId) return project;
    }
    return projects.firstOrNull;
  }

  Future<List<String>> sourceFiles(Project project) async {
    _validateProject(project);
    final root = await Directory(project.path).resolveSymbolicLinks();
    final files = <String>[];
    Future<void> visit(Directory directory) async {
      await for (final entry in directory.list(followLinks: false)) {
        if (entry is Directory) {
          if (!{
            '.git',
            '.qfli',
            'vendor',
            'build',
          }.contains(p.basename(entry.path))) {
            await visit(entry);
          }
        } else if (entry is File && p.extension(entry.path) == '.go') {
          files.add(p.relative(entry.path, from: root));
          if (files.length > 1000) {
            throw const FormatException('项目超过 1000 个 Go 文件，请缩小项目范围');
          }
        }
      }
    }

    await visit(Directory(root));
    files.sort();
    return files;
  }

  Future<String> readSource(Project project, String relativePath) async {
    if (p.extension(relativePath) != '.go') {
      throw const FormatException('请选择 Go 源文件');
    }
    return _read(await _containedFile(project, relativePath));
  }

  Future<GoModuleReport> inspectModule(Project project) async {
    final manifest = await _containedFile(project, 'go.mod');
    if (!await manifest.exists()) {
      throw const FormatException('当前项目根目录没有 go.mod');
    }
    final parsed = GoModuleManifest.parse(await _read(manifest));
    final vendorFile = await _containedFile(
      project,
      p.join('vendor', 'modules.txt'),
    );
    final vendor = await vendorFile.exists() ? await _read(vendorFile) : '';
    final vendored = <String>{};
    for (final line in const LineSplitter().convert(vendor)) {
      final match = RegExp(r'^# (\S+) (v\S+)(?:\s|$)').firstMatch(line);
      if (match != null) vendored.add('${match[1]} ${match[2]}');
    }
    final dependencies = <GoDependencyInspection>[];
    for (final requirement in parsed.requirements) {
      final replacement =
          parsed.replacements
              .where((item) => item.path == requirement.path)
              .where(
                (item) =>
                    item.version == null || item.version == requirement.version,
              )
              .toList()
            ..sort(
              (a, b) => (a.version == null ? 1 : 0).compareTo(
                b.version == null ? 1 : 0,
              ),
            );
      final target = replacement.firstOrNull;
      var status = '未在 vendor/modules.txt 找到；未检查 SDK 缓存';
      if (vendored.contains('${requirement.path} ${requirement.version}')) {
        status = 'vendor 清单有记录；未验证包完整性';
      }
      if (target != null && target.targetVersion == null) {
        try {
          final localManifest = await _containedFile(
            project,
            p.join(target.target, 'go.mod'),
          );
          status = await localManifest.exists()
              ? '本地替换存在 go.mod；未验证包完整性'
              : '本地替换缺少 go.mod';
        } on FormatException {
          status = '本地替换位于项目外，未读取';
        }
      }
      dependencies.add(
        GoDependencyInspection(
          requirement: requirement,
          replacement: target,
          status: status,
        ),
      );
    }
    return GoModuleReport(manifest: parsed, dependencies: dependencies);
  }

  static void _validateProject(Project project) {
    if (project.isCloud) throw const FormatException('请选择本地 Go 项目');
    if (!Directory(project.path).existsSync()) {
      throw const FormatException('项目目录不存在');
    }
  }

  Future<File> _containedFile(Project project, String relativePath) async {
    _validateProject(project);
    final root = await Directory(project.path).resolveSymbolicLinks();
    final candidate = p.normalize(p.join(root, relativePath));
    if (!p.isWithin(root, candidate)) {
      throw const FormatException('文件位于项目外');
    }
    // Resolve the deepest existing ancestor, including links to missing files.
    var ancestor = candidate;
    while (FileSystemEntity.typeSync(ancestor, followLinks: false) ==
        FileSystemEntityType.notFound) {
      final parent = p.dirname(ancestor);
      if (parent == ancestor) throw const FormatException('文件路径不可用');
      ancestor = parent;
    }
    final resolved = await File(ancestor).resolveSymbolicLinks();
    if (!p.equals(root, resolved) && !p.isWithin(root, resolved)) {
      throw const FormatException('文件链接位于项目外');
    }
    return File(candidate);
  }

  Future<String> _read(File file) async {
    if (await file.length() > maxFileBytes) {
      throw const FormatException('文件超过 1 MiB，请选择较小的文件');
    }
    return file.readAsString();
  }
}

class GoModuleRequirement {
  const GoModuleRequirement(this.path, this.version, {this.indirect = false});
  final String path;
  final String version;
  final bool indirect;
}

class GoModuleReplacement {
  const GoModuleReplacement(
    this.path,
    this.version,
    this.target,
    this.targetVersion,
  );
  final String path;
  final String? version;
  final String target;
  final String? targetVersion;
}

class GoModuleManifest {
  const GoModuleManifest({
    required this.module,
    this.goVersion,
    this.toolchain,
    required this.requirements,
    required this.replacements,
    required this.otherDirectives,
  });

  final String module;
  final String? goVersion;
  final String? toolchain;
  final List<GoModuleRequirement> requirements;
  final List<GoModuleReplacement> replacements;
  final List<String> otherDirectives;

  /// Reads module metadata only; this is not Go's module/build validator.
  factory GoModuleManifest.parse(String source) {
    String? module;
    String? goVersion;
    String? toolchain;
    String? block;
    final requirements = <GoModuleRequirement>[];
    final replacements = <GoModuleReplacement>[];
    final others = <String>[];
    final lines = const LineSplitter().convert(source);
    for (var index = 0; index < lines.length; index++) {
      final words = _modWords(lines[index]);
      if (words.isEmpty) continue;
      final indirect = words.last == '// indirect';
      if (indirect) words.removeLast();
      if (words.isEmpty) continue;
      Never invalid() => throw FormatException('go.mod 第 ${index + 1} 行格式不正确');
      if (words.first == ')') {
        if (words.length != 1 || block == null) invalid();
        block = null;
        continue;
      }
      final directive = block ?? words.removeAt(0);
      if (words.length == 1 && words.first == '(') {
        if (block != null) invalid();
        block = directive;
        continue;
      }
      switch (directive) {
        case 'module':
          if (words.length != 1 || module != null || block != null) invalid();
          module = words.single;
        case 'go':
          if (words.length != 1 || goVersion != null || block != null) {
            invalid();
          }
          goVersion = words.single;
        case 'toolchain':
          if (words.length != 1 || toolchain != null || block != null) {
            invalid();
          }
          toolchain = words.single;
        case 'require':
          if (words.length != 2) invalid();
          requirements.add(
            GoModuleRequirement(words[0], words[1], indirect: indirect),
          );
        case 'replace':
          final arrow = words.indexOf('=>');
          if ((arrow != 1 && arrow != 2) ||
              words.length < arrow + 2 ||
              words.length > arrow + 3) {
            invalid();
          }
          replacements.add(
            GoModuleReplacement(
              words[0],
              arrow == 2 ? words[1] : null,
              words[arrow + 1],
              words.length == arrow + 3 ? words.last : null,
            ),
          );
        default:
          others.add('$directive ${words.join(' ')}');
      }
    }
    if (block != null) throw const FormatException('go.mod 缺少右括号');
    if (module == null || module.isEmpty) {
      throw const FormatException('go.mod 缺少 module 声明');
    }
    return GoModuleManifest(
      module: module,
      goVersion: goVersion,
      toolchain: toolchain,
      requirements: requirements,
      replacements: replacements,
      otherDirectives: others,
    );
  }
}

List<String> _modWords(String line) {
  final words = <String>[];
  var index = 0;
  while (index < line.length) {
    if (line[index].trim().isEmpty) {
      index++;
      continue;
    }
    if (line.startsWith('//', index)) {
      if (line.substring(index + 2).trim() == 'indirect') {
        words.add('// indirect');
      }
      break;
    }
    if (line[index] == '"' || line[index] == '`') {
      final quote = line[index++];
      final start = index - 1;
      var escaped = false;
      var closed = false;
      while (index < line.length) {
        final char = line[index++];
        if (char == quote && !escaped) {
          closed = true;
          break;
        }
        escaped = quote == '"' && char == r'\' && !escaped;
      }
      if (!closed) {
        throw const FormatException('go.mod 字符串未闭合');
      }
      final token = line.substring(start, index);
      if (quote == '`') {
        words.add(token.substring(1, token.length - 1));
      } else {
        // Standard JSON escapes cover ordinary quoted module paths. Refuse
        // unsupported Go-only escapes rather than inspecting a different path.
        try {
          words.add(jsonDecode(token) as String);
        } on FormatException {
          throw const FormatException('go.mod 路径包含暂不支持的转义');
        }
      }
    } else {
      final start = index;
      while (index < line.length &&
          line[index].trim().isNotEmpty &&
          !line.startsWith('//', index)) {
        index++;
      }
      words.add(line.substring(start, index));
    }
  }
  return words;
}

class GoDependencyInspection {
  const GoDependencyInspection({
    required this.requirement,
    this.replacement,
    required this.status,
  });
  final GoModuleRequirement requirement;
  final GoModuleReplacement? replacement;
  final String status;
}

class GoModuleReport {
  const GoModuleReport({required this.manifest, required this.dependencies});
  final GoModuleManifest manifest;
  final List<GoDependencyInspection> dependencies;

  String get text => [
    'module ${manifest.module}',
    if (manifest.goVersion != null) 'go ${manifest.goVersion}',
    if (manifest.toolchain != null) 'toolchain ${manifest.toolchain}',
    '',
    if (dependencies.isEmpty) '没有 require 依赖',
    for (final dependency in dependencies) ...[
      '${dependency.requirement.path} ${dependency.requirement.version}${dependency.requirement.indirect ? ' (indirect)' : ''}',
      if (dependency.replacement != null)
        '  => ${dependency.replacement!.target}${dependency.replacement!.targetVersion == null ? '' : ' ${dependency.replacement!.targetVersion}'}',
      '  ${dependency.status}',
    ],
    if (manifest.otherDirectives.isNotEmpty) ...[
      '',
      '其他声明（仅展示）：',
      ...manifest.otherDirectives,
    ],
    '',
    '仅检查本地元数据，不执行 go mod，也不下载依赖。',
  ].join('\n');
}

class GoJsonStruct {
  const GoJsonStruct(this.source, this.notes);
  final String source;
  final List<String> notes;

  static GoJsonStruct generate(String input, {String typeName = 'Payload'}) {
    if (input.length > GoTools.maxFileBytes) {
      throw const FormatException('JSON 超过 1 MiB，请缩小样本');
    }
    if (!RegExp(r'^[A-Z][A-Za-z0-9_]*$').hasMatch(typeName)) {
      throw const FormatException('类型名必须以大写字母开头，仅使用字母、数字和下划线');
    }
    final value = jsonDecode(input);
    if (value is! Map<String, dynamic>) {
      throw const FormatException('请输入 JSON 对象作为根节点');
    }
    final notes = <String>{};
    final shape = _JsonShape.from(value);
    final body = _renderJsonShape(shape, 0, notes);
    return GoJsonStruct('type $typeName $body\n', notes.toList());
  }
}

class _JsonShape {
  _JsonShape(this.kind, {this.nullable = false, this.fields, this.element});
  final String kind;
  bool nullable;
  final Map<String, _JsonShape>? fields;
  final _JsonShape? element;

  static _JsonShape from(Object? value, {int depth = 0}) {
    if (depth > 40) throw const FormatException('JSON 嵌套超过 40 层');
    return switch (value) {
      null => _JsonShape('null', nullable: true),
      bool() => _JsonShape('bool'),
      int() => _JsonShape('int64'),
      num() => _JsonShape('float64'),
      String() => _JsonShape('string'),
      Map<String, dynamic>() => _JsonShape(
        'object',
        fields: value.map(
          (key, value) => MapEntry(key, from(value, depth: depth + 1)),
        ),
      ),
      List() => _JsonShape(
        'array',
        element: value.isEmpty
            ? _JsonShape('any')
            : value.map((item) => from(item, depth: depth + 1)).reduce(merge),
      ),
      _ => _JsonShape('any'),
    };
  }

  static _JsonShape merge(_JsonShape left, _JsonShape right) {
    if (left.kind == 'null') {
      right.nullable = true;
      return right;
    }
    if (right.kind == 'null') {
      left.nullable = true;
      return left;
    }
    final nullable = left.nullable || right.nullable;
    if ({left.kind, right.kind}.difference({'int64', 'float64'}).isEmpty) {
      return _JsonShape(
        left.kind == right.kind ? left.kind : 'float64',
        nullable: nullable,
      );
    }
    if (left.kind != right.kind) return _JsonShape('any', nullable: nullable);
    if (left.kind == 'array') {
      return _JsonShape(
        'array',
        nullable: nullable,
        element: merge(left.element!, right.element!),
      );
    }
    if (left.kind == 'object') {
      final fields = <String, _JsonShape>{};
      for (final key in {...left.fields!.keys, ...right.fields!.keys}) {
        final a = left.fields![key];
        final b = right.fields![key];
        fields[key] = a != null && b != null ? merge(a, b) : (a ?? b)!;
        if (a == null || b == null) fields[key]!.nullable = true;
      }
      return _JsonShape('object', nullable: nullable, fields: fields);
    }
    return _JsonShape(left.kind, nullable: nullable);
  }
}

String _renderJsonShape(_JsonShape shape, int depth, Set<String> notes) {
  if (depth > 40) throw const FormatException('JSON 嵌套超过 40 层');
  String result;
  switch (shape.kind) {
    case 'object':
      if (shape.fields!.isEmpty) {
        result = 'map[string]any';
        notes.add('空对象、空数组或 null 的具体类型需要按业务补充。');
        break;
      }
      final names = <String>{};
      final lines = <String>['struct {'];
      for (final entry in shape.fields!.entries) {
        if (!_validGoJsonTag(entry.key)) {
          throw FormatException(
            'JSON 键 ${jsonEncode(entry.key)} 无法安全表示为 Go JSON 字段标签',
          );
        }
        final base = _goFieldName(entry.key);
        var name = base;
        var suffix = 2;
        while (!names.add(name)) {
          name = '$base${suffix++}';
        }
        final type = _renderJsonShape(entry.value, depth + 1, notes);
        lines.add(
          '${'\t' * (depth + 1)}$name $type `json:${jsonEncode(entry.key)}`',
        );
      }
      lines.add('${'\t' * depth}}');
      result = lines.join('\n');
    case 'array':
      result = '[]${_renderJsonShape(shape.element!, depth, notes)}';
    case 'null':
    case 'any':
      result = 'any';
      notes.add('空数组、null 或混合类型使用 any，请按业务确认。');
    default:
      result = shape.kind;
  }
  if (shape.nullable && result != 'any' && !result.startsWith('[]')) {
    result = '*$result';
    notes.add('可缺失或为 null 的字段使用指针；数组可使用 nil。');
  }
  return result;
}

bool _validGoJsonTag(String key) {
  if (key.isEmpty || key == '-') return false;
  const punctuation = '!#\$%&()*+-./:;<=>?@[]^_{|}~ ';
  final letterOrDigit = RegExp(r'^[\p{L}\p{Nd}]$', unicode: true);
  return key.runes.every((rune) {
    final char = String.fromCharCode(rune);
    return punctuation.contains(char) || letterOrDigit.hasMatch(char);
  });
}

String _goFieldName(String key) {
  const initialisms = {
    'id',
    'url',
    'http',
    'https',
    'json',
    'api',
    'uuid',
    'ip',
    'sql',
    'dns',
    'tls',
  };
  final words = key
      .replaceAllMapped(
        RegExp(r'([a-z0-9])([A-Z])'),
        (match) => '${match[1]} ${match[2]}',
      )
      .split(RegExp(r'[^A-Za-z0-9]+'))
      .where((word) => word.isNotEmpty);
  var name = words
      .map(
        (word) => initialisms.contains(word.toLowerCase())
            ? word.toUpperCase()
            : '${word[0].toUpperCase()}${word.substring(1)}',
      )
      .join();
  if (name.isEmpty) name = 'Field';
  if (RegExp(r'^[0-9]').hasMatch(name)) name = 'Field$name';
  return name;
}
