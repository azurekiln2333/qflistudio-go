import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/main.dart' show goProfile;
import 'package:qfli_studio_core/community/models.dart';
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/i18n/studio_localizations.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/pages/home_page.dart';
import 'package:qfli_studio_core/pages/profile_page.dart';
import 'package:qfli_studio_core/pages/quick_tools_page.dart';
import 'package:qfli_studio_core/pages/settings_page.dart';
import 'package:qfli_studio_core/services/app_paths.dart';
import 'package:qfli_studio_core/services/project_templates.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_studio_core/theme/app_theme.dart';

/// Offline-entry regressions for the Go product.
///
/// Every assertion runs against the **real** `goProfile` from `lib/main.dart`
/// and the **real** shared widgets (`HomePage`, `FunctionsTab`, `ProfileTab`,
/// `SettingsPage`, `EditorPage`). Only the storage directory is faked, using the
/// same `plugins.flutter.io/path_provider` method-channel mock as
/// `test/native_startup_test.dart`, so this file needs no extra packages.
///
/// These tests pin the product contract: the Go product is offline-only, so no
/// network-dependent entry point may be reachable from it, and no background
/// refresh may fire for a stale but trustworthy token.
void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();

  const pathProvider = MethodChannel('plugins.flutter.io/path_provider');
  late Directory root;
  StudioProfile? originalProfile;

  setUpAll(() {
    root = Directory.systemTemp.createTempSync('qfli_go_offline_');
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      pathProvider,
      (call) async => root.path,
    );
    // AppPaths caches the resolved directory; warm it once outside any fake
    // clock so the stores below can write their registries.
    AppPaths.storageDirectory();
    // Count every HTTP attempt for the whole file so it is active before
    // ApiClient.instance lazily creates its client, regardless of test order.
    HttpOverrides.global = _CountingHttpOverrides();
  });

  setUp(() {
    originalProfile = StudioProfile.current;
    StudioProfile.current = goProfile;
    _CountingHttpOverrides.requests.clear();
  });

  tearDown(() {
    StudioProfile.current = originalProfile;
  });

  tearDownAll(() {
    HttpOverrides.global = null;
    binding.defaultBinaryMessenger.setMockMethodCallHandler(pathProvider, null);
    if (root.existsSync()) root.deleteSync(recursive: true);
  });

  test('the Go profile is offline and offline-only', () {
    expect(goProfile.isOffline, isTrue);
    // offlineOnly is what actually hides the account/Git/cloud routes. The Go
    // product relies on the shared default (offlineOnly ?? isOffline), so this
    // assertion guards the wiring that every other test below depends on.
    expect(goProfile.offlineOnly, isTrue);
    expect(goProfile.productKey, StudioProductCatalog.goShiftKey);
  });

  testWidgets('the home page offers no cloud project scope', (tester) async {
    final fixture = _Fixture.create(root);
    addTearDown(() => fixture.dispose(tester));
    await tester.runAsync(() => fixture.projects.load());
    _sizeTester(tester);
    await tester.pumpWidget(
      _app(
        HomePage(
          store: fixture.projects,
          auth: fixture.auth,
          settings: fixture.settings,
        ),
      ),
    );
    await _settle(tester);

    final bar = find.byType(TabBar);
    expect(bar, findsOneWidget);
    final l10n = StudioLocalizations.of(tester.element(bar));
    expect(
      find.descendant(of: bar, matching: find.text(l10n.cloudProjects)),
      findsNothing,
    );
    // The offline scopes stay reachable.
    expect(
      find.descendant(of: bar, matching: find.text(l10n.allProjects)),
      findsOneWidget,
    );
    // Exactly the three offline scopes, no cloud tab slot.
    expect(
      find.descendant(of: bar, matching: find.byType(Tab)),
      findsNWidgets(3),
    );
  });

  testWidgets('the Go tools tab has no network tool card', (tester) async {
    await tester.pumpWidget(
      _app(
        FunctionsTab(store: ProjectStore(), onOpenTerminal: () {}),
      ),
    );
    await _settle(tester);

    // The shared offline tools are present (real ToolsGrid body).
    expect(find.text('JSON 格式化'), findsOneWidget);
    // Web-only network tools belong to another product and must not appear.
    expect(find.textContaining('HTTP 请求'), findsNothing);
    expect(find.textContaining('本地服务'), findsNothing);
  });

  testWidgets('the Go profile page hides every account entry', (tester) async {
    final fixture = _Fixture.create(root);
    addTearDown(() => fixture.dispose(tester));
    await tester.runAsync(() => fixture.auth.load());
    await tester.pumpWidget(
      _app(
        ProfileTab(
          auth: fixture.auth,
          settings: fixture.settings,
          store: fixture.projects,
        ),
      ),
    );
    await _settle(tester);

    // Networked account/support entries are gone.
    expect(find.text('退出登录'), findsNothing);
    expect(find.text('每日任务'), findsNothing);
    expect(find.text('签到与积分'), findsNothing);
    // Local, offline-only sections stay.
    expect(find.text('本机记录'), findsOneWidget);
    expect(find.text('偏好与支持'), findsOneWidget);
    expect(find.text('设置'), findsOneWidget);
  });

  testWidgets('the Go settings page omits the AI assistant section', (
    tester,
  ) async {
    final fixture = _Fixture.create(root);
    addTearDown(() => fixture.dispose(tester));
    await tester.pumpWidget(
      _app(
        SettingsPage(
          settings: fixture.settings,
          auth: fixture.auth,
          store: fixture.projects,
          // The editor and profile routes both pass this gate; it is the shared
          // switch that hides the AI helper.
          showAi: goProfile.offlineOnly != true,
        ),
      ),
    );
    await _settle(tester);

    expect(find.text('AI 助手'), findsNothing);
    expect(find.text('个人 AI 接口'), findsNothing);
  });

  testWidgets('the Go editor exposes no Git entry point', (tester) async {
    final fixture = _Fixture.create(root, withGoSource: true);
    addTearDown(() => fixture.dispose(tester));
    _sizeTester(tester);

    await tester.pumpWidget(
      _app(
        EditorPage(
          project: fixture.project,
          auth: fixture.auth,
          store: fixture.projects,
          settings: fixture.settings,
          initialOpenPath: 'main.go',
        ),
      ),
    );
    // Wait for the editor to lay out via its "更多" action, which is present as
    // soon as the app bar is built. This avoids importing re_editor just to
    // reference CodeEditor.
    await _pumpIoUntil(
      tester,
      () => find.byTooltip('更多').evaluate().isNotEmpty,
    );

    await tester.tap(find.byTooltip('更多'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    // The Go product is offline-only: Git (local remote ops) must not be
    // reachable. The AI assistant and online terminal are already gated by the
    // same switch.
    expect(
      find.byWidgetPredicate(
        (widget) => widget is PopupMenuItem<String> && widget.value == 'git',
      ),
      findsNothing,
      reason: 'Git menu entry leaked into the offline Go product',
    );
    expect(
      find.byWidgetPredicate(
        (widget) =>
            widget is PopupMenuItem<String> &&
            widget.value == 'online_terminal',
      ),
      findsNothing,
    );
    expect(
      find.byWidgetPredicate(
        (widget) => widget is PopupMenuItem<String> && widget.value == 'ai',
      ),
      findsNothing,
    );
  });

  group('offline background refreshes', () {
    testWidgets(
      'an offline profile does not refresh the account on pull-to-refresh',
      (tester) async {
        final fixture = _Fixture.create(root, signedIn: true);
        addTearDown(() => fixture.dispose(tester));
        await tester.runAsync(() => fixture.auth.load());
        expect(fixture.auth.isLoggedIn, isTrue);

        await tester.pumpWidget(
          _app(
            ProfileTab(
              auth: fixture.auth,
              settings: fixture.settings,
              store: fixture.projects,
            ),
          ),
        );
        await _settle(tester);

        await tester.drag(
          find.byType(ListView).first,
          const Offset(0, 360),
        );
        await _settle(tester);

        // The offline product must not call the account endpoint even though a
        // trustworthy token is still present in auth.json.
        expect(
          fixture.auth.refreshCalls,
          0,
          reason:
              'RefreshIndicator leaked auth.refreshMe() into the offline Go '
              'product',
        );
      },
    );

    testWidgets(
      'a networked profile still refreshes the account on pull-to-refresh',
      (tester) async {
        // Control: the same widget and gesture must still reach refreshMe for a
        // product that is allowed to use the network, so the offline assertion
        // above is not a tautology from a broken drag.
        StudioProfile.current = _networkedProfile();
        final fixture = _Fixture.create(root, signedIn: true);
        addTearDown(() => fixture.dispose(tester));
        await tester.runAsync(() => fixture.auth.load());
        expect(fixture.auth.isLoggedIn, isTrue);

        await tester.pumpWidget(
          _app(
            ProfileTab(
              auth: fixture.auth,
              settings: fixture.settings,
              store: fixture.projects,
            ),
          ),
        );
        await _settle(tester);

        await tester.drag(
          find.byType(ListView).first,
          const Offset(0, 360),
        );
        await _settle(tester);

        expect(fixture.auth.refreshCalls, greaterThan(0));
      },
    );

    testWidgets('an offline profile issues no home activity request', (
      tester,
    ) async {
      final fixture = _Fixture.create(root, signedIn: true);
      addTearDown(() => fixture.dispose(tester));
      await tester.runAsync(() => fixture.auth.load());
      expect(fixture.auth.isLoggedIn, isTrue);

      _sizeTester(tester);
      await tester.pumpWidget(
        _app(
          HomePage(
            store: fixture.projects,
            auth: fixture.auth,
            settings: fixture.settings,
          ),
        ),
      );
      await _settle(tester);
      // An auth change also reaches the refresh path.
      await tester.runAsync(() => fixture.auth.signIn(
        'test-token',
        _user,
      ));
      await _settle(tester);
      await _drainIo(tester);

      expect(
        _CountingHttpOverrides.requests,
        isEmpty,
        reason:
            'HomeTab leaked a server task/activity refresh into the offline Go '
            'product: ${_CountingHttpOverrides.requests}',
      );
    });

    testWidgets('a networked profile does issue a home activity request', (
      tester,
    ) async {
      // Control: with the same residual token, a networked product must reach
      // the task endpoint, proving the counting harness is live.
      StudioProfile.current = _networkedProfile();
      final fixture = _Fixture.create(root, signedIn: true);
      addTearDown(() => fixture.dispose(tester));
      await tester.runAsync(() => fixture.auth.load());
      expect(fixture.auth.isLoggedIn, isTrue);

      _sizeTester(tester);
      await tester.pumpWidget(
        _app(
          HomePage(
            store: fixture.projects,
            auth: fixture.auth,
            settings: fixture.settings,
          ),
        ),
      );
      await _settle(tester);
      await _drainIo(tester);

      expect(
        _CountingHttpOverrides.requests,
        isNotEmpty,
        reason: 'the networked control did not reach the task endpoint',
      );
    });
  });
}

const _residualToken = 'residual-token';

const _user = CommunityUser(
  id: 'user_11111111111111111111111111111111',
  username: 'tester',
  nickname: 'Tester',
  bio: '',
  avatarColor: '#2196F3',
  points: 0,
  checkinStreak: 0,
  provider: 'local',
);

/// A networked control profile that keeps the Go templates but enables every
/// network surface, so the offline assertions can be distinguished from a
/// harness that simply never fires.
StudioProfile _networkedProfile() => StudioProfile(
  id: 'go',
  appTitle: StudioProductCatalog.goShift,
  templates: [ProjectTemplate.empty, ProjectTemplate.go],
  isOffline: false,
  offlineOnly: false,
  productKey: StudioProductCatalog.goShiftKey,
  showHomeTabs: false,
  entryFileNames: const ['main.go', 'src/main.go'],
);

/// Counts every HTTP attempt the shell makes, and fails it locally with a
/// `SocketException` so `ApiClient` converts it to a normal `ApiException`.
class _CountingHttpOverrides extends HttpOverrides {
  /// Absolute URLs of every attempted request in creation order.
  static final List<String> requests = <String>[];

  @override
  HttpClient createHttpClient(SecurityContext? context) =>
      _CountingHttpClient();
}

class _CountingHttpClient implements HttpClient {
  @override
  Future<HttpClientRequest> openUrl(String method, Uri url) async {
    _CountingHttpOverrides.requests.add('$method $url');
    // A real offline device cannot open the socket either; ApiClient maps this
    // to an ApiException the refresh paths already handle.
    throw const SocketException('offline');
  }

  @override
  dynamic noSuchMethod(Invocation invocation) =>
      throw UnsupportedError(
        'Unexpected HttpClient member: ${invocation.memberName}',
      );
}

Widget _app(Widget home) => MaterialApp(
  theme: AppTheme.light,
  debugShowCheckedModeBanner: false,
  // No explicit locale: MaterialApp installs DefaultMaterialLocalizations for
  // the default locale, which NavigationRail and the other shell widgets need.
  // Every string asserted here is hardcoded in the widgets, so the locale does
  // not affect the expectations, and this avoids importing flutter_localizations.
  localizationsDelegates: const [StudioLocalizations.delegate],
  home: home,
);

void _sizeTester(WidgetTester tester) {
  tester.view.physicalSize = const Size(1100, 850);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

Future<void> _settle(WidgetTester tester) async {
  // The real Home/Profile trees keep timers alive, so these tests use bounded
  // pumps instead of pumpAndSettle (matching the shared harnesses).
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 500));
  await tester.pump();
}

/// Lets unawaited real-I/O futures (the shell fires home/activity refreshes with
/// `unawaited`) actually run. A pure `pump` only advances the fake clock and
/// would never observe the HTTP attempt.
Future<void> _drainIo(WidgetTester tester) async {
  for (var attempt = 0; attempt < 50; attempt++) {
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 20)),
    );
    await tester.pump();
  }
}

Future<void> _pumpIoUntil(
  WidgetTester tester,
  bool Function() condition,
) async {
  for (var attempt = 0; attempt < 200; attempt++) {
    await tester.pump(const Duration(milliseconds: 20));
    if (condition()) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
  }
  expect(condition(), isTrue, reason: 'The editor operation did not finish.');
}

class _Fixture {
  _Fixture(this.directory, this.projects, this.project, this.auth);

  final Directory directory;
  final ProjectStore projects;
  final Project project;
  final _CountingAuthStore auth;
  final SettingsStore settings = SettingsStore();

  factory _Fixture.create(
    Directory root, {
    bool withGoSource = false,
    bool signedIn = false,
  }) {
    final directory = root.createTempSync('fixture_');
    final projectDirectory = Directory(p.join(directory.path, 'go-project'))
      ..createSync();
    if (withGoSource) {
      File(p.join(projectDirectory.path, 'main.go')).writeAsStringSync(
        'package main\n\nfunc main() { println("hi") }\n',
      );
    }
    final project = Project.create(
      name: 'go project',
      path: projectDirectory.path,
      language: 'Go',
      type: 'go',
    );
    final registry = File(p.join(directory.path, 'projects.json'));
    registry.writeAsStringSync(
      jsonEncode({
        'version': 1,
        'projects': [project.toJson()],
      }),
    );
    final authFile = File(p.join(directory.path, 'auth.json'));
    if (signedIn) {
      // A trustworthy residual session left by an earlier build: the same
      // service origin ApiConfig owns, with a valid token and user.
      authFile.writeAsStringSync(
        jsonEncode({
          'serviceOrigin': 'https://qfli.suanxiwanjie.cn',
          'token': _residualToken,
          'user': {
            'id': _user.id,
            'username': _user.username,
            'nickname': _user.nickname,
            'bio': _user.bio,
            'avatarColor': _user.avatarColor,
            'points': _user.points,
            'checkinStreak': _user.checkinStreak,
            'provider': _user.provider,
          },
        }),
      );
    }
    return _Fixture(
      directory,
      ProjectStore(storageFile: registry),
      project,
      _CountingAuthStore(storageFile: authFile),
    );
  }

  Future<void> dispose(WidgetTester tester) async {
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
    projects.dispose();
    auth.dispose();
    settings.dispose();
    await tester.runAsync(() async {
      if (directory.existsSync()) await directory.delete(recursive: true);
    });
  }
}

/// An `AuthStore` that counts the manual profile refresh the profile page fires
/// on pull-to-refresh. The real store is used for everything else, so the
/// widget sees a genuine logged-in account.
class _CountingAuthStore extends AuthStore {
  _CountingAuthStore({super.storageFile});

  int refreshCalls = 0;

  @override
  Future<void> refreshMe() async {
    refreshCalls++;
    // Skip the real network call; this test only asserts whether the offline
    // product reached the refresh path at all.
  }
}
