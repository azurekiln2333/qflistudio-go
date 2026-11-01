import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_go/go_code_analyzer.dart';
import 'package:qfli_go/go_ide_tools.dart';

class _Backend implements GoAnalysisBackend {
  bool fail = false;
  final requests = <String>[];

  @override
  Future<String> analyze(String requestJson) async {
    requests.add(requestJson);
    if (fail) throw StateError('native library unavailable');
    final request = jsonDecode(requestJson) as Map<String, dynamic>;
    return jsonEncode({
      'schemaVersion': 1,
      'filePath': request['filePath'],
      'utf16Length': (request['source'] as String).length,
      'packageName': 'main',
      'diagnostics': [],
      'imports': [],
      'symbols': [
        {
          'name': 'main',
          'kind': 'function',
          'receiver': '',
          'startOffset': 0,
          'endOffset': 1,
        },
      ],
      'formattedSource': 'package main\n',
    });
  }

  @override
  Future<String> format(String requestJson) => analyze(requestJson);
}

void main() {
  test(
    'tool actions use the native source adapter and surface failures',
    () async {
      final backend = _Backend();
      final tools = createGoIdeTools(backend: backend);
      final formatted = await tools.format('package main', '/project/main.go');
      expect(formatted.formattedSource, 'package main\n');
      expect(formatted.unavailableReason, isNull);
      final inspection = await tools.inspect(
        'package main',
        '/project/main.go',
      );
      expect(inspection.report, contains('function main'));
      expect(backend.requests, hasLength(2));
      backend.fail = true;
      final failed = await tools.format('package main', '/project/main.go');
      expect(failed.formattedSource, isNull);
      expect(failed.unavailableReason, contains('native library unavailable'));
    },
  );
}
