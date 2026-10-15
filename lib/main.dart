import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:qfli_studio_core/app.dart';
import 'package:qfli_studio_core/services/project_templates.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/splash_screen.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';

import 'go_platform.dart';
import 'go_runner.dart';
import 'go_terminal_delegate.dart';

/// 本 App 的产品名。窗口标题、任务切换器和应用内顶栏都读它。
const String _appTitle = StudioProductCatalog.goShift;

/// Go 版档位：同一套内核 UI，收窄成只服务 Go。
///
/// 单独提出来是为了让测试能直接断言档位，而不必为了一个常量去跑 `main()`。
final StudioProfile goProfile = StudioProfile(
  id: 'go',
  appTitle: _appTitle,
  templates: [ProjectTemplate.empty, ProjectTemplate.go],
  isOffline: true,
  runner: GoProgramRunner(),
  productKey: StudioProductCatalog.goShiftKey,
  showHomeTabs: false,
  runtimeKind: goRuntimeBackendFor(
    kIsWeb ? 'web' : Platform.operatingSystem,
  ).kind,
  runtimeStatus: goRuntimeBackendFor(
    kIsWeb ? 'web' : Platform.operatingSystem,
  ).status,
  supportedFileExtensions: ['.go'],
  // main.go 排在默认入口表前面，保证本版一定先命中它。
  entryFileNames: ['main.go', 'src/main.go'],
  // 终端命令挂钩：让内置终端能跑 go run/build/test/fmt/vet/mod 等命令，
  // 复用运行按钮同一条工具链（桌面真实 SDK，移动端只承诺解释器支持的能力）。
  terminalCommandDelegate: goTerminalCommandDelegate,
);

Future<void> main() async {
  final binding = WidgetsFlutterBinding.ensureInitialized();
  final nativeStartup = !kIsWeb && defaultTargetPlatform == TargetPlatform.ohos;
  if (nativeStartup) binding.deferFirstFrame();

  // 在 runApp 之前定档。
  StudioProfile.current = goProfile;
  final store = ProjectStore();
  final auth = AuthStore();
  final settings = SettingsStore();
  final ready = ValueNotifier<bool>(false);
  runApp(QfliApp(store: store, auth: auth, settings: settings, ready: ready));

  const platformChannel = MethodChannel('qflistudio/platform');
  Future<void> reportProgress(double progress) async {
    try {
      await platformChannel.invokeMethod<void>('startupProgress', {
        'progress': progress,
      });
    } on PlatformException catch (error) {
      debugPrint('Startup progress unavailable: ${error.code}');
    } on MissingPluginException {
      // Native startup progress is optional for other entry shells.
    }
  }

  Future<void> completeStartup() async {
    try {
      final minimumDisplay = nativeStartup
          ? Future<void>.delayed(const Duration(milliseconds: 1100))
          : Future<void>.value();
      if (nativeStartup) {
        await Future<void>.delayed(const Duration(milliseconds: 160));
      }
      await AppBootstrap.run(
        store: store,
        auth: auth,
        settings: settings,
        ready: ready,
        onProgress: nativeStartup
            ? (progress) => unawaited(reportProgress(progress))
            : null,
      );
      await Future.wait([
        minimumDisplay,
        if (nativeStartup)
          Future<void>.delayed(const Duration(milliseconds: 320)),
      ]);
      // 原生遮罩持续显示，直到主页完成构建、布局并提交首帧。
      if (nativeStartup) await binding.endOfFrame;
    } finally {
      if (nativeStartup) binding.allowFirstFrame();
    }
  }

  binding.addPostFrameCallback((_) {
    unawaited(completeStartup());
  });
}
