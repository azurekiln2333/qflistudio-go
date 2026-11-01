import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/native_go_bridge_ffi.dart';

void main() {
  const proof = {
    'engine': 'qfli-embedded-testing-v1',
    'testsRun': 3,
    'testsPassed': 1,
    'testsFailed': 1,
    'testsSkipped': 1,
    'benchmarksRun': 2,
    'fuzzSeedsRun': 4,
  };
  test('raw run decoder preserves exact native execution evidence', () {
    final value = {
      'stdout': 'output\n',
      'stderr': 'error',
      'exitCode': 1,
      'testExecution': proof,
    };
    final result = NativeGoResult.decode(jsonEncode(value));
    expect(result.stdout, 'output\n');
    expect(result.exitCode, 1);
    expect(result.testExecution!.testsFailed, 1);
    expect(result.toJson(), value);
  });

  test('ordinary run has no fabricated test evidence', () {
    final result = NativeGoResult.decode(
      '{"stdout":"hello","stderr":"","exitCode":0}',
    );
    expect(result.testExecution, isNull);
    expect(result.toJson().containsKey('testExecution'), isFalse);
  });

  test('invalid evidence is rejected at the single typed boundary', () {
    for (final value in <Map<String, Object?>>[
      {'stdout': '', 'stderr': '', 'exitCode': '0'},
      {'stdout': '', 'stderr': '', 'exitCode': 0, 'testExecution': 'invalid'},
      for (final field in proof.keys)
        {
          'stdout': '',
          'stderr': '',
          'exitCode': 0,
          'testExecution': {...proof, field: field == 'engine' ? '' : -1},
        },
      {
        'stdout': '',
        'stderr': '',
        'exitCode': 0,
        'testExecution': {...proof, 'testsRun': 1.5},
      },
    ]) {
      expect(
        () => NativeGoResult.decode(jsonEncode(value)),
        throwsFormatException,
      );
    }
  });

  final library = Platform.environment['QFLI_GO_RUNTIME_LIBRARY'];
  test(
    'real native call retains evidence and cancellation owns the same run',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'native-test-proof-',
      );
      addTearDown(() => directory.delete(recursive: true));
      final entry = File(p.join(directory.path, 'actual_test.go'));
      await entry.writeAsString('''package checks
import "testing"
func TestActual(t *testing.T) { t.Run("child", func(t *testing.T){}) }
func FuzzSeed(f *testing.F) { f.Add("x"); f.Fuzz(func(t *testing.T, x string){if x != "x" {t.Fatal(x)}}) }
''');
      final execution = startNativeGo(
        projectPath: directory.path,
        entryFile: entry.path,
      );
      final result = await execution.result.timeout(
        const Duration(seconds: 10),
      );
      expect(result.exitCode, 0, reason: result.stderr);
      expect(result.testExecution!.engine, 'qfli-embedded-testing-v1');
      expect(result.testExecution!.testsRun, 2);
      expect(result.testExecution!.testsPassed, 2);
      expect(result.testExecution!.fuzzSeedsRun, 1);
      expect(result.stdout, contains('--- PASS: TestActual/child'));
      await entry.writeAsString(
        'package checks\nimport "testing"\nfunc TestLoop(t *testing.T){for {}}\n',
      );
      final running = startNativeGo(
        projectPath: directory.path,
        entryFile: entry.path,
      );
      await running.cancel();
      final cancelled = await running.result.timeout(
        const Duration(seconds: 5),
      );
      expect(cancelled.exitCode, 1);
      expect(cancelled.stderr, contains('canceled'));
    },
    skip: library == null ? 'Requires rebuilt QFLI_GO_RUNTIME_LIBRARY' : false,
  );
}
