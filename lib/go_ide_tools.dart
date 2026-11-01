import 'go_code_analyzer.dart';
import 'go_tools.dart';

/// Connects the direct tool cards to the same pure native source services as
/// editor diagnostics. A missing or outdated library remains a visible error.
GoTools createGoIdeTools({GoAnalysisBackend? backend}) {
  final sourceTools = GoSourceTools(backend: backend);
  return GoTools(
    formatter: (source, filePath) async {
      final result = await sourceTools.format(
        source: source,
        filePath: filePath,
      );
      return GoToolSourceResult(
        formattedSource: result.formattedSource,
        errors: [for (final item in result.diagnostics) item.message],
        unavailableReason: result.unavailableReason,
      );
    },
    inspector: (source, filePath) async {
      final result = await sourceTools.inspect(
        source: source,
        filePath: filePath,
      );
      return GoToolSourceResult(
        report: result.report,
        errors: [for (final item in result.diagnostics) item.message],
        unavailableReason: result.unavailableReason,
      );
    },
  );
}
