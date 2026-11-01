import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_go/native_go_result.dart';

import '../integration_test/go_catalog_test.dart' as audit;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Map<String, dynamic> item(String id, {String shape = 'displayed-import'}) {
    const code = 'package main\nfunc main() {}\n';
    return {
      'id': id,
      'topic': 'T001',
      'shape': shape,
      'operation': 'program',
      'entryFile': 'src/main.go',
      'contentSha256': audit.catalogAuditSha256(utf8.encode(code)),
      'files': [
        {
          'path': 'src/main.go',
          'contentBase64': base64Encode(utf8.encode(code)),
          'sha256': audit.catalogAuditSha256(utf8.encode(code)),
        },
      ],
      'verification': {'kind': 'stdout-exact', 'expected': 'ready'},
      'expectedExitCode': 0,
      'expectedStderr': '',
      'stdin': '',
    };
  }

  test('nonzero, timeout, stderr and wrong output cannot pass', () {
    final sample = audit.CatalogAuditCase.fromJson(item('example/test'));
    expect(
      sample.check(
        const audit.CatalogAuditExecution(
          stdout: 'ready\n',
          stderr: '',
          exitCode: 0,
        ),
      ),
      isEmpty,
    );
    for (final result in [
      const audit.CatalogAuditExecution(
        stdout: 'wrong',
        stderr: '',
        exitCode: 0,
      ),
      const audit.CatalogAuditExecution(
        stdout: 'ready',
        stderr: '',
        exitCode: 1,
      ),
      const audit.CatalogAuditExecution(
        stdout: 'ready',
        stderr: 'panic',
        exitCode: 0,
      ),
      const audit.CatalogAuditExecution(
        stdout: 'ready',
        stderr: '',
        exitCode: 0,
        timedOut: true,
      ),
    ]) {
      expect(sample.check(result), isNotEmpty);
    }
  });

  for (final cancelFails in [false, true]) {
    test('native timeout retains the same result until drained (cancelFails=$cancelFails)', () async {
      final completion = Completer<NativeGoResult>();
      final held = Completer<void>();
      final observations = <Map<String, Object?>>[];
      var cancelCount = 0;
      var nextCaseStarted = false;
      final execution = NativeGoExecution(
        result: completion.future,
        cancel: () async {
          cancelCount++;
          if (cancelFails) throw StateError('cancel transport failed');
        },
      );
      final observed = audit.observeCatalogNativeExecution(
        execution: execution,
        caseId: 'tutorial/T001',
        projectPath: '/owned/catalog-fixture',
        executionObservation: Duration.zero,
        cleanupObservation: Duration.zero,
        publishOwnership: (observation) {
          observations.add(observation);
          if (observation['status'] == 'HOLD-native-result-pending' &&
              !held.isCompleted) {
            held.complete();
          }
        },
      ).then((result) {
        nextCaseStarted = true;
        return result;
      });
      await held.future;
      expect(nextCaseStarted, isFalse);
      expect(cancelCount, 1);
      expect(observations.last['releaseConfirmed'], isFalse);
      expect(observations.last['terminalObserved'], isFalse);
      expect(observations.last['nativeRunId'], isNull);
      expect(observations.last['dartIdentityIsNativeHandle'], isFalse);
      expect(observations.map((value) => value['dartResultFutureIdentity']).toSet(),
          {identityHashCode(completion.future)});
      expect(observations.last.containsKey('cancelError'), cancelFails);

      completion.complete(const NativeGoResult(
        stdout: 'ready\n', stderr: '', exitCode: 0,
      ));
      final result = await observed;
      expect(nextCaseStarted, isTrue);
      expect(cancelCount, 1);
      expect(result.stdout, 'ready\n');
      expect(result.exitCode, 124);
      expect(result.timedOut, isTrue);
      expect(result.nativeOwnership!['nativeExitCode'], 0);
      expect(result.nativeOwnership!['releaseConfirmed'], isTrue);
      expect(observations.last['status'], 'drained-after-timeout');
      expect(audit.CatalogAuditCase.fromJson(item('tutorial/T001')).check(result),
          contains('execution timed out'));
    });
  }

  test('zero exit cannot pretend to execute test functions', () {
    final data = item('canonical/T001');
    data['operation'] = 'test';
    data['verification'] = {'kind': 'test-pass', 'expected': ''};
    expect(
      audit.CatalogAuditCase.fromJson(data).check(
        const audit.CatalogAuditExecution(
          stdout: 'ok package',
          stderr: '',
          exitCode: 0,
        ),
      ),
      contains(contains('execution metadata')),
    );
  });

  test(
    'embedded metadata requires real passed functions and complete counts',
    () {
      final data = item('canonical/T001')
        ..['operation'] = 'test'
        ..['verification'] = {'kind': 'test-pass'}
        ..['expectedTestNames'] = ['TestReady'];
      final sample = audit.CatalogAuditCase.fromJson(data);
      const execution = <String, Object?>{
        'engine': 'qfli-embedded-testing-v1',
        'testsRun': 1,
        'testsPassed': 1,
        'testsFailed': 0,
        'testsSkipped': 0,
        'benchmarksRun': 0,
        'fuzzSeedsRun': 0,
      };
      audit.CatalogAuditExecution result(
        Map<String, Object?> metadata, {
        String stdout = '--- PASS: TestReady\nPASS\n',
      }) => audit.CatalogAuditExecution(
        stdout: stdout,
        stderr: '',
        exitCode: 0,
        testExecution: metadata,
      );
      expect(sample.check(result(execution)), isEmpty);
      for (final change in [
        {'engine': 'fake'},
        {'testsPassed': 0},
        {'testsFailed': 1},
        {'testsRun': -1},
        {'testsRun': 2},
        {'testsSkipped': 1},
        {'testsRun': 1, 'testsPassed': 0, 'testsSkipped': 1},
      ]) {
        expect(sample.check(result({...execution, ...change})), isNotEmpty);
      }
      expect(sample.check(result(execution, stdout: 'PASS\n')), isNotEmpty);
      data['minimumFuzzSeeds'] = 2;
      expect(
        audit.CatalogAuditCase.fromJson(data).check(result(execution)),
        isNotEmpty,
      );
      data.remove('minimumFuzzSeeds');
      data['verification'] = {'kind': 'bench-exists'};
      data['expectedBenchmarkNames'] = ['BenchmarkOne', 'BenchmarkTwo'];
      expect(
        audit.CatalogAuditCase.fromJson(data).check(result(execution)),
        isNotEmpty,
      );
      expect(
        audit.CatalogAuditCase.fromJson(
          data,
        ).check(result({...execution, 'benchmarksRun': 2})),
        isEmpty,
      );
    },
  );

  test('missing and duplicated result records fail coverage', () {
    final manifest = audit.CatalogAuditManifest.fromJson({
      'cases': [item('example/test')],
    });
    expect(manifest.validateResults([]), isNotEmpty);
    expect(
      manifest.validateResults([
        {'id': 'example/test'},
        {'id': 'example/test'},
      ]),
      isNotEmpty,
    );
    expect(
      manifest.validateResults([
        {'id': 'example/test'},
      ]),
      isEmpty,
    );
  });

  test(
    'fixtures preserve bytes and reject hash mismatch and escapes',
    () async {
      final project = await Directory.systemTemp.createTemp('qfli_audit_test_');
      try {
        final data = item('fixture');
        await audit.CatalogAuditCase.fromJson(data).materialize(project);
        expect(
          await File('${project.path}/src/main.go').readAsString(),
          'package main\nfunc main() {}\n',
        );
        final file = (data['files'] as List).first as Map<String, dynamic>;
        file['sha256'] = 'wrong';
        await expectLater(
          audit.CatalogAuditCase.fromJson(data).materialize(project),
          throwsFormatException,
        );
        for (final path in [
          '../outside',
          '/absolute',
          r'C:\outside',
          'a/./b',
          'a//b',
          '.qfli/project.json',
          'CON.go',
          'name. ',
        ]) {
          file['path'] = path;
          await expectLater(
            audit.CatalogAuditCase.fromJson(data).materialize(project),
            throwsFormatException,
          );
        }
      } finally {
        await project.delete(recursive: true);
      }
    },
  );

  test('loaded catalogs independently detect omitted code cases', () {
    const code = 'package main\nfunc main() {}\n';
    final tutorials = utf8.encode(
      jsonEncode({
        'entries': [
          {
            'id': 'go-tutorial-001',
            'type': 'go',
            'language': 'go',
            'lessons': [
              {'id': 'lesson', 'code': code, 'output': 'ready'},
            ],
          },
        ],
      }),
    );
    final examples = utf8.encode(
      jsonEncode({
        'entries': [
          {
            'id': 'go-example-001',
            'type': 'go',
            'language': 'go',
            'code': code,
            'expectedOutput': 'ready',
          },
        ],
      }),
    );
    final data = <String, dynamic>{
      'schemaVersion': 1,
      'inventoryIssues': <String>[],
      'catalogs': {
        'tutorial': {
          'sha256': audit.catalogAuditSha256(tutorials),
          'goEntries': 1,
        },
        'example': {
          'sha256': audit.catalogAuditSha256(examples),
          'goEntries': 1,
        },
      },
      'cases': [
        item('tutorial/go-tutorial-001/lesson'),
        item('example/go-example-001'),
        item('canonical/T001', shape: 'canonical-sample'),
      ],
    };
    List<String> check() => audit.CatalogAuditManifest.fromJson(
      data,
    ).validateCatalogs(tutorials: tutorials, examples: examples);
    expect(check(), isEmpty);
    (data['cases'] as List).removeAt(1);
    expect(check(), contains('displayed code coverage mismatch'));
    (data['cases'] as List).insert(1, item('example/go-example-001'));
    final canonical = (data['cases'] as List).last as Map<String, dynamic>;
    (canonical['files'] as List).add({
      'path': 'helper_test.go',
      'contentBase64': base64Encode(utf8.encode('package main\n')),
      'sha256': audit.catalogAuditSha256(utf8.encode('package main\n')),
    });
    expect(check(), contains('canonical support-test coverage mismatch'));
  });

  test('current generated manifest covers every real catalog code block', () {
    File catalog(String name) {
      final local = File('assets/curriculum/$name.json');
      return local.existsSync()
          ? local
          : File('../qfli_studio_core/assets/content/$name.json');
    }

    final packaged = File('assets/curriculum/audit-manifest.json');
    final manifestFile = packaged.existsSync()
        ? packaged
        : File('tool/go_curriculum/evidence/catalog-audit-manifest.json');
    expect(
      manifestFile.existsSync(),
      isTrue,
      reason: 'generate the manifest with audit_native.py --backend inventory',
    );
    final manifest = audit.CatalogAuditManifest.fromJson(
      Map<String, dynamic>.from(
        jsonDecode(manifestFile.readAsStringSync()) as Map,
      ),
    );
    expect(
      manifest.validateCatalogs(
        tutorials: catalog('tutorials').readAsBytesSync(),
        examples: catalog('examples').readAsBytesSync(),
      ),
      isEmpty,
    );
  });
}
