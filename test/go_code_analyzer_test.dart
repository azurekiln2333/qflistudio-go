import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_code_analyzer.dart';
import 'package:qfli_studio_core/services/code_analysis.dart';

class _Backend implements GoAnalysisBackend {
  _Backend(this.reply);

  final Map<String, Object?> Function(Map<String, dynamic>) reply;
  final requests = <Map<String, dynamic>>[];
  int formatCalls = 0;

  @override
  Future<String> analyze(String requestJson) async {
    final request = jsonDecode(requestJson) as Map<String, dynamic>;
    requests.add(request);
    return jsonEncode(reply(request));
  }

  @override
  Future<String> format(String requestJson) {
    formatCalls++;
    return analyze(requestJson);
  }
}

Map<String, Object?> _response(Map<String, dynamic> request) => {
  'schemaVersion': 1,
  'filePath': request['filePath'],
  'utf16Length': (request['source'] as String).length,
  'packageName': 'main',
  'diagnostics': <Object?>[],
  'imports': <Object?>[],
  'symbols': <Object?>[],
};

Map<String, Object?> _diagnostic(int start, int end) => {
  'startOffset': start,
  'endOffset': end,
  'message': "illegal character U+0040 '@'",
  'severity': 'error',
  'source': 'go/parser',
  'code': 'syntax',
};

void main() {
  final projectPath = p.absolute('analysis-project');
  final mainPath = p.join(projectPath, 'main.go');
  CodeAnalysisRequest request(List<CodeDocumentSnapshot> documents) =>
      CodeAnalysisRequest(
        projectPath: projectPath,
        activeFilePath: mainPath,
        language: 'go',
        revision: 42,
        documents: documents,
      );

  test(
    'analyzes exact unsaved snapshots and preserves UTF-16 CRLF ranges',
    () async {
      const source = 'package main\r\nvar 中文 = "😀"; var bad = @\r\n';
      final at = source.indexOf('@');
      final backend = _Backend(
        (value) => {
          ..._response(value),
          'diagnostics': [_diagnostic(at, at + 1)],
        },
      );
      final result = await GoCodeAnalyzer(backend: backend).analyze(
        request([
          CodeDocumentSnapshot(path: mainPath, text: source, revision: 42),
        ]),
      );
      expect(result.unavailableReason, isNull);
      expect(backend.requests.single['source'], source);
      expect(result.diagnostics.single.filePath, mainPath);
      expect(result.diagnostics.single.startOffset, at);
      expect(result.diagnostics.single.endOffset, at + 1);
      expect(source.substring(at, at + 1), '@');
    },
  );

  test(
    'analyzes sibling open Go buffers and excludes foreign projects',
    () async {
      final backend = _Backend(_response);
      final sibling = p.join(projectPath, 'helper.go');
      final result = await GoCodeAnalyzer(backend: backend).analyze(
        request([
          CodeDocumentSnapshot(
            path: mainPath,
            text: 'package main',
            revision: 42,
          ),
          CodeDocumentSnapshot(
            path: sibling,
            text: 'package main',
            revision: 7,
          ),
          CodeDocumentSnapshot(
            path: p.absolute('foreign', 'main.go'),
            text: 'foreign',
            revision: 1,
          ),
          CodeDocumentSnapshot(
            path: p.join(projectPath, 'note.txt'),
            text: 'not Go',
            revision: 1,
          ),
        ]),
      );
      expect(result.unavailableReason, isNull);
      expect(backend.requests.map((item) => item['filePath']), [
        mainPath,
        sibling,
      ]);
    },
  );

  test(
    'missing or stale active snapshots never become successful empty results',
    () async {
      final backend = _Backend(_response);
      final analyzer = GoCodeAnalyzer(backend: backend);
      for (final documents in <List<CodeDocumentSnapshot>>[
        [],
        [CodeDocumentSnapshot(path: mainPath, text: 'old', revision: 41)],
      ]) {
        final result = await analyzer.analyze(request(documents));
        expect(result.unavailableReason, isNotEmpty);
      }
      expect(backend.requests, isEmpty);
    },
  );

  test(
    'malformed, foreign, oversized and old native responses are unavailable',
    () async {
      final changes = <Map<String, Object?>>[
        {'schemaVersion': 2},
        {'filePath': 'foreign.go'},
        {'utf16Length': 999},
        {
          'diagnostics': [_diagnostic(-1, 1)],
        },
        {
          'diagnostics': [_diagnostic(1, 999)],
        },
        {
          'diagnostics': [_diagnostic(2, 1)],
        },
        {'diagnostics': 'invalid'},
        {'imports': null},
        {'error': 'native parser failed'},
        {'error': ''},
      ];
      for (final change in changes) {
        final tools = GoSourceTools(
          backend: _Backend((value) => {..._response(value), ...change}),
        );
        final result = await tools.inspect(
          source: 'package main',
          filePath: mainPath,
        );
        expect(result.unavailableReason, isNotEmpty, reason: '$change');
      }
      final backend = _Backend(_response);
      final oversized = await GoSourceTools(backend: backend).inspect(
        source: 'x' * (GoSourceTools.maxSourceBytes + 1),
        filePath: mainPath,
      );
      expect(oversized.unavailableReason, contains('4 MiB'));
      expect(backend.requests, isEmpty);
    },
  );

  test('typed AST report and format results use the shared decoder', () async {
    final backend = _Backend(
      (value) => {
        ..._response(value),
        'imports': [
          {'path': 'fmt', 'alias': 'f', 'startOffset': 0, 'endOffset': 3},
        ],
        'symbols': [
          {
            'name': '方法',
            'kind': 'method',
            'receiver': '*数据',
            'startOffset': 2,
            'endOffset': 4,
          },
        ],
        'formattedSource': 'package main\n',
      },
    );
    final tools = GoSourceTools(backend: backend);
    final inspection = await tools.inspect(
      source: 'package main',
      filePath: mainPath,
    );
    expect(inspection.imports.single.path, 'fmt');
    expect(inspection.symbols.single.receiver, '*数据');
    expect(inspection.report, contains('import f "fmt"'));
    expect(inspection.report, contains('method (*数据) 方法'));
    final format = await tools.format(
      source: 'package main',
      filePath: mainPath,
    );
    expect(format.formattedSource, 'package main\n');
    expect(format.unavailableReason, isNull);
    expect(backend.formatCalls, 1);
  });

  test(
    'format errors retain diagnostics without inventing formatted source',
    () async {
      final tools = GoSourceTools(
        backend: _Backend(
          (value) => {
            ..._response(value),
            'diagnostics': [_diagnostic(0, 1)],
          },
        ),
      );
      final result = await tools.format(source: '@', filePath: mainPath);
      expect(result.diagnostics, hasLength(1));
      expect(result.formattedSource, isNull);
      expect(result.unavailableReason, isNull);
    },
  );

  test(
    'real FFI parser and formatter handle Unicode and cannot run user code',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'go-analysis-test-',
      );
      addTearDown(() => directory.delete(recursive: true));
      final file = File(p.join(directory.path, 'main.go'));
      await file.writeAsString('saved invalid source');
      final marker = p.join(directory.path, 'must-not-exist');
      final source =
          '''package main\r
import "os"\r
var _ = func() int { os.WriteFile(${jsonEncode(marker)}, []byte("init"), 0600); return 1 }()\r
func main(){os.WriteFile(${jsonEncode(marker)}, []byte("main"), 0600)}\r
''';
      final tools = GoSourceTools();
      final inspection = await tools.inspect(
        source: source,
        filePath: file.path,
      );
      expect(inspection.unavailableReason, isNull);
      expect(inspection.diagnostics, isEmpty);
      expect(inspection.imports.single.path, 'os');
      final formatted = await tools.format(source: source, filePath: file.path);
      expect(formatted.unavailableReason, isNull);
      expect(formatted.formattedSource, contains('func main()'));
      expect(await File(marker).exists(), isFalse);
      expect(await file.readAsString(), 'saved invalid source');
      const invalid = 'package main\r\nvar 中文 = "😀"; var bad = 💥\r\n';
      final result = await tools.inspect(source: invalid, filePath: file.path);
      expect(result.unavailableReason, isNull);
      final start = invalid.indexOf('💥');
      expect(
        result.diagnostics.any(
          (item) => item.startOffset == start && item.endOffset == start + 2,
        ),
        isTrue,
      );
    },
    skip: Platform.environment['QFLI_GO_RUNTIME_LIBRARY'] == null
        ? 'Set QFLI_GO_RUNTIME_LIBRARY to a rebuilt native library'
        : false,
  );
}
