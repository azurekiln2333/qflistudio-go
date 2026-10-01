import 'package:flutter_test/flutter_test.dart';
import 'package:qfli_go/go_platform.dart';

void main() {
  test('mobile platforms use the bundled interpreter', () {
    for (final platform in ['android', 'ohos', 'ios']) {
      final backend = goRuntimeBackendFor(platform);
      expect(backend, GoRuntimeBackend.embeddedInterpreter, reason: platform);
      expect(backend.kind, 'embedded-go-runtime');
      expect(backend.status, 'available');
    }
  });

  test(
    'desktop platforms retain the official SDK backend and prerequisite',
    () {
      for (final platform in ['windows', 'linux', 'macos']) {
        final backend = goRuntimeBackendFor(platform);
        expect(backend, GoRuntimeBackend.officialSdk, reason: platform);
        expect(backend.kind, 'official-go-sdk');
        expect(backend.status, 'requires-sdk');
      }
    },
  );

  test('unknown platforms do not advertise a local Go runtime', () {
    for (final platform in ['web', 'fuchsia', 'unknown']) {
      final backend = goRuntimeBackendFor(platform);
      expect(backend, GoRuntimeBackend.unavailable, reason: platform);
      expect(backend.status, 'unavailable');
    }
  });
}
