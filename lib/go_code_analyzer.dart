import 'dart:convert';

import 'package:path/path.dart' as p;
import 'package:qfli_studio_core/services/code_analysis.dart';

import 'native_go_analysis_stub.dart'
    if (dart.library.ffi) 'native_go_analysis_ffi.dart'
    as native;

/// JSON transport only. Decoding and range validation belong to [GoSourceTools].
abstract interface class GoAnalysisBackend {
  Future<String> analyze(String requestJson);
  Future<String> format(String requestJson);
}

class _NativeGoAnalysisBackend implements GoAnalysisBackend {
  const _NativeGoAnalysisBackend();

  @override
  Future<String> analyze(String requestJson) =>
      native.analyzeNativeGo(requestJson);

  @override
  Future<String> format(String requestJson) =>
      native.formatNativeGo(requestJson);
}

class GoSourceImport {
  const GoSourceImport({
    required this.path,
    required this.alias,
    required this.startOffset,
    required this.endOffset,
  });

  final String path;
  final String alias;
  final int startOffset;
  final int endOffset;
}

class GoSourceSymbol {
  const GoSourceSymbol({
    required this.name,
    required this.kind,
    required this.receiver,
    required this.startOffset,
    required this.endOffset,
  });

  final String name;
  final String kind;
  final String receiver;
  final int startOffset;
  final int endOffset;
}

class GoSourceAnalysis {
  const GoSourceAnalysis({
    this.packageName = '',
    this.diagnostics = const [],
    this.imports = const [],
    this.symbols = const [],
    this.unavailableReason,
  });

  final String packageName;
  final List<CodeDiagnostic> diagnostics;
  final List<GoSourceImport> imports;
  final List<GoSourceSymbol> symbols;
  final String? unavailableReason;

  /// A syntax/AST report, without claiming imports resolve or types are valid.
  String get report => [
    if (packageName.isNotEmpty) 'package $packageName',
    for (final item in imports)
      'import ${item.alias.isEmpty ? '' : '${item.alias} '}${jsonEncode(item.path)}',
    for (final item in symbols)
      '${item.kind} ${item.receiver.isEmpty ? '' : '(${item.receiver}) '}${item.name}',
    for (final item in diagnostics)
      '${item.source}: ${item.message} [${item.startOffset}, ${item.endOffset})',
  ].join('\n');
}

class GoFormatResult {
  const GoFormatResult({
    this.formattedSource,
    this.diagnostics = const [],
    this.unavailableReason,
  });

  final String? formattedSource;
  final List<CodeDiagnostic> diagnostics;
  final String? unavailableReason;
}

/// Parses current UTF-8 source and formats it in the bundled Go library.
/// These operations never execute source, resolve imports, or write files.
class GoSourceTools {
  GoSourceTools({GoAnalysisBackend? backend})
    : _backend = backend ?? const _NativeGoAnalysisBackend();

  static const maxSourceBytes = 4 * 1024 * 1024;
  final GoAnalysisBackend _backend;

  Future<GoSourceAnalysis> inspect({
    required String source,
    required String filePath,
  }) async {
    try {
      final result = await _invoke(source, filePath, formatting: false);
      return GoSourceAnalysis(
        packageName: result.packageName,
        diagnostics: result.diagnostics,
        imports: result.imports,
        symbols: result.symbols,
      );
    } catch (error) {
      return GoSourceAnalysis(unavailableReason: 'Go source analysis: $error');
    }
  }

  Future<GoFormatResult> format({
    required String source,
    required String filePath,
  }) async {
    try {
      final result = await _invoke(source, filePath, formatting: true);
      if (result.formattedSource == null && result.diagnostics.isEmpty) {
        throw const FormatException('Go formatter returned no source');
      }
      return GoFormatResult(
        formattedSource: result.formattedSource,
        diagnostics: result.diagnostics,
      );
    } catch (error) {
      return GoFormatResult(unavailableReason: 'Go formatting: $error');
    }
  }

  Future<_GoSourceResponse> _invoke(
    String source,
    String filePath, {
    required bool formatting,
  }) async {
    if (filePath.isEmpty) {
      throw const FormatException('A Go source file path is required');
    }
    if (utf8.encode(source).length > maxSourceBytes) {
      throw const FormatException('Go source exceeds the 4 MiB analysis limit');
    }
    final requestJson = jsonEncode({'filePath': filePath, 'source': source});
    final encoded = await (formatting
        ? _backend.format(requestJson)
        : _backend.analyze(requestJson));
    return _GoSourceResponse.decode(encoded, filePath, source.length);
  }
}

/// Syntax checks the exact open buffers in their owning project. The shared
/// editor owns debouncing and rejects results whose snapshot revision changed.
class GoCodeAnalyzer implements CodeAnalyzer {
  GoCodeAnalyzer({GoAnalysisBackend? backend})
    : _tools = GoSourceTools(backend: backend);

  final GoSourceTools _tools;

  @override
  Future<CodeAnalysisResult> analyze(CodeAnalysisRequest request) async {
    if (request.language.toLowerCase() != 'go') {
      return const CodeAnalysisResult(
        unavailableReason: 'Go analyzer requires a Go document',
      );
    }
    if (!p.isAbsolute(request.projectPath) ||
        !p.isAbsolute(request.activeFilePath) ||
        !p.isWithin(request.projectPath, request.activeFilePath)) {
      return const CodeAnalysisResult(
        unavailableReason: 'Go source must belong to the selected project',
      );
    }
    CodeDocumentSnapshot? active;
    final documents = <String, CodeDocumentSnapshot>{};
    for (final document in request.documents) {
      if (!p.isAbsolute(document.path) ||
          !p.isWithin(request.projectPath, document.path) ||
          p.extension(document.path) != '.go') {
        continue;
      }
      final key = p.normalize(document.path);
      if (documents.containsKey(key)) {
        return const CodeAnalysisResult(
          unavailableReason: 'Duplicate Go source snapshots',
        );
      }
      documents[key] = document;
      if (p.equals(document.path, request.activeFilePath)) active = document;
    }
    if (active == null || active.revision != request.revision) {
      return const CodeAnalysisResult(
        unavailableReason: 'The current Go source snapshot is unavailable',
      );
    }
    final diagnostics = <CodeDiagnostic>[];
    for (final document in documents.values) {
      final result = await _tools.inspect(
        source: document.text,
        filePath: document.path,
      );
      if (result.unavailableReason != null) {
        return CodeAnalysisResult(unavailableReason: result.unavailableReason);
      }
      diagnostics.addAll(result.diagnostics);
    }
    return CodeAnalysisResult(diagnostics: List.unmodifiable(diagnostics));
  }
}

/// The single typed boundary for native payloads used by both UI consumers.
class _GoSourceResponse {
  const _GoSourceResponse({
    required this.packageName,
    required this.diagnostics,
    required this.imports,
    required this.symbols,
    required this.formattedSource,
  });

  final String packageName;
  final List<CodeDiagnostic> diagnostics;
  final List<GoSourceImport> imports;
  final List<GoSourceSymbol> symbols;
  final String? formattedSource;

  static _GoSourceResponse decode(
    String encoded,
    String filePath,
    int sourceLength,
  ) {
    final decoded = jsonDecode(encoded);
    if (decoded is! Map<String, dynamic> || decoded['schemaVersion'] != 1) {
      throw const FormatException('Invalid Go analysis response version');
    }
    final error = decoded['error'];
    if (error != null) {
      if (error is! String || error.isEmpty) {
        throw const FormatException('Invalid Go analysis error');
      }
      throw StateError(error);
    }
    if (decoded['filePath'] != filePath ||
        decoded['utf16Length'] != sourceLength) {
      throw const FormatException('Go analysis source identity mismatch');
    }
    String stringField(Map<String, dynamic> value, String name) {
      final field = value[name];
      if (field is! String) {
        throw FormatException('Invalid Go analysis $name');
      }
      return field;
    }

    List<T> items<T>(
      String name,
      T Function(Map<String, dynamic>, int, int) decode,
    ) {
      final field = decoded[name];
      if (field is! List) {
        throw FormatException('Invalid Go analysis $name');
      }
      return List<T>.unmodifiable(
        field.map((item) {
          if (item is! Map<String, dynamic>) {
            throw FormatException('Invalid Go analysis $name item');
          }
          final start = item['startOffset'];
          final end = item['endOffset'];
          if (start is! int ||
              end is! int ||
              start < 0 ||
              end < start ||
              end > sourceLength) {
            throw const FormatException('Invalid Go analysis UTF-16 range');
          }
          return decode(item, start, end);
        }),
      );
    }

    final diagnostics = items('diagnostics', (value, start, end) {
      final severity = switch (stringField(value, 'severity')) {
        'error' => CodeDiagnosticSeverity.error,
        'warning' => CodeDiagnosticSeverity.warning,
        'information' => CodeDiagnosticSeverity.information,
        'hint' => CodeDiagnosticSeverity.hint,
        _ => throw const FormatException('Invalid Go diagnostic severity'),
      };
      return CodeDiagnostic(
        filePath: filePath,
        startOffset: start,
        endOffset: end,
        message: stringField(value, 'message'),
        severity: severity,
        source: stringField(value, 'source'),
        code: stringField(value, 'code'),
      );
    });
    final imports = items(
      'imports',
      (value, start, end) => GoSourceImport(
        path: stringField(value, 'path'),
        alias: stringField(value, 'alias'),
        startOffset: start,
        endOffset: end,
      ),
    );
    final symbols = items(
      'symbols',
      (value, start, end) => GoSourceSymbol(
        name: stringField(value, 'name'),
        kind: stringField(value, 'kind'),
        receiver: stringField(value, 'receiver'),
        startOffset: start,
        endOffset: end,
      ),
    );
    final formatted = decoded['formattedSource'];
    if (formatted != null && formatted is! String) {
      throw const FormatException('Invalid Go formatted source');
    }
    return _GoSourceResponse(
      packageName: stringField(decoded, 'packageName'),
      diagnostics: diagnostics,
      imports: imports,
      symbols: symbols,
      formattedSource: formatted as String?,
    );
  }
}
