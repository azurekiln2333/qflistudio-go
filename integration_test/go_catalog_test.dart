/// Executes the Python-generated exhaustive inventory through the actual
/// packaged FFI bridge. A host run cannot satisfy this integration test.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_platform.dart';
import 'package:qfli_go/native_go_bridge_ffi.dart' as native;
import 'package:qfli_studio_core/tools/offline_tools.dart';
import 'package:qfli_studio_core/services/code_import_service.dart';
import 'package:qfli_studio_core/services/example_input_fixtures.dart';

import 'go_native_ide_acceptance.dart';
import 'go_product_ui_acceptance.dart';

String catalogAuditSha256(List<int> bytes) => OfflineDigest.sha256Bytes(
  bytes,
).map((byte) => byte.toRadixString(16).padLeft(2, '0')).join();

Map<String, dynamic> _object(Object? value) =>
    Map<String, dynamic>.from(value as Map);

String _normalized(String value) {
  final text = value.replaceAll('\r\n', '\n');
  return text.endsWith('\n') ? text.substring(0, text.length - 1) : text;
}

class CatalogAuditExecution {
  const CatalogAuditExecution({
    required this.stdout,
    required this.stderr,
    required this.exitCode,
    this.timedOut = false,
    this.testExecution,
    this.nativeOwnership,
  });

  final String stdout;
  final String stderr;
  final int exitCode;
  final bool timedOut;
  final Map<String, Object?>? testExecution;
  final Map<String, Object?>? nativeOwnership;

  Map<String, Object?> toJson() => {
    'stdout': stdout,
    'stderr': stderr,
    'exitCode': exitCode,
    'timedOut': timedOut,
    if (testExecution != null) 'testExecution': testExecution,
    if (nativeOwnership != null) 'nativeOwnership': nativeOwnership,
  };
}

class CatalogAuditCase {
  CatalogAuditCase.fromJson(Map<String, dynamic> data)
    : data = Map.unmodifiable(data);

  final Map<String, dynamic> data;
  String get id => data['id'] as String;
  String get topic => data['topic'] as String;
  String get shape => data['shape'] as String;
  String get operation => data['operation'] as String;
  String get entryFile => data['entryFile'] as String;
  List<Map<String, dynamic>> get files =>
      (data['files'] as List).map(_object).toList();

  List<String> check(CatalogAuditExecution result) {
    final errors = <String>[];
    if (result.timedOut) errors.add('execution timed out');
    if (result.exitCode != data['expectedExitCode']) {
      errors.add(
        'exit: expected ${data['expectedExitCode']}, got ${result.exitCode}',
      );
    }
    if (_normalized(result.stderr) !=
        _normalized(data['expectedStderr'] as String? ?? '')) {
      errors.add('stderr mismatch: ${result.stderr}');
    }
    if ((data['stdin'] as String? ?? '').isNotEmpty) {
      errors.add('the packaged bridge does not supply stdin');
    }
    final verification = _object(data['verification']);
    final expected = _normalized(verification['expected'] as String? ?? '');
    final actual = _normalized(result.stdout);
    switch (verification['kind']) {
      case 'stdout-exact':
        if (expected != actual) {
          errors.add('stdout mismatch: expected $expected, got $actual');
        }
      case 'stdout-sorted':
      case 'stdout-normalized':
        List<String> lines(String text) => text
            .split('\n')
            .map((line) => line.trim())
            .where((line) => line.isNotEmpty)
            .toList();
        final want = lines(expected);
        final got = lines(actual);
        if (verification['kind'] == 'stdout-sorted') {
          want.sort();
          got.sort();
        }
        if (jsonEncode(want) != jsonEncode(got)) {
          errors.add('normalized stdout mismatch: expected $want, got $got');
        }
      case 'test-pass':
      case 'bench-exists':
        errors.addAll(_checkTestExecution(result));
      default:
        errors.add('unknown verification kind ${verification['kind']}');
    }
    return errors;
  }

  List<String> _checkTestExecution(CatalogAuditExecution result) {
    final execution = result.testExecution;
    if (operation != 'test' ||
        execution == null ||
        execution['engine'] != 'qfli-embedded-testing-v1') {
      return ['missing genuine embedded test execution metadata'];
    }
    const fields = [
      'testsRun',
      'testsPassed',
      'testsFailed',
      'testsSkipped',
      'benchmarksRun',
      'fuzzSeedsRun',
    ];
    if (fields.any(
      (field) => execution[field] is! int || (execution[field] as int) < 0,
    )) {
      return ['invalid embedded test execution counts'];
    }
    final errors = <String>[];
    final run = execution['testsRun'] as int;
    final passed = execution['testsPassed'] as int;
    final failed = execution['testsFailed'] as int;
    final skipped = execution['testsSkipped'] as int;
    if (run != passed + failed + skipped) {
      errors.add('inconsistent embedded test execution counts');
    }
    if (failed != 0 || skipped != 0) {
      errors.add('embedded tests failed or were skipped');
    }
    final names = (data['expectedTestNames'] as List? ?? []).cast<String>();
    if (passed < names.length) {
      errors.add('not every declared test/fuzz function executed successfully');
    }
    if ((execution['fuzzSeedsRun'] as int) <
        (data['minimumFuzzSeeds'] as int? ?? 0)) {
      errors.add('not every declared fuzz seed executed');
    }
    if (_object(data['verification'])['kind'] == 'bench-exists') {
      final benchmarks = (data['expectedBenchmarkNames'] as List? ?? []).length;
      if ((execution['benchmarksRun'] as int) <
          (benchmarks == 0 ? 1 : benchmarks)) {
        errors.add('not every declared benchmark executed');
      }
    } else if (passed == 0) {
      errors.add('no successful test function execution');
    }
    for (final name in names) {
      if (!RegExp(
        '^--- PASS: ${RegExp.escape(name)}(?:\\s|\$)',
        multiLine: true,
      ).hasMatch(result.stdout)) {
        errors.add('missing passing transcript for $name');
      }
    }
    if (!RegExp(r'^PASS$', multiLine: true).hasMatch(result.stdout)) {
      errors.add('no final embedded test PASS');
    }
    return errors;
  }

  Future<void> materialize(Directory project) async {
    ExampleInputFixtures.files({
      for (final fixture in files) fixture['path'] as String: '',
    });
    final paths = <String>{};
    for (final fixture in files) {
      final name = fixture['path'] as String;
      if (name.isEmpty ||
          name.contains('\\') ||
          name.contains(':') ||
          p.posix.isAbsolute(name) ||
          name.split('/').any((part) => part == '.' || part == '..') ||
          !paths.add(name)) {
        throw FormatException('unsafe/duplicate fixture path: $name');
      }
      final bytes = base64Decode(fixture['contentBase64'] as String);
      if (catalogAuditSha256(bytes) != fixture['sha256']) {
        throw FormatException('$id fixture hash mismatch: $name');
      }
      final target = File(p.joinAll([project.path, ...name.split('/')]));
      await target.parent.create(recursive: true);
      await target.writeAsBytes(bytes, flush: true);
    }
    if (!paths.contains(entryFile)) {
      throw FormatException('$id entry source is absent: $entryFile');
    }
  }
}

class CatalogAuditManifest {
  CatalogAuditManifest.fromJson(Map<String, dynamic> data)
    : data = Map.unmodifiable(data),
      cases = (data['cases'] as List)
          .map((value) => CatalogAuditCase.fromJson(_object(value)))
          .toList(growable: false);

  final Map<String, dynamic> data;
  final List<CatalogAuditCase> cases;

  /// Coverage is independently derived from the loaded product catalogs.
  /// A stale manifest, omitted case, duplicate result or changed displayed
  /// bytes therefore fails even if the remaining runs all return zero.
  List<String> validateCatalogs({
    required List<int> tutorials,
    required List<int> examples,
  }) {
    final issues = [
      for (final issue in data['inventoryIssues'] as List) issue.toString(),
    ];
    if (data['schemaVersion'] != 1) issues.add('unknown manifest schema');
    final expectedBlocks = <String, String>{};
    final expectedOutput = <String, String>{};
    final expectedFixtures = <String, Map<String, dynamic>>{};
    final expectedEntryFiles = <String, String>{};
    final expectedTopics = <String>{};
    final topicSets = <String, Set<String>>{};
    final catalogs = _object(data['catalogs']);
    for (final (kind, bytes) in [
      ('tutorial', tutorials),
      ('example', examples),
    ]) {
      if (catalogAuditSha256(bytes) != _object(catalogs[kind])['sha256']) {
        issues.add('$kind catalog hash mismatch');
      }
      final entries =
          _object(jsonDecode(utf8.decode(bytes)))['entries'] as List;
      final entryIds = <String>{};
      final topics = <String>{};
      topicSets[kind] = topics;
      for (final value in entries) {
        final entry = _object(value);
        if (entry['type'] != 'go' &&
            entry['language'] != 'go' &&
            !(entry['id'] as String? ?? '').startsWith('go-')) {
          continue;
        }
        final entryId = entry['id'] as String;
        if (entry['type'] != 'go' || entry['language'] != 'go') {
          issues.add('$entryId: language/type must both be go');
        }
        if (!entryIds.add(entryId)) issues.add('duplicate $kind id $entryId');
        final match = RegExp('^go-$kind-(\\d+)\$').firstMatch(entryId);
        if (match == null) {
          issues.add('unmapped topic $entryId');
        } else {
          expectedTopics.add('T${match[1]!.padLeft(3, '0')}');
          topics.add('T${match[1]!.padLeft(3, '0')}');
        }
        final blocks = kind == 'tutorial' ? entry['lessons'] as List : [entry];
        if (blocks.isEmpty) issues.add('$entryId has no code blocks');
        for (final blockValue in blocks) {
          final block = _object(blockValue);
          final id = kind == 'tutorial'
              ? '$kind/$entryId/${block['id']}'
              : '$kind/$entryId';
          if (expectedBlocks.containsKey(id)) issues.add('duplicate block $id');
          final code = block['code'] as String? ?? '';
          if (code.trim().isEmpty) issues.add('$id empty displayed code');
          expectedBlocks[id] = code;
          expectedEntryFiles[id] =
              'src/${CodeImportService.suggestedFileName('go', code: code)}';
          expectedOutput[id] =
              block[kind == 'tutorial' ? 'output' : 'expectedOutput']
                  as String? ??
              '';
          expectedFixtures[id] = _object(
            block['inputFixtures'] ?? <String, dynamic>{},
          );
        }
      }
      if (entryIds.isEmpty) issues.add('$kind contains no Go entries');
      if (entryIds.length != _object(catalogs[kind])['goEntries']) {
        issues.add('$kind catalog count mismatch');
      }
    }
    final caseIds = <String>{};
    final rawIds = <String>{};
    final canonicalTopics = <String>{};
    final expectedSupportTests = <String>{};
    final actualSupportTests = <String>{};
    for (final item in cases) {
      if (!caseIds.add(item.id)) issues.add('duplicate case ${item.id}');
      if (item.shape == 'displayed-import') {
        rawIds.add(item.id);
        final code = expectedBlocks[item.id];
        final files = item.files;
        final source = files
            .where((file) => file['path'] == item.entryFile)
            .toList();
        if (code == null ||
            source.length != 1 ||
            item.entryFile != expectedEntryFiles[item.id] ||
            base64Encode(utf8.encode(code)) != source.first['contentBase64'] ||
            catalogAuditSha256(utf8.encode(code)) !=
                item.data['contentSha256']) {
          issues.add('${item.id} does not match its displayed code bytes');
        }
        final fixtures = expectedFixtures[item.id] ?? <String, dynamic>{};
        final wantedFiles = {
          item.entryFile,
          for (final name in fixtures.keys)
            name == 'stdin' ? 'input.txt' : name,
        };
        if (!_sameSet(
              files.map((file) => file['path'] as String).toSet(),
              wantedFiles,
            ) ||
            files.length != wantedFiles.length) {
          issues.add('${item.id} imported fixture coverage mismatch');
        }
        for (final fixture in fixtures.entries) {
          final name = fixture.key == 'stdin' ? 'input.txt' : fixture.key;
          final candidates = files
              .where((file) => file['path'] == name)
              .toList();
          if (candidates.length != 1 ||
              candidates.single['contentBase64'] !=
                  base64Encode(utf8.encode(fixture.value as String))) {
            issues.add('${item.id} imported fixture bytes mismatch: $name');
          }
        }
        if (_object(item.data['verification'])['expected'] !=
            expectedOutput[item.id]) {
          issues.add('${item.id} does not match its displayed expectation');
        }
      } else if (item.shape == 'canonical-sample') {
        if (!canonicalTopics.add(item.topic)) {
          issues.add('duplicate canonical topic ${item.topic}');
        }
        if (item.operation != 'test' &&
            item.files.any(
              (file) => (file['path'] as String).endsWith('_test.go'),
            )) {
          expectedSupportTests.add(item.topic);
        }
      } else if (item.shape == 'canonical-support-test') {
        if (!actualSupportTests.add(item.topic) || item.operation != 'test') {
          issues.add('invalid/duplicate support-test topic ${item.topic}');
        }
      } else {
        issues.add('${item.id}: unknown imported shape ${item.shape}');
      }
    }
    if (!_sameSet(rawIds, expectedBlocks.keys.toSet())) {
      issues.add('displayed code coverage mismatch');
    }
    if (!_sameSet(canonicalTopics, expectedTopics)) {
      issues.add('canonical sample coverage mismatch');
    }
    if (!_sameSet(topicSets['tutorial']!, canonicalTopics) ||
        !_sameSet(topicSets['example']!, canonicalTopics)) {
      issues.add('every canonical topic requires both tutorial and example');
    }
    if (!_sameSet(actualSupportTests, expectedSupportTests)) {
      issues.add('canonical support-test coverage mismatch');
    }
    if (cases.isEmpty) issues.add('empty audit inventory');
    return issues;
  }

  List<String> validateResults(List<Map<String, Object?>> records) {
    final ids = records.map((r) => r['id'] as String).toList();
    return [
      if (ids.length != ids.toSet().length) 'duplicate result ids',
      if (!_sameSet(ids.toSet(), cases.map((c) => c.id).toSet()))
        'execution result coverage mismatch',
    ];
  }
}

bool _sameSet(Set<String> a, Set<String> b) =>
    a.length == b.length && a.containsAll(b);

/// An observation deadline cannot release a live native invocation. Keep the
/// original result future, cancel once, and drain it before another test starts.
/// The bridge does not expose its native numeric run ID; the Dart future hash
/// below is diagnostic identity only, never a native process/run handle.
Future<CatalogAuditExecution> observeCatalogNativeExecution({
  required native.NativeGoExecution execution,
  required String caseId,
  required String projectPath,
  required void Function(Map<String, Object?> observation) publishOwnership,
  Duration executionObservation = const Duration(seconds: 20),
  Duration cleanupObservation = const Duration(seconds: 5),
}) async {
  final completion = execution.result;
  final ownership = <String, Object?>{
    'caseId': caseId,
    'fixturePath': projectPath,
    'nativeRunId': null,
    'nativeRunIdUnavailableReason': 'NativeGoExecution does not expose its native run ID',
    'dartResultFutureIdentity': identityHashCode(completion),
    'dartIdentityIsNativeHandle': false,
    'cancelRequests': 0,
    'terminalObserved': false,
    'releaseConfirmed': false,
  };
  void publish(String status) {
    ownership['status'] = status;
    publishOwnership(Map<String, Object?>.unmodifiable(ownership));
  }
  CatalogAuditExecution terminal(native.NativeGoResult result, bool timedOut) {
    ownership.addAll({
      'terminalObserved': true,
      'releaseConfirmed': true,
      'nativeExitCode': result.exitCode,
      'executionObservationTimedOut': timedOut,
    });
    publish(timedOut ? 'drained-after-timeout' : 'terminal');
    return CatalogAuditExecution(
      stdout: result.stdout,
      stderr: result.stderr,
      exitCode: timedOut ? 124 : result.exitCode,
      timedOut: timedOut,
      testExecution: result.testExecution?.toJson(),
      nativeOwnership: Map<String, Object?>.unmodifiable(ownership),
    );
  }
  publish('running');
  try {
    return terminal(await completion.timeout(executionObservation), false);
  } on TimeoutException {
    ownership['cancelRequests'] = 1;
    publish('cancel-requested');
    try {
      await execution.cancel();
    } catch (error) {
      // A failed cancellation dispatch does not release the original result.
      ownership['cancelError'] = '$error';
    }
    try {
      return terminal(await completion.timeout(cleanupObservation), true);
    } on TimeoutException {
      publish('HOLD-native-result-pending');
      // Preserve this exact future after the observation deadline. In
      // particular, do not return to the test runner: a separately registered
      // IDE test must not acquire another native session while this one lives.
      return terminal(await completion, true);
    }
  }
}

Future<CatalogAuditExecution> _runNative(
  Directory project,
  CatalogAuditCase item,
  IntegrationTestWidgetsFlutterBinding binding,
) => observeCatalogNativeExecution(
  execution: native.startNativeGo(
    projectPath: project.path,
    entryFile: p.joinAll([project.path, ...item.entryFile.split('/')]),
  ),
  caseId: item.id,
  projectPath: project.path,
  publishOwnership: (ownership) {
    binding.reportData = {
      ...?binding.reportData,
      'goCatalogNativeOwnership': ownership,
    };
    // ignore: avoid_print
    print('QFLI_GO_CATALOG_NATIVE_OWNERSHIP ${jsonEncode(ownership)}');
  },
);

Future<Map<String, Object?>> _loadedRuntime() async {
  // The maps entry identifies the library actually loaded in this process.
  // A build-time supplied hash alone cannot establish this identity.
  final mappings = await File('/proc/self/maps').readAsLines();
  final candidates = mappings
      .where((line) => line.contains('libqfli_go_runtime.so'))
      .map((line) => line.substring(line.indexOf('/')).trim())
      .toSet();
  if (candidates.length != 1) {
    throw StateError(
      'cannot identify exactly one loaded Go runtime: $candidates',
    );
  }
  final path = candidates.single;
  return {
    'path': path,
    'sha256': catalogAuditSha256(await File(path).readAsBytes()),
  };
}

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  Completer<void>? catalogOwnershipReleased;
  const manifestAsset = String.fromEnvironment(
    'QFLI_GO_AUDIT_MANIFEST_ASSET',
    defaultValue: 'assets/curriculum/audit-manifest.json',
  );
  const tutorialAsset = String.fromEnvironment(
    'QFLI_GO_AUDIT_TUTORIAL_ASSET',
    defaultValue: 'assets/curriculum/tutorials.json',
  );
  const exampleAsset = String.fromEnvironment(
    'QFLI_GO_AUDIT_EXAMPLE_ASSET',
    defaultValue: 'assets/curriculum/examples.json',
  );

  testWidgets(
    'every packaged Go catalog case runs through FFI',
    (_) async {
      final released = Completer<void>();
      catalogOwnershipReleased = released;
      try {
      expect(
        goRuntimeBackendFor(Platform.operatingSystem),
        GoRuntimeBackend.embeddedInterpreter,
        reason: 'device evidence requires Android/OHOS/iOS, not a host SDK',
      );
      Future<List<int>> bytes(String asset) async =>
          (await rootBundle.load(asset)).buffer.asUint8List();
      final manifestBytes = await bytes(manifestAsset);
      final manifest = CatalogAuditManifest.fromJson(
        _object(jsonDecode(utf8.decode(manifestBytes))),
      );
      final inventoryIssues = manifest.validateCatalogs(
        tutorials: await bytes(tutorialAsset),
        examples: await bytes(exampleAsset),
      );
      final records = <Map<String, Object?>>[];
      final originalCwd = Directory.current;
      var priorInvocationStuck = false;
      for (final item in manifest.cases) {
        final project = await Directory.systemTemp.createTemp(
          'qfli_go_catalog_',
        );
        final started = Stopwatch()..start();
        final environmentFailures = <String>[];
        late CatalogAuditExecution result;
        try {
          if (priorInvocationStuck) {
            throw StateError(
              'not executed: preceding native call did not stop',
            );
          }
          await item.materialize(project);
          result = await _runNative(project, item, binding);
        } on TimeoutException catch (error) {
          priorInvocationStuck = true;
          result = CatalogAuditExecution(
            stdout: '',
            stderr: error.toString(),
            exitCode: 124,
            timedOut: true,
          );
        } catch (error) {
          result = CatalogAuditExecution(
            stdout: '',
            stderr: 'harness error: $error',
            exitCode: 125,
          );
        } finally {
          try {
            final currentCwd = Directory.current.path;
            if (currentCwd != originalCwd.path) {
              environmentFailures.add(
                'host cwd changed: before=${originalCwd.path} '
                'after=$currentCwd',
              );
            }
          } catch (error) {
            environmentFailures.add('host cwd unavailable: $error');
          }
          // A still-running native call may retain a fixture file. Keep it for
          // diagnosis, as with a changed cwd that may now point at the fixture.
          if (!priorInvocationStuck && environmentFailures.isEmpty) {
            await project.delete(recursive: true);
          }
        }
        final failures = [...item.check(result), ...environmentFailures];
        records.add({
          'id': item.id,
          'topic': item.topic,
          'shape': item.shape,
          'operation': item.operation,
          'workingDirectory': item.data['workingDirectory'],
          'contentSha256': item.data['contentSha256'],
          'projectSha256': item.data['projectSha256'],
          'verification': item.data['verification'],
          'expectedExitCode': item.data['expectedExitCode'],
          'expectedStderr': item.data['expectedStderr'],
          ...result.toJson(),
          'durationMs': started.elapsedMilliseconds,
          'passed': failures.isEmpty,
          'assertionErrors': failures,
        });
      }
      final coverageIssues = manifest.validateResults(records);
      Map<String, Object?>? runtime;
      try {
        runtime = await _loadedRuntime();
      } catch (error) {
        inventoryIssues.add('loaded runtime identity unavailable: $error');
      }
      final failed = records.where((r) => r['passed'] != true).length;
      final report = <String, Object?>{
        'schemaVersion': 1,
        'evidenceLevel': 'packaged-ffi-device',
        'deviceExecution': true,
        'operatingSystem': Platform.operatingSystem,
        'operatingSystemVersion': Platform.operatingSystemVersion,
        'runtime': runtime,
        'manifestSha256': catalogAuditSha256(manifestBytes),
        'inventorySha256': manifest.data['inventorySha256'],
        'catalogs': manifest.data['catalogs'],
        'inventoryIssues': inventoryIssues,
        'coverageIssues': coverageIssues,
        'total': records.length,
        'passed': records.length - failed,
        'failed': failed,
        'exhaustive': true,
        'success':
            failed == 0 && inventoryIssues.isEmpty && coverageIssues.isEmpty,
        'records': records,
      };
      final reportFile = File(
        p.join(Directory.systemTemp.path, 'qfli-go-catalog-device.json'),
      );
      await reportFile.writeAsString(jsonEncode(report), flush: true);
      binding.reportData = {
        ...?binding.reportData,
        'goCatalogAudit': report,
        'reportPath': reportFile.path,
      };
      // Driver reportData and this prefix both preserve all failure records.
      // ignore: avoid_print
      print('QFLI_GO_CATALOG_AUDIT ${jsonEncode(report)}');
      expect(report['success'], isTrue, reason: 'report: ${reportFile.path}');
      } finally {
        // This finally belongs to the actual asynchronous body, not the
        // framework's observation timeout. _runNative drains its owned result.
        released.complete();
      }
    },
    timeout: const Timeout(Duration(hours: 3)),
  );

  test(
    'OHOS Go native host refuses agreement and external URL dispatch',
    () async {
      const channel = MethodChannel('qflistudio/platform');
      final records = <Map<String, String>>[];
      for (final method in ['openAgreement', 'openUrl']) {
        for (final url in [
          'https://example.invalid/agreement',
          'http://example.invalid/',
          'http://127.0.0.1:65534/',
          'file:///data/storage/el2/base/example.html',
          'custom://external-ability',
        ]) {
          try {
            await channel.invokeMethod<void>(method, {
              'url': url,
              'title': 'offline host audit',
            });
            fail('$method unexpectedly dispatched $url');
          } on PlatformException catch (error) {
            expect(error.code, 'OFFLINE_ONLY', reason: '$method $url');
            records.add({'method': method, 'url': url, 'code': error.code});
          }
        }
      }
      await channel.invokeMethod<void>('startupProgress', {'progress': 0.5});
      final report = <String, Object?>{
        'deviceExecution': true,
        'operatingSystem': Platform.operatingSystem,
        'rejectedDispatches': records,
        'startupProgressPreserved': true,
        'success': records.length == 10,
      };
      binding.reportData = {
        ...?binding.reportData,
        'goOfflineHostAudit': report,
      };
      // ignore: avoid_print
      print('QFLI_GO_OFFLINE_HOST_AUDIT ${jsonEncode(report)}');
    },
    skip: Platform.operatingSystem != 'ohos',
  );

  final waitForApi = registerGoNativeIdeAcceptance(
    binding: binding,
    requireEmbeddedRuntime: true,
    runtimeIdentity: _loadedRuntime,
    beforeAudit: () async {
      final released = catalogOwnershipReleased;
      if (released != null) await released.future;
    },
  );
  registerGoProductUiAcceptance(
    binding: binding,
    requireEmbeddedRuntime: true,
    runtimeIdentity: _loadedRuntime,
    beforeAudit: waitForApi,
  );
}
