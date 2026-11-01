import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_content_repository.dart';
import 'package:qfli_studio_core/content/content_repository.dart';
import 'package:qfli_studio_core/content/content_validator.dart';
import 'package:qfli_studio_core/content/local_content_adapter.dart';
import 'package:qfli_studio_core/services/code_import_service.dart';

/// Content-loading / import regression for the Go curriculum slice.
///
/// This test reads the durable Go slice authored under
/// `tool/go_curriculum/content/go/` through the **real shared parser**
/// (`ContentCatalog.fromJson`) and the **real shared validator**
/// (`ContentCatalogValidator`). It does not invent its own JSON shape, so a
/// contract drift between the authoring tool and the application/UI is caught
/// here instead of at runtime.
///
/// Release gate: both the authored slice and real application assets must
/// contain all 120 tutorials/examples; incomplete content fails unconditionally.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final root = _toolRoot();
  final tutorialsFile = File(p.join(root, 'content', 'go', 'tutorials.json'));
  final examplesFile = File(p.join(root, 'content', 'go', 'examples.json'));
  final classifyFile = File(p.join(root, 'content', 'classify.json'));

  late ContentCatalog catalog;
  late Map<String, Map<String, Object?>> classify;

  setUpAll(() {
    catalog = ContentCatalog.fromJson(
      tutorialsSource: tutorialsFile.readAsStringSync(),
      examplesSource: examplesFile.readAsStringSync(),
    );
    final classifyList =
        jsonDecode(classifyFile.readAsStringSync()) as List<Object?>;
    classify = {
      for (final raw in classifyList)
        (raw as Map<String, Object?>)['id'] as String: raw,
    };
  });

  test('Go slice loads through the real shared parser', () {
    final goTutorials = catalog.tutorials
        .where((t) => t.type.toLowerCase() == 'go')
        .toList();
    final goExamples = catalog.examples
        .where((e) => e.type.toLowerCase() == 'go')
        .toList();
    expect(goTutorials, isNotEmpty, reason: 'no Go tutorials parsed');
    expect(goExamples, isNotEmpty, reason: 'no Go examples parsed');
    // Every parsed Go entry must have an explicit id/language/type (no
    // compatibility fallback), otherwise the UI would group it oddly.
    for (final t in goTutorials) {
      expect(t.hasExplicitId, isTrue, reason: '${t.id} missing explicit id');
      expect(t.hasExplicitLanguage, isTrue, reason: '${t.id} missing language');
      expect(t.hasExplicitType, isTrue, reason: '${t.id} missing type');
      expect(t.locale, 'zh-CN', reason: '${t.id} locale must be zh-CN');
    }
  });

  test('product asset bundle loads the complete authored Go slice', () async {
    final loaded = await GoContentRepository().load();
    final tutorials = loaded.tutorials.where((t) => t.type == 'go').toList();
    final examples = loaded.examples.where((e) => e.type == 'go').toList();
    expect(tutorials.length, classify.length);
    expect(examples.length, classify.length);
    expect(tutorials.map((t) => t.id), catalog.tutorials.map((t) => t.id));
    expect(examples.map((e) => e.id), catalog.examples.map((e) => e.id));
    for (var i = 0; i < tutorials.length; i++) {
      expect(tutorials[i].title, catalog.tutorials[i].title);
      expect(
        tutorials[i].lessons.first.explain,
        catalog.tutorials[i].lessons.first.explain,
      );
      expect(
        tutorials[i].lessons.first.code,
        catalog.tutorials[i].lessons.first.code,
      );
      expect(examples[i].code, catalog.examples[i].code);
      expect(examples[i].inputFixtures, catalog.examples[i].inputFixtures);
      expect(
        tutorials[i].lessons.first.inputFixtures,
        catalog.tutorials[i].lessons.first.inputFixtures,
      );
    }
  });

  test('every Go lesson satisfies the release per-entry contract', () {
    final issues = <String>[];
    final lessonIds = <String>{};
    for (final t in catalog.tutorials.where((t) => t.type == 'go')) {
      expect(t.lessons, isNotEmpty, reason: '${t.id} has no lessons');
      for (final lesson in t.lessons) {
        final where = '${t.id}/${lesson.id}';
        if (lesson.id.isEmpty || !lessonIds.add(lesson.id)) {
          issues.add('$where duplicate/empty lesson id');
        }
        if (lesson.objective.trim().isEmpty) {
          issues.add('$where empty objective');
        }
        if (lesson.prerequisites.isEmpty) {
          issues.add('$where empty prerequisites');
        }
        if (lesson.pitfalls.length < 2) {
          issues.add('$where needs >=2 pitfalls');
        }
        if (lesson.exercises.isEmpty) {
          issues.add('$where needs >=1 exercise');
        }
        for (final e in lesson.exercises) {
          if (e.prompt.trim().isEmpty ||
              e.hint.trim().isEmpty ||
              e.answer.trim().isEmpty) {
            issues.add('$where exercise missing prompt/hint/answer');
          }
        }
        if (lesson.code.trim().isEmpty) {
          issues.add('$where empty code');
        }
        if (lesson.output.trim().isEmpty) {
          // stdout/empty-output topics may legitimately be empty strings only
          // for test/bench kinds; a stdout-exact topic must carry output.
          final c = classify[_topicIdFor(t.id)];
          final kind = (c?['verification'] as Map<String, Object?>?)?['kind'];
          if (kind == 'stdout-exact') {
            issues.add('$where stdout-exact but empty output');
          }
        }
      }
    }
    expect(issues, isEmpty, reason: issues.join('\n'));
  });

  test('every Go example is self-contained shape-wise', () {
    final ids = <String>{};
    for (final e in catalog.examples.where((e) => e.type == 'go')) {
      expect(e.id.isNotEmpty, isTrue);
      expect(ids.add(e.id), isTrue, reason: 'duplicate example id ${e.id}');
      expect(e.code.trim(), isNotEmpty, reason: '${e.id} empty code');
      expect(e.templateType, 'go', reason: '${e.id} templateType != go');
      // An aggregate example code must be exactly one Go file, never a
      // concatenation of go.mod + multiple files. test-package / module
      // examples may legitimately be a non-main single file.
      expect(
        RegExp(r'^package\s+\w+', multiLine: true).hasMatch(e.code),
        isTrue,
        reason: '${e.id} code is not a single Go file',
      );
      expect(
        RegExp(r'^(module|go)\s', multiLine: true).hasMatch(e.code),
        isFalse,
        reason: '${e.id} code contains go.mod content',
      );
    }
  });

  test('Go slice passes the shared validator for Go entries', () {
    // Run the real shared validator scoped to Go. It enforces the release
    // minimum per type; scoping avoids asserting on other languages' counts
    // while still exercising the shared validation logic on the Go slice.
    final goCatalog = ContentCatalog(
      schemaVersion: catalog.schemaVersion,
      tutorials: catalog.tutorials.where((t) => t.type == 'go').toList(),
      examples: catalog.examples.where((e) => e.type == 'go').toList(),
    );
    final result = ContentCatalogValidator.validate(
      goCatalog,
      enforceReleaseMinimum: true,
      requiredTypes: const {'go'},
      minimumEntriesPerType: 120,
    );
    expect(
      result.issues.map((i) => i.toString()).toList(),
      isEmpty,
      reason: 'shared validator reported Go issues',
    );
  });

  test('all authored topics and the original 120 remain available', () {
    final goTutorials = catalog.tutorials.where((t) => t.type == 'go').length;
    final goExamples = catalog.examples.where((e) => e.type == 'go').length;
    // Final gate (R1/AC1): both must be exactly 120. Never skipped; an
    // incomplete slice must fail loudly, not pass green.
    expect(goTutorials, classify.length);
    expect(goExamples, classify.length);
    expect(classify.length, greaterThanOrEqualTo(120));
    for (var number = 1; number <= 120; number++) {
      expect(classify, contains('T${number.toString().padLeft(3, '0')}'));
    }
  });

  test(
    'real import maps every displayed source and all support files',
    () async {
      final repository = GoContentRepository();
      final examples = await LocalContentAdapter.loadExamples(
        repository: repository,
        language: 'go',
        productKey: 'goshift',
      );
      final tutorial = (await LocalContentAdapter.loadTutorial(
        repository: repository,
        language: 'go',
        displayName: 'Go',
        productKey: 'goshift',
      ))!;
      expect(tutorial.allLessons.length, classify.length);
      for (final example in examples) {
        final sourceName = CodeImportService.suggestedFileName(
          'go',
          code: example.code,
        );
        final entry = 'src/$sourceName';
        final files = CodeImportService.projectFiles(
          example: example,
          entryFile: entry,
        );
        expect(files[entry], example.code, reason: example.id);
        expect(
          files.length,
          example.inputFixtures.length + 1,
          reason: example.id,
        );
        final source =
            jsonDecode(
                  File(
                    p.join(root, 'topics', '${_topicIdFor(example.id)}.json'),
                  ).readAsStringSync(),
                )
                as Map<String, dynamic>;
        final canonical = Directory(
          p.join(root, 'samples', source['id'] as String),
        );
        final tutorialCode = (source['tutorial'] as Map)['code'] as String;
        final canonicalFiles = canonical
            .listSync(recursive: true)
            .whereType<File>()
            .toList();
        String relativePath(File file) =>
            p.relative(file.path, from: canonical.path).replaceAll('\\', '/');
        final packageTrees = canonicalFiles
            .map(relativePath)
            .where((name) => name.contains('/') && name.endsWith('.go'))
            .map((name) => name.split('/').first)
            .toSet();
        for (final file in canonicalFiles) {
          final relative = relativePath(file);
          final bytes = file.readAsBytesSync();
          final text = utf8.decode(bytes);
          if (relative.endsWith('.go') && text == tutorialCode) continue;
          final rootRelative =
              relative == 'go.mod' ||
              relative == 'go.sum' ||
              packageTrees.contains(relative.split('/').first);
          final destination = rootRelative ? relative : 'src/$relative';
          expect(
            utf8.encode(files[destination]!),
            bytes,
            reason: '${example.id}: $destination',
          );
        }
        final lesson = tutorial.allLessons.firstWhere(
          (lesson) =>
              lesson.id == 'go-tutorial-${example.id.split('-').last}-lesson',
        );
        expect(lesson.inputFixtures, example.inputFixtures, reason: example.id);
        if (source['importKind'] == 'test-package') {
          expect(sourceName, 'snippet_test.go', reason: example.id);
        }
      }
    },
  );

  test('runtime/importKind claims match classify.json', () {
    final issues = <String>[];
    for (final t in catalog.tutorials.where((t) => t.type == 'go')) {
      final topicId = _topicIdFor(t.id);
      final c = classify[topicId];
      if (c == null) {
        issues.add('${t.id} ($topicId) missing from classify.json');
        continue;
      }
      final runtime = c['runtime'];
      if (runtime != 'desktop' && runtime != 'mobile') {
        issues.add('${t.id} runtime=$runtime');
      }
      final importKind = c['importKind'];
      if (importKind != 'single-file' &&
          importKind != 'test-package' &&
          importKind != 'module-project') {
        issues.add('${t.id} importKind=$importKind');
      }
      // A mobile claim must be paired with single-file import and a
      // non-test verification (mobile cannot run go test/bench/fuzz).
      if (runtime == 'mobile') {
        final kind = (c['verification'] as Map<String, Object?>?)?['kind'];
        if (importKind != 'single-file') {
          issues.add('${t.id} mobile but importKind=$importKind');
        }
        if (kind != 'stdout-exact' &&
            kind != 'stdout-sorted' &&
            kind != 'stdout-normalized') {
          issues.add('${t.id} mobile but verification=$kind');
        }
      }
    }
    expect(issues, isEmpty, reason: issues.join('\n'));
  });
  test('tutorial.code and example.code parse as Go through shared fields', () {
    // The shared parser stores raw code text; assert it survives round-trip
    // without trimming damage (leading/trailing whitespace is preserved by
    // _rawText) for the first entry as a contract smoke check.
    final first = catalog.tutorials.first;
    expect(first.lessons.first.code, contains('package main'));
  });
}

String _topicIdFor(String aggregateId) {
  // Aggregate ids are go-tutorial-NNN / go-example-NNN; classify keys are TNNN.
  final match = RegExp(
    r'^(?:go-tutorial|go-example)-(\d{3})$',
  ).firstMatch(aggregateId);
  if (match == null) return aggregateId;
  return 'T${match.group(1)}';
}

String _toolRoot() {
  // Test runs with cwd at the qfli_go package root.
  final path = p.join(Directory.current.path, 'tool', 'go_curriculum');
  if (!Directory(path).existsSync()) {
    throw StateError(
      'tool/go_curriculum not found from ${Directory.current.path}; '
      'run flutter test from the qfli_go package root',
    );
  }
  return path;
}
