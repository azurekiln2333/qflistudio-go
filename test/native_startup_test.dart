import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_go/main.dart' as app;
import 'package:qfli_studio_core/app.dart';
import 'package:qfli_studio_core/pages/home_page.dart';
import 'package:qfli_studio_core/services/app_paths.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/splash_screen.dart';

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const pathProvider = MethodChannel('plugins.flutter.io/path_provider');
  const platform = MethodChannel('qflistudio/platform');
  late Directory storage;
  late StudioProfile? previousProfile;
  late List<double> progress;
  Completer<String>? storageLookup;
  var rejectProgress = false;

  setUpAll(() {
    storage = Directory.systemTemp.createTempSync('qfli_startup_test_');
    storageLookup = Completer<String>();
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      pathProvider,
      (call) async =>
          storageLookup == null ? storage.path : await storageLookup!.future,
    );
    binding.defaultBinaryMessenger.setMockMethodCallHandler(platform, (
      call,
    ) async {
      if (call.method == 'startupProgress') {
        progress.add(((call.arguments as Map)['progress'] as num).toDouble());
        if (rejectProgress) {
          throw PlatformException(code: 'UNAVAILABLE');
        }
      }
      return null;
    });
    // AppPaths caches this future; create it outside the individual fake clocks.
    unawaited(AppPaths.storageDirectory());
  });

  setUp(() {
    previousProfile = StudioProfile.current;
    progress = [];
    rejectProgress = false;
  });

  tearDown(() {
    debugDefaultTargetPlatformOverride = null;
    StudioProfile.current = previousProfile;
  });

  tearDownAll(() {
    binding.defaultBinaryMessenger.setMockMethodCallHandler(pathProvider, null);
    binding.defaultBinaryMessenger.setMockMethodCallHandler(platform, null);
    storage.deleteSync(recursive: true);
  });

  testWidgets(
    'OHOS waits for initialization and home layout before its first frame',
    (tester) async {
      await app.main();
      expect(binding.sendFramesToEngine, isFalse);
      await tester.pump();
      expect(find.byType(SplashScreen), findsOneWidget);
      await tester.pump(const Duration(milliseconds: 160));

      // Even after the minimum display time, slow storage must keep the native
      // loading layer visible rather than submit the Flutter fallback screen.
      await tester.pump(const Duration(seconds: 2));
      expect(binding.sendFramesToEngine, isFalse);
      expect(progress, isEmpty);
      expect(find.byType(HomePage), findsNothing);

      storageLookup!.complete(storage.path);
      await _waitForReady(tester);
      await tester.pump(const Duration(milliseconds: 320));
      await tester.pump();

      expect(progress, [1 / 3, 2 / 3, 1]);
      expect(binding.sendFramesToEngine, isTrue);
      expect(find.byType(HomePage), findsOneWidget);
      expect(find.byType(SplashScreen), findsNothing);
      expect(tester.takeException(), isNull);
      await _unmount(tester);
    },
    variant: TargetPlatformVariant({TargetPlatform.ohos}),
  );

  testWidgets(
    'other platforms submit the Flutter fallback without native delay',
    (tester) async {
      await app.main();
      expect(binding.sendFramesToEngine, isTrue);
      await tester.pump();
      expect(find.byType(SplashScreen), findsOneWidget);
      await _waitForReady(tester);
      await tester.pump();

      expect(progress, isEmpty);
      expect(find.byType(HomePage), findsOneWidget);
      expect(tester.takeException(), isNull);
      await _unmount(tester);
    },
    variant: TargetPlatformVariant({TargetPlatform.android}),
  );

  testWidgets(
    'a failing progress bridge cannot keep the OHOS first frame deferred',
    (tester) async {
      rejectProgress = true;

      await app.main();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 160));
      await _waitForReady(tester);
      await tester.pump(const Duration(seconds: 2));
      await tester.pump();

      expect(progress, [1 / 3, 2 / 3, 1]);
      expect(binding.sendFramesToEngine, isTrue);
      expect(find.byType(HomePage), findsOneWidget);
      expect(tester.takeException(), isNull);
      await _unmount(tester);
    },
    variant: TargetPlatformVariant({TargetPlatform.ohos}),
  );
}

Future<void> _waitForReady(WidgetTester tester) async {
  for (var attempt = 0; attempt < 100; attempt++) {
    if (tester.widget<QfliApp>(find.byType(QfliApp)).ready!.value) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
    await tester.pump();
  }
  fail('Local initialization did not complete');
}

Future<void> _unmount(WidgetTester tester) async {
  final application = tester.widget<QfliApp>(find.byType(QfliApp));
  await tester.pumpWidget(const SizedBox.shrink());
  application.store.dispose();
  application.auth.dispose();
  application.settings!.dispose();
  (application.ready! as ValueNotifier<bool>).dispose();
}
