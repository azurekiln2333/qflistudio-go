import 'dart:convert';

/// The actual native run result, including evidence from the embedded engine.
class NativeGoResult {
  const NativeGoResult({
    required this.stdout,
    required this.stderr,
    required this.exitCode,
    this.testExecution,
  });

  final String stdout;
  final String stderr;
  final int exitCode;
  final NativeGoTestExecution? testExecution;

  factory NativeGoResult.decode(String encoded) {
    final value = jsonDecode(encoded);
    if (value is! Map<String, dynamic>) {
      throw const FormatException('Invalid native Go result');
    }
    return NativeGoResult.fromJson(value);
  }

  factory NativeGoResult.fromJson(Map<String, dynamic> value) {
    final stdout = value['stdout'];
    final stderr = value['stderr'];
    final exitCode = value['exitCode'];
    final proof = value['testExecution'];
    if (stdout is! String ||
        stderr is! String ||
        exitCode is! int ||
        (proof != null && proof is! Map<String, dynamic>)) {
      throw const FormatException('Invalid native Go result fields');
    }
    return NativeGoResult(
      stdout: stdout,
      stderr: stderr,
      exitCode: exitCode,
      testExecution: proof == null
          ? null
          : NativeGoTestExecution.fromJson(proof as Map<String, dynamic>),
    );
  }

  Map<String, Object?> toJson() => {
    'stdout': stdout,
    'stderr': stderr,
    'exitCode': exitCode,
    if (testExecution != null) 'testExecution': testExecution!.toJson(),
  };
}

class NativeGoTestExecution {
  const NativeGoTestExecution({
    required this.engine,
    required this.testsRun,
    required this.testsPassed,
    required this.testsFailed,
    required this.testsSkipped,
    required this.benchmarksRun,
    required this.fuzzSeedsRun,
  });

  final String engine;
  final int testsRun;
  final int testsPassed;
  final int testsFailed;
  final int testsSkipped;
  final int benchmarksRun;
  final int fuzzSeedsRun;

  factory NativeGoTestExecution.fromJson(Map<String, dynamic> value) {
    final engine = value['engine'];
    if (engine is! String || engine.isEmpty) {
      throw const FormatException('Invalid embedded test engine');
    }
    int count(String field) {
      final count = value[field];
      if (count is! int || count < 0) {
        throw FormatException('Invalid embedded test $field');
      }
      return count;
    }

    return NativeGoTestExecution(
      engine: engine,
      testsRun: count('testsRun'),
      testsPassed: count('testsPassed'),
      testsFailed: count('testsFailed'),
      testsSkipped: count('testsSkipped'),
      benchmarksRun: count('benchmarksRun'),
      fuzzSeedsRun: count('fuzzSeedsRun'),
    );
  }

  Map<String, Object?> toJson() => {
    'engine': engine,
    'testsRun': testsRun,
    'testsPassed': testsPassed,
    'testsFailed': testsFailed,
    'testsSkipped': testsSkipped,
    'benchmarksRun': benchmarksRun,
    'fuzzSeedsRun': fuzzSeedsRun,
  };
}

class NativeGoExecution {
  const NativeGoExecution({required this.result, required this.cancel});

  final Future<NativeGoResult> result;
  final Future<void> Function() cancel;
}
