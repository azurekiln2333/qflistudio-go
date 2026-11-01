import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:qfli_studio_core/content/content_repository.dart';

/// The Go product owns its verified curriculum while sharing the content model.
class GoContentRepository implements ContentRepository {
  GoContentRepository({AssetBundle? bundle}) : _bundle = bundle ?? rootBundle;

  static const tutorialAsset = 'assets/curriculum/tutorials.json';
  static const exampleAsset = 'assets/curriculum/examples.json';

  final AssetBundle _bundle;
  Future<ContentCatalog>? _catalog;

  @override
  Future<ContentCatalog> load() => _catalog ??= _load();

  Future<ContentCatalog> _load() async {
    final sources = await Future.wait([
      _bundle.loadString(tutorialAsset),
      _bundle.loadString(exampleAsset),
    ]);
    return compute(_parseGoCatalog, sources, debugLabel: 'parse-go-curriculum');
  }

  @override
  Future<List<TutorialContent>> tutorials({
    ContentFilter filter = const ContentFilter(),
  }) async => [
    for (final entry in (await load()).tutorials)
      if (filter.matches(entry)) entry,
  ];

  @override
  Future<List<ExampleContent>> examples({
    ContentFilter filter = const ContentFilter(),
  }) async => [
    for (final entry in (await load()).examples)
      if (filter.matches(entry)) entry,
  ];
}

ContentCatalog _parseGoCatalog(List<String> sources) {
  final catalog = ContentCatalog.fromJson(
    tutorialsSource: sources[0],
    examplesSource: sources[1],
  );
  for (final entry in <ContentEntry>[
    ...catalog.tutorials,
    ...catalog.examples,
  ]) {
    if (entry.type != 'go' || entry.language != 'go') {
      throw ContentFormatException(
        'go-curriculum',
        '${entry.id} is not a Go entry',
      );
    }
  }
  return catalog;
}
