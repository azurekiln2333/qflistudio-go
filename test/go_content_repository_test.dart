import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_go/go_content_repository.dart';
import 'package:qfli_studio_core/content/content_repository.dart';

class _Bundle extends CachingAssetBundle {
  _Bundle(this.assets);
  final Map<String, String> assets;
  final List<String> requested = [];

  @override
  Future<ByteData> load(String key) async {
    requested.add(key);
    final value = assets[key];
    if (value == null) throw StateError('Missing product asset: $key');
    return ByteData.sublistView(Uint8List.fromList(utf8.encode(value)));
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Map<String, Object?> entry(String id, {String language = 'go'}) => {
    'id': id,
    'language': language,
    'type': language,
    'locale': 'zh-CN',
    'level': 'beginner',
    'title': 'Fixture import',
    'summary': 'Preserve source and companion files',
    'concepts': ['modules'],
    'source': 'https://go.dev/doc/',
    'license': 'CC BY 4.0',
    'updatedAt': '2026-10-22',
  };

  _Bundle bundle({String language = 'go'}) => _Bundle({
    GoContentRepository.tutorialAsset: jsonEncode({
      'schemaVersion': 1,
      'entries': [
        {
          ...entry('go-tutorial-001', language: language),
          'lessons': [
            {
              'id': 'lesson',
              'title': 'Lesson',
              'code': 'package main\r\nfunc main() {}\r\n',
              'output': 'ok',
              'inputFixtures': {'src/helper.go': 'package main\n'},
            },
          ],
        },
      ],
    }),
    GoContentRepository.exampleAsset: jsonEncode({
      'schemaVersion': 1,
      'entries': [
        {
          ...entry('go-example-001', language: language),
          'code': 'package main\r\nfunc main() {}\r\n',
          'expectedOutput': 'ok',
          'templateType': 'go',
          'inputFixtures': {'src/helper.go': 'package main\n'},
        },
      ],
    }),
  });

  test(
    'loads only product assets once and preserves fixtures and filters',
    () async {
      final assets = bundle();
      final repository = GoContentRepository(bundle: assets);
      final catalog = await repository.load();
      expect(identical(await repository.load(), catalog), isTrue);
      expect(catalog.tutorials.single.lessons.single.code, contains('\r\n'));
      expect(catalog.tutorials.single.lessons.single.inputFixtures, {
        'src/helper.go': 'package main\n',
      });
      expect(catalog.examples.single.inputFixtures, {
        'src/helper.go': 'package main\n',
      });
      expect(
        await repository.examples(filter: const ContentFilter(type: 'c')),
        isEmpty,
      );
      expect(
        await repository.tutorials(filter: const ContentFilter(language: 'go')),
        hasLength(1),
      );
      expect(assets.requested, [
        GoContentRepository.tutorialAsset,
        GoContentRepository.exampleAsset,
      ]);
    },
  );

  test('foreign entries and missing product assets fail visibly', () async {
    await expectLater(
      GoContentRepository(bundle: bundle(language: 'python')).load(),
      throwsA(isA<ContentFormatException>()),
    );
    final missing = _Bundle({});
    await expectLater(
      GoContentRepository(bundle: missing).load(),
      throwsStateError,
    );
    expect(
      missing.requested.every((key) => key.startsWith('assets/curriculum/')),
      isTrue,
    );
  });
}
