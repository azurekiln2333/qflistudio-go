import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/main.dart' show goProfile;
import 'package:qfli_studio_core/editor/editor_controller.dart';
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/editor/editor_problems_bar.dart';
import 'package:qfli_studio_core/editor/file_explorer.dart';
import 'package:qfli_studio_core/editor/open_file.dart';
import 'package:qfli_studio_core/editor/project_history.dart';
import 'package:qfli_studio_core/editor/retained_editor_host.dart';
import 'package:qfli_studio_core/i18n/studio_localizations.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/pages/home_page.dart';
import 'package:qfli_studio_core/services/app_paths.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_studio_core/workspace/editor_workspace.dart';
import 'package:qfli_studio_core/workspace/saved_workspace.dart';
import 'package:qfli_studio_core/workspace/saved_workspaces_tab.dart';
import 'package:qfli_studio_core/workspace/workspace_store.dart';
import 'package:re_editor/re_editor.dart';

const _cursor = FileCursor(
  baseIndex: 3,
  baseOffset: 5,
  extentIndex: 3,
  extentOffset: 5,
);

const _firstCursor = FileCursor(
  baseIndex: 3,
  baseOffset: 2,
  extentIndex: 3,
  extentOffset: 2,
);

const _liveCursor = CodeLineSelection.collapsed(index: 3, offset: 4);

// Exercise both the actual product entry and the saved-session APIs. A main
// profile or a manually supplied workspace alone cannot prove Go Home entry.

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const pathProvider = MethodChannel('plugins.flutter.io/path_provider');
  late Directory storage;
  late _Fixture fixture;
  StudioProfile? previous;

  setUpAll(() async {
    storage = Directory.systemTemp.createTempSync('qfli_go_workspace_storage_');
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      pathProvider,
      (call) async => storage.path,
    );
    await AppPaths.storageDirectory();
  });

  setUp(() async {
    previous = StudioProfile.current;
    StudioProfile.current = goProfile;
    fixture = await _Fixture.create(storage);
  });

  tearDown(() {
    StudioProfile.current = previous;
  });

  tearDownAll(() {
    binding.defaultBinaryMessenger.setMockMethodCallHandler(pathProvider, null);
    storage.deleteSync(recursive: true);
  });

  testWidgets(
    'Go Home offers local named workspaces without a cloud scope',
    (tester) async {
      fixture.use(tester);
      await tester.pumpWidget(
        _app(
          HomeTab(
            store: fixture.projects,
            auth: fixture.auth,
            settings: fixture.settings,
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 200));
      final bar = find.byType(TabBar);
      final l10n = StudioLocalizations.of(tester.element(bar));
      expect(goProfile.offlineOnly, isTrue);
      expect(goProfile.productKey, StudioProductCatalog.goShiftKey);
      expect(goProfile.supportsSavedWorkspaces, isTrue);
      expect(
        find.descendant(of: bar, matching: find.text(l10n.cloudProjects)),
        findsNothing,
      );
      expect(
        find.descendant(of: bar, matching: find.byType(Tab)),
        findsNWidgets(4),
        reason:
            'The fourth scope is local saved workspaces, independent of cloud.',
      );
      final workspaceTab = find.descendant(
        of: bar,
        matching: find.text('工作区'),
      );
      expect(workspaceTab, findsOneWidget);
      await tester.tap(workspaceTab);
      await _pumpUntil(
        tester,
        () => find.byType(SavedWorkspacesTab).evaluate().isNotEmpty,
        reason: 'The real Go Home must expose the saved workspace list.',
      );
    },
  );

  testWidgets(
    'Go explorer saves two roots by name without changing source',
    (tester) async {
      fixture.use(tester);
      await fixture.mountExplorer(tester);
      await fixture.openWorkspaceDialog(tester, title: '保存工作区');
      await tester.enterText(
        find.byKey(const ValueKey('workspace-name-field')),
        'Go workbench',
      );
      final second = find.byKey(
        ValueKey('workspace-project-${fixture.second.id}'),
      );
      await tester.ensureVisible(second);
      await tester.tap(second);
      await tester.tap(find.widgetWithText(FilledButton, '保存'));
      await _pumpUntil(
        tester,
        () => fixture.lastState?.saved != null,
        reason: 'Naming an unsaved Go session must create a saved workspace.',
      );
      final saved = fixture.lastState!.saved!;
      expect(saved.name, 'Go workbench');
      expect(saved.memberPaths, [fixture.first.path, fixture.second.path]);
      expect(saved.primaryMember!.projectId, fixture.first.id);
      final json = fixture.readWorkspace(saved.id);
      expect(json['name'], 'Go workbench');
      expect(
        (json['members'] as List).map((member) => (member as Map)['path']),
        [fixture.first.path, fixture.second.path],
      );
      fixture.expectSourcesUnchanged();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('Go saved workspace rename and removal preserve source files', (
    tester,
  ) async {
    fixture.use(tester);
    final saved = (await tester.runAsync(fixture.saveWorkspace))!;
    await fixture.mountExplorer(tester, workspace: saved);
    await fixture.openWorkspaceDialog(tester, title: '工作区设置');
    await tester.enterText(
      find.byKey(const ValueKey('workspace-name-field')),
      'Go renamed',
    );
    await tester.tap(find.widgetWithText(FilledButton, '应用'));
    await _pumpUntil(
      tester,
      () => fixture.lastState?.saved?.name == 'Go renamed',
      reason: 'Applying a workspace name must update the live explorer state.',
    );
    expect(fixture.readWorkspace(saved.id)['name'], 'Go renamed');
    expect(
      fixture.workspaces.byId(saved.id)!.memberPaths,
      [fixture.first.path, fixture.second.path],
    );

    await fixture.openWorkspaceDialog(tester, title: '工作区设置');
    await tester.tap(find.widgetWithText(TextButton, '删除工作区记录'));
    await _pumpUntil(
      tester,
      () => find
          .widgetWithText(FilledButton, '删除记录')
          .hitTestable()
          .evaluate()
          .isNotEmpty,
      reason: 'Metadata deletion must require its visible confirmation.',
    );
    await tester.tap(find.widgetWithText(FilledButton, '删除记录'));
    await _pumpUntil(
      tester,
      () =>
          fixture.workspaces.byId(saved.id) == null &&
          fixture.lastState?.saved == null,
      reason:
          'Deletion must detach the explorer and remove the workspace record.',
    );
    expect(fixture.workspaceFile(saved.id).existsSync(), isFalse);
    expect(fixture.projects.projects, hasLength(2));
    fixture.expectSourcesUnchanged();
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Go saved workspace reopens disk session with owners, cursors and tree state',
    (tester) async {
      fixture.use(tester);
      late SavedWorkspace saved;
      await tester.runAsync(() async {
        saved = await fixture.saveWorkspace();
        await fixture.saveSession(saved);
        // A distinct legacy session must not replace this named session.
        await ProjectHistory.save(
          fixture.first.path,
          cursors: const {'legacy.go': _cursor},
          openFiles: const ['legacy.go'],
          activeFile: 'legacy.go',
        );
      });
      late WorkspaceStore reloaded;
      await tester.runAsync(() async {
        reloaded = fixture.newWorkspaceStore();
        await reloaded.load();
      });
      final reopened = reloaded.byId(saved.id)!;
      expect(reopened.session.documents, hasLength(2));
      final host = RetainedEditorController();
      fixture.hosts.add(host);
      await fixture.mountCards(tester, host, workspaceStore: reloaded);
      await tester.tap(find.text(reopened.name));
      await _pumpUntil(
        tester,
        () => host.sessionInfos.length == 1,
        reason: 'The saved Go card must open its disk-backed named session.',
      );
      expect(host.sessionInfos.single.workspace!.id, saved.id);
      expect(host.sessionInfos.single.project.path, fixture.first.path);
      expect(
        host.sessionInfos.single.workspace!.session.documents.map(
          (document) => document.projectPath,
        ),
        [fixture.first.path, fixture.second.path],
      );
      await fixture.unmount(tester);
      var editor = await fixture.mountEditor(
        tester,
        workspace: reopened,
        workspaceStore: reloaded,
        members: [fixture.first, fixture.second],
        expected: 2,
      );
      fixture.expectOwnedTabs(editor);
      await fixture.openTree(tester);
      await fixture.expectExpandedFiles(tester);

      // Collapse and reopen through the toolbar, then reconstruct the whole
      // page from another disk load. Presence in a clipped tree is insufficient.
      await tester.tap(find.byTooltip('收起文件树'));
      await tester.pump(const Duration(milliseconds: 250));
      await fixture.openTree(tester);
      await fixture.expectExpandedFiles(tester);
      await fixture.unmount(tester);
      await tester.runAsync(() => reloaded.load(force: true));
      editor = await fixture.mountEditor(
        tester,
        workspace: reloaded.byId(saved.id)!,
        workspaceStore: reloaded,
        members: [fixture.first, fixture.second],
        expected: 2,
      );
      fixture.expectOwnedTabs(editor);
      await fixture.openTree(tester);
      await fixture.expectExpandedFiles(tester);
      fixture.expectSourcesUnchanged();
      final encoded = jsonEncode(fixture.readWorkspace(saved.id));
      expect(encoded, isNot(contains('println')));
      expect(encoded, isNot(contains('package main')));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('Go standalone still restores legacy multi-root history', (
    tester,
  ) async {
    fixture.use(tester);
    await tester.runAsync(() async {
      await ProjectHistory.save(
        fixture.first.path,
        cursors: const {},
        openFiles: const [],
        activeFile: null,
        documents: fixture.documents,
      );
      await ProjectHistory.saveWorkspaceRoots(
        fixture.first.path,
        [fixture.second.path],
      );
      await ProjectHistory.saveExpandedDirs(fixture.first.path, ['src']);
      await ProjectHistory.saveExpandedDirs(fixture.second.path, ['cmd']);
    });
    final editor = await fixture.mountEditor(tester, expected: 2);
    fixture.expectOwnedTabs(editor);
    await fixture.openTree(tester);
    await fixture.expectExpandedFiles(tester);
    expect(fixture.workspaces.workspaces, isEmpty);
    fixture.expectSourcesUnchanged();
    expect(tester.takeException(), isNull);
  });

  for (final missingPrimary in [true, false]) {
    testWidgets(
      'Go workspace reports missing ${missingPrimary ? 'primary' : 'secondary'} '
      'and opens its survivor',
      (tester) async {
        fixture.use(tester);
        late SavedWorkspace saved;
        await tester.runAsync(() async {
          saved = await fixture.saveWorkspace();
          await fixture.saveSession(saved);
        });
        final missing = missingPrimary ? fixture.first : fixture.second;
        final survivor = missingPrimary ? fixture.second : fixture.first;
        final parked = Directory(
          missing.path,
        ).renameSync('${missing.path}-parked');
        final host = RetainedEditorController();
        fixture.hosts.add(host);
        await fixture.mountCards(tester, host);
        await tester.tap(find.text(saved.name));
        await _pumpUntil(
          tester,
          () => find.text('部分项目不可用').hitTestable().evaluate().isNotEmpty,
          reason: 'Opening must visibly report the unavailable project.',
        );
        expect(find.textContaining(missing.path), findsOneWidget);
        expect(host.sessionInfos, isEmpty);
        await tester.tap(find.widgetWithText(FilledButton, '继续打开'));
        await _pumpUntil(
          tester,
          () => host.sessionInfos.length == 1,
          reason:
              'Confirmation must open the same named workspace with its survivor.',
        );
        final info = host.sessionInfos.single;
        expect(info.workspace!.id, saved.id);
        expect(info.project.path, survivor.path);
        final resolution = (await tester.runAsync(
          () => fixture.workspaces.resolve(info.workspace!, fixture.projects),
        ))!;
        expect(resolution.projects.map((project) => project.path), [
          survivor.path,
        ]);
        expect(resolution.primaryMissing, missingPrimary);
        await fixture.unmount(tester);
        final editor = await fixture.mountEditor(
          tester,
          workspace: info.workspace,
          project: info.project,
          members: resolution.projects,
          expected: 1,
        );
        expect(editor.files.single.projectRootPath, survivor.path);
        expect(editor.files.single.ownerProjectName, survivor.name);
        expect(editor.files.single.projectType, 'go');
        await fixture.openTree(tester);
        expect(fixture.root(missing), findsNothing);
        expect(fixture.root(survivor).hitTestable(), findsOneWidget);
        final relative = missingPrimary ? 'src/main.go' : 'cmd/worker.go';
        expect(File(p.join(parked.path, relative)).existsSync(), isTrue);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets('Go workspace with all roots missing refuses to open an editor', (
    tester,
  ) async {
    fixture.use(tester);
    final saved = (await tester.runAsync(fixture.saveWorkspace))!;
    final parked = [
      for (final project in [fixture.first, fixture.second])
        Directory(project.path).renameSync('${project.path}-parked'),
    ];
    final host = RetainedEditorController();
    fixture.hosts.add(host);
    await fixture.mountCards(tester, host);
    await tester.tap(find.text(saved.name));
    await _pumpUntil(
      tester,
      () => find.text('无法打开工作区').hitTestable().evaluate().isNotEmpty,
      reason: 'An all-missing workspace must offer an actionable refusal.',
    );
    expect(host.sessionInfos, isEmpty);
    expect(find.byType(EditorPage), findsNothing);
    await tester.tap(find.widgetWithText(TextButton, '关闭'));
    await tester.pump(const Duration(milliseconds: 250));
    expect(fixture.workspaces.byId(saved.id), isNotNull);
    expect(File(p.join(parked[0].path, 'src', 'main.go')).existsSync(), isTrue);
    expect(File(p.join(parked[1].path, 'cmd', 'worker.go')).existsSync(), isTrue);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Go retained attachWorkspace replaces same-ID rename and keeps live state',
    (tester) async {
      fixture.use(tester);
      final saved = (await tester.runAsync(fixture.saveLiveWorkspace))!;
      final host = RetainedEditorController();
      fixture.hosts.add(host);
      final editor = await fixture.mountRetainedEditor(tester, host, saved);
      await fixture.prepareLiveState(tester, editor);
      final pageState = tester.state(find.byType(EditorPage));
      final treeState = tester.state(find.byType(FileExplorer));
      final files = List<OpenFile>.of(editor.files);
      final sessionKey = host.sessionInfos.single.key;
      final result = await _pumpResult(
        tester,
        fixture.workspaces.save(
          existing: saved,
          name: 'Go attached rename',
          members: [fixture.first, fixture.second],
          primary: fixture.first,
        ),
        reason: 'The external rename must finish its serialized metadata write.',
      );
      expect(result.error, isNull);
      final renamed = result.workspace!;
      expect(renamed.id, saved.id);
      expect(renamed.memberPaths, saved.memberPaths);
      host.attachWorkspace(
        sessionKey,
        renamed,
        [fixture.first, fixture.second],
      );
      await fixture.expectWorkspaceTitle(tester, renamed.name);
      expect(host.sessionInfos, hasLength(1));
      expect(host.sessionInfos.single.key, sessionKey);
      expect(host.sessionInfos.single.workspace, same(renamed));
      expect(tester.state(find.byType(EditorPage)), same(pageState));
      expect(tester.state(find.byType(FileExplorer)), same(treeState));
      expect(_currentEditor(tester), same(editor));
      fixture.expectLiveBuffers(editor, files);
      await fixture.expectLiveExpansion(tester);
      await fixture.openWorkspaceDialog(tester, title: '工作区设置');
      expect(
        tester.widget<TextField>(
          find.byKey(const ValueKey('workspace-name-field')),
        ).controller!.text,
        renamed.name,
      );
      await tester.tap(find.widgetWithText(TextButton, '取消'));
      await _pumpUntil(
        tester,
        () => find.byType(AlertDialog).evaluate().isEmpty,
        reason: 'The externally renamed settings must close normally.',
      );
      await fixture.restoreThroughCurrentLabel(tester, renamed.name);
      expect(tester.state(find.byType(EditorPage)), same(pageState));
      expect(_currentEditor(tester), same(editor));
      fixture.expectLiveBuffers(editor, files);
      await fixture.expectLiveExpansion(tester);
      fixture.expectSourcesUnchanged();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'Go same-key same-ID refresh updates name members and primary in place',
    (tester) async {
      fixture.use(tester);
      final saved = (await tester.runAsync(fixture.saveLiveWorkspace))!;
      const pageKey = ValueKey('go-same-id-editor');
      final editor = await fixture.mountEditor(
        tester,
        pageKey: pageKey,
        workspace: saved,
        members: [fixture.first, fixture.second],
        expected: 2,
      );
      await fixture.prepareLiveState(tester, editor);
      final pageState = tester.state(find.byKey(pageKey));
      final treeState = tester.state(find.byType(FileExplorer));
      final files = List<OpenFile>.of(editor.files);
      final result = await _pumpResult(
        tester,
        fixture.workspaces.save(
          existing: saved,
          name: 'Go externally refreshed',
          members: [fixture.second, fixture.first],
          primary: fixture.second,
        ),
        reason: 'The new name and effective primary must be saved first.',
      );
      expect(result.error, isNull);
      // Deliver a previous view snapshot with current metadata. A same-ID
      // widget update must keep the mounted expansion instead of restoring it.
      // This copy is widget input only; it is not written back to the store.
      final refreshed = result.workspace!.copyWith(session: saved.session);
      expect(refreshed.id, saved.id);
      final currentEditor = await fixture.mountEditor(
        tester,
        pageKey: pageKey,
        workspace: refreshed,
        project: fixture.second,
        members: [fixture.second, fixture.first],
        expected: 2,
      );
      await fixture.expectWorkspaceTitle(tester, refreshed.name);
      expect(tester.state(find.byKey(pageKey)), same(pageState));
      expect(tester.state(find.byType(FileExplorer)), same(treeState));
      expect(currentEditor, same(editor));
      fixture.expectLiveBuffers(editor, files);
      await fixture.expectLiveExpansion(tester);
      final page = tester.widget<EditorPage>(find.byKey(pageKey));
      expect(page.project.path, fixture.second.path);
      expect(page.workspace!.primaryMember!.path, fixture.second.path);
      expect(page.workspace!.memberPaths, [
        fixture.second.path,
        fixture.first.path,
      ]);
      expect(
        tester.getTopLeft(fixture.root(fixture.second)).dy,
        lessThan(tester.getTopLeft(fixture.root(fixture.first)).dy),
      );
      await fixture.openWorkspaceDialog(tester, title: '工作区设置');
      expect(
        tester.widget<TextField>(
          find.byKey(const ValueKey('workspace-name-field')),
        ).controller!.text,
        refreshed.name,
      );
      final primaryTile = tester.widget<CheckboxListTile>(
        find.byKey(ValueKey('workspace-project-${fixture.second.id}')),
      );
      expect(primaryTile.value, isTrue);
      expect(primaryTile.onChanged, isNull);
      expect(
        tester.widget<CheckboxListTile>(
          find.byKey(ValueKey('workspace-project-${fixture.first.id}')),
        ).value,
        isTrue,
      );
      await tester.tap(find.widgetWithText(TextButton, '取消'));
      await _pumpUntil(
        tester,
        () => find.byType(AlertDialog).evaluate().isEmpty,
        reason: 'Closing metadata settings must return to the same editor.',
      );
      fixture.expectLiveBuffers(editor, files);
      await fixture.expectLiveExpansion(tester);
      fixture.expectSourcesUnchanged();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'Go editor same-ID rename reaches retained owner and restore label',
    (tester) async {
      fixture.use(tester);
      final saved = (await tester.runAsync(fixture.saveLiveWorkspace))!;
      final host = RetainedEditorController();
      fixture.hosts.add(host);
      final editor = await fixture.mountRetainedEditor(tester, host, saved);
      await fixture.prepareLiveState(tester, editor);
      final pageState = tester.state(find.byType(EditorPage));
      final treeState = tester.state(find.byType(FileExplorer));
      final files = List<OpenFile>.of(editor.files);
      final sessionKey = host.sessionInfos.single.key;
      await fixture.openWorkspaceDialog(tester, title: '工作区设置');
      await tester.enterText(
        find.byKey(const ValueKey('workspace-name-field')),
        'Go editor rename',
      );
      await tester.tap(find.widgetWithText(FilledButton, '应用'));
      await _pumpUntil(
        tester,
        () => host.sessionInfos.single.workspace?.name == 'Go editor rename',
        reason:
            'The real onWorkspaceSaved path must notify the retained owner '
            'for a same-ID rename.',
      );
      await fixture.expectWorkspaceTitle(tester, 'Go editor rename');
      expect(host.sessionInfos, hasLength(1));
      expect(host.sessionInfos.single.key, sessionKey);
      expect(host.sessionInfos.single.workspace!.id, saved.id);
      expect(host.sessionInfos.single.workspace!.memberPaths, [
        fixture.first.path,
        fixture.second.path,
      ]);
      expect(fixture.readWorkspace(saved.id)['name'], 'Go editor rename');
      expect(tester.state(find.byType(EditorPage)), same(pageState));
      expect(tester.state(find.byType(FileExplorer)), same(treeState));
      expect(_currentEditor(tester), same(editor));
      fixture.expectLiveBuffers(editor, files);
      await fixture.expectLiveExpansion(tester);
      await fixture.restoreThroughCurrentLabel(tester, 'Go editor rename');
      expect(tester.state(find.byType(EditorPage)), same(pageState));
      fixture.expectLiveBuffers(editor, files);
      await fixture.expectLiveExpansion(tester);
      await fixture.openWorkspaceDialog(tester, title: '工作区设置');
      expect(
        tester.widget<TextField>(
          find.byKey(const ValueKey('workspace-name-field')),
        ).controller!.text,
        'Go editor rename',
      );
      await tester.tap(find.widgetWithText(TextButton, '取消'));
      await _pumpUntil(
        tester,
        () => find.byType(AlertDialog).evaluate().isEmpty,
        reason: 'The renamed dialog must close normally.',
      );
      fixture.expectSourcesUnchanged();
      expect(tester.takeException(), isNull);
    },
  );
}

Widget _app(Widget home) => MaterialApp(
  localizationsDelegates: const [StudioLocalizations.delegate],
  home: home,
);

Future<void> _pumpUntil(
  WidgetTester tester,
  bool Function() complete, {
  required String reason,
}) async {
  for (var attempt = 0; attempt < 200; attempt++) {
    await tester.pump(const Duration(milliseconds: 20));
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 5)),
    );
    if (complete()) return;
  }
  expect(complete(), isTrue, reason: reason);
}

EditorController _currentEditor(WidgetTester tester) => tester
    .widget<EditorProblemsBar>(find.byType(EditorProblemsBar).first)
    .analysis
    .editor;

Future<T> _pumpResult<T>(
  WidgetTester tester,
  Future<T> pending, {
  required String reason,
}) async {
  var complete = false;
  late T result;
  Object? failure;
  StackTrace? failureStack;
  pending.then<void>(
    (value) {
      result = value;
      complete = true;
    },
    onError: (Object error, StackTrace stack) {
      failure = error;
      failureStack = stack;
      complete = true;
    },
  );
  await _pumpUntil(tester, () => complete, reason: reason);
  if (failure != null) {
    Error.throwWithStackTrace(failure!, failureStack!);
  }
  return result;
}

class _Fixture {
  _Fixture(this.directory, this.projects, this.workspaces, this.first, this.second)
    : auth = AuthStore(storageFile: File(p.join(directory.path, 'auth.json')));

  final Directory directory;
  final ProjectStore projects;
  final WorkspaceStore workspaces;
  final Project first;
  final Project second;
  final AuthStore auth;
  final settings = SettingsStore();
  final hosts = <RetainedEditorController>[];
  final _extraStores = <WorkspaceStore>[];
  EditorController? _explorerEditor;
  EditorWorkspaceState? lastState;

  static const firstSource =
      'package main\n\nfunc main() {\n  println("go-first")\n}\n';
  static const secondSource =
      'package main\n\nfunc main() {\n  println("go-second")\n}\n';
  static const dirtySource = '$secondSource// same-ID edit stays in memory\n';

  static Future<_Fixture> create(Directory storage) async {
    final directory = storage.createTempSync('fixture_');
    final first = Project.create(
      name: 'Go first',
      path: p.join(directory.path, 'first'),
      type: 'go',
      language: 'Go',
    );
    final second = Project.create(
      name: 'Go second',
      path: p.join(directory.path, 'second'),
      type: 'go',
      language: 'Go',
    );
    Directory(p.join(first.path, 'src')).createSync(recursive: true);
    Directory(p.join(second.path, 'cmd')).createSync(recursive: true);
    File(p.join(first.path, 'src', 'main.go')).writeAsStringSync(firstSource);
    File(p.join(second.path, 'cmd', 'worker.go')).writeAsStringSync(secondSource);
    File(p.join(first.path, 'legacy.go')).writeAsStringSync(firstSource);
    final registry = File(p.join(directory.path, 'projects.json'))
      ..writeAsStringSync(
        jsonEncode({
          'projects': [first.toJson(), second.toJson()],
        }),
      );
    final projects = ProjectStore(storageFile: registry);
    await projects.load();
    final workspaces = WorkspaceStore(
      root: Directory(p.join(directory.path, 'workspaces')),
    );
    await workspaces.load();
    return _Fixture(directory, projects, workspaces, first, second);
  }

  void use(WidgetTester tester) {
    tester.view.physicalSize = const Size(1100, 850);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(() => dispose(tester));
  }

  List<ProjectDocumentSession> get documents => [
    ProjectDocumentSession(
      projectPath: first.path,
      relativePath: 'src/main.go',
      cursor: _firstCursor,
    ),
    ProjectDocumentSession(
      projectPath: second.path,
      relativePath: 'cmd/worker.go',
      cursor: _cursor,
      isActive: true,
    ),
  ];

  Future<SavedWorkspace> saveWorkspace() async {
    final result = await workspaces.save(
      name: 'Go workbench',
      members: [first, second],
      primary: first,
    );
    expect(result.error, isNull);
    return result.workspace!;
  }

  Future<void> saveSession(SavedWorkspace workspace) => workspaces.saveSession(
    workspace,
    WorkspaceSessionSnapshot(
      primaryPath: first.path,
      documents: documents,
      expandedDirs: {
        first.path: ['src'],
        second.path: ['cmd'],
      },
      rootExpanded: {first.path: true, second.path: true},
    ),
  );

  Future<SavedWorkspace> saveLiveWorkspace() async {
    final live = Directory(p.join(first.path, 'src', 'live'))..createSync();
    File(p.join(live.path, 'nested.go')).writeAsStringSync('package main\n');
    final saved = await saveWorkspace();
    await saveSession(saved);
    return workspaces.byId(saved.id)!;
  }

  WorkspaceStore newWorkspaceStore() {
    final store = WorkspaceStore(
      root: Directory(p.join(directory.path, 'workspaces')),
    );
    _extraStores.add(store);
    return store;
  }

  File workspaceFile(String id) =>
      File(p.join(directory.path, 'workspaces', '$id.json'));

  Map<String, dynamic> readWorkspace(String id) =>
      jsonDecode(workspaceFile(id).readAsStringSync()) as Map<String, dynamic>;

  Finder root(Project project) =>
      find.byKey(ValueKey('workspace-root-${project.path}'));

  Finder entry(Project project, String name) =>
      find.descendant(of: root(project), matching: find.text(name));

  Future<void> mountExplorer(
    WidgetTester tester, {
    SavedWorkspace? workspace,
  }) async {
    _explorerEditor = EditorController(project: first);
    await tester.pumpWidget(
      _app(
        Scaffold(
          body: Align(
            alignment: Alignment.topLeft,
            child: SizedBox(
              width: 360,
              height: 700,
              child: FileExplorer(
                project: first,
                editor: _explorerEditor!,
                store: projects,
                settings: settings,
                workspace: workspace,
                workspaceMembers: workspace == null ? const [] : [first, second],
                workspaceStore: workspaces,
                onWorkspaceChanged: (state) => lastState = state,
              ),
            ),
          ),
        ),
      ),
    );
    await _pumpUntil(
      tester,
      () => entry(first, 'src').evaluate().isNotEmpty,
      reason: 'The explorer must finish its real directory load.',
    );
  }

  Future<void> openWorkspaceDialog(
    WidgetTester tester, {
    required String title,
  }) async {
    await tester.tap(find.byTooltip('工作区项目'));
    await _pumpUntil(
      tester,
      () => find.text(title).hitTestable().evaluate().isNotEmpty,
      reason: 'The real Go explorer must expose the $title dialog.',
    );
    expect(tester.widget<AlertDialog>(find.byType(AlertDialog)).scrollable, isTrue);
    expect(
      find.byKey(const ValueKey('workspace-name-field')).hitTestable(),
      findsOneWidget,
    );
  }

  Future<EditorController> mountEditor(
    WidgetTester tester, {
    Key? pageKey,
    SavedWorkspace? workspace,
    WorkspaceStore? workspaceStore,
    Project? project,
    List<Project> members = const [],
    required int expected,
  }) async {
    await tester.pumpWidget(
      _app(
        EditorPage(
          key: pageKey,
          project: project ?? first,
          auth: auth,
          store: projects,
          settings: settings,
          workspace: workspace,
          workspaceMembers: members,
          workspaceStore: workspaceStore ?? workspaces,
        ),
      ),
    );
    EditorController? editor;
    await _pumpUntil(
      tester,
      () {
        final bars = find.byType(EditorProblemsBar);
        if (bars.evaluate().isEmpty) return false;
        editor = tester.widget<EditorProblemsBar>(bars.first).analysis.editor;
        return editor!.files.length == expected;
      },
      reason: 'The real Go editor must restore $expected owned tabs.',
    );
    // Selection of the active document follows the final openPath await.
    await tester.pump(const Duration(milliseconds: 40));
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 5)),
    );
    await tester.pump();
    return editor!;
  }

  Future<EditorController> mountRetainedEditor(
    WidgetTester tester,
    RetainedEditorController host,
    SavedWorkspace workspace,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: const [StudioLocalizations.delegate],
        navigatorObservers: [host.navigatorObserver],
        builder: (context, child) =>
            RetainedEditorHost(controller: host, child: child!),
        home: const Scaffold(body: Text('Go workspace host')),
      ),
    );
    host.open(
      project: first,
      auth: auth,
      store: projects,
      settings: settings,
      workspace: workspace,
      workspaceProjects: [first, second],
      workspaceStore: workspaces,
    );
    await _pumpUntil(
      tester,
      () =>
          find.byType(EditorProblemsBar).evaluate().isNotEmpty &&
          _currentEditor(tester).files.length == 2 &&
          _currentEditor(tester).current?.projectRootPath == second.path,
      reason: 'The real retained Go editor must finish restoring both owners.',
    );
    return _currentEditor(tester);
  }

  Future<void> prepareLiveState(
    WidgetTester tester,
    EditorController editor,
  ) async {
    await openTree(tester);
    await expectExpandedFiles(tester);
    final live = entry(first, 'live');
    await tester.ensureVisible(live);
    await tester.tap(live);
    await expectLiveExpansion(tester);
    expect(settings.autoSave, isFalse);
    expect(editor.current!.projectRootPath, second.path);
    editor.current!.controller.text = dirtySource;
    editor.current!.controller.selection = _liveCursor;
    await tester.pump();
    expect(editor.current!.dirty, isTrue);
  }

  void expectLiveBuffers(EditorController editor, List<OpenFile> files) {
    expect(editor.files, hasLength(files.length));
    for (var index = 0; index < files.length; index++) {
      expect(editor.files[index], same(files[index]));
    }
    expect(editor.current, same(files[1]));
    expect(editor.files.first.projectRootPath, first.path);
    expect(editor.files.first.controller.text, firstSource);
    expect(editor.files.first.dirty, isFalse);
    expect(
      editor.files.first.controller.selection.baseIndex,
      _firstCursor.baseIndex,
    );
    expect(
      editor.files.first.controller.selection.baseOffset,
      _firstCursor.baseOffset,
    );
    expect(
      editor.files.first.controller.selection.extentIndex,
      _firstCursor.extentIndex,
    );
    expect(
      editor.files.first.controller.selection.extentOffset,
      _firstCursor.extentOffset,
    );
    expect(editor.current!.projectRootPath, second.path);
    expect(editor.current!.controller.text, dirtySource);
    expect(editor.current!.dirty, isTrue);
    expect(editor.current!.controller.selection.baseIndex, _liveCursor.baseIndex);
    expect(
      editor.current!.controller.selection.baseOffset,
      _liveCursor.baseOffset,
    );
    expect(
      editor.current!.controller.selection.extentIndex,
      _liveCursor.extentIndex,
    );
    expect(
      editor.current!.controller.selection.extentOffset,
      _liveCursor.extentOffset,
    );
  }

  Future<void> expectLiveExpansion(WidgetTester tester) => _pumpUntil(
    tester,
    () =>
        entry(first, 'nested.go').hitTestable().evaluate().isNotEmpty &&
        entry(second, 'worker.go').hitTestable().evaluate().isNotEmpty,
    reason: 'The live nested directory and both roots must stay expanded.',
  );

  Future<void> expectWorkspaceTitle(WidgetTester tester, String name) =>
      _pumpUntil(
        tester,
        () => find
            .descendant(
              of: find.byType(AppBar),
              matching: find.textContaining('工作区「$name」'),
            )
            .hitTestable()
            .evaluate()
            .isNotEmpty,
        reason: 'The mounted editor must display the current workspace name.',
      );

  Future<void> restoreThroughCurrentLabel(
    WidgetTester tester,
    String name,
  ) async {
    await tester.tap(find.byTooltip('暂时收起编辑器'));
    final restore = find.text('返回编辑器 · $name');
    await _pumpUntil(
      tester,
      () => restore.hitTestable().evaluate().isNotEmpty,
      reason: 'The retained restore label must use the new same-ID name.',
    );
    expect(restore.hitTestable(), findsOneWidget);
    await tester.tap(restore);
    await expectWorkspaceTitle(tester, name);
  }

  void expectOwnedTabs(EditorController editor) {
    expect(editor.files.map((file) => file.path), [
      p.join(first.path, 'src', 'main.go'),
      p.join(second.path, 'cmd', 'worker.go'),
    ]);
    expect(editor.files.map((file) => file.projectRootPath), [
      first.path,
      second.path,
    ]);
    expect(editor.files.map((file) => file.ownerProjectName), [
      first.name,
      second.name,
    ]);
    expect(editor.files.map((file) => file.projectType), ['go', 'go']);
    expect(editor.files.map((file) => file.controller.text), [
      firstSource,
      secondSource,
    ]);
    expect(editor.current!.projectRootPath, second.path);
    for (var index = 0; index < editor.files.length; index++) {
      final file = editor.files[index];
      final cursor = documents[index].cursor;
      expect(file.controller.selection.baseIndex, cursor.baseIndex);
      expect(file.controller.selection.baseOffset, cursor.baseOffset);
      expect(file.controller.selection.extentIndex, cursor.extentIndex);
      expect(file.controller.selection.extentOffset, cursor.extentOffset);
      expect(file.dirty, isFalse);
    }
  }

  Future<void> openTree(WidgetTester tester) async {
    await tester.tap(find.byTooltip('打开文件树'));
    await _pumpUntil(
      tester,
      () => find.byTooltip('工作区项目').hitTestable().evaluate().isNotEmpty,
      reason: 'Open the sidebar physically before checking its tree.',
    );
  }

  Future<void> expectExpandedFiles(WidgetTester tester) => _pumpUntil(
    tester,
    () =>
        entry(first, 'main.go').hitTestable().evaluate().isNotEmpty &&
        entry(second, 'worker.go').hitTestable().evaluate().isNotEmpty,
    reason: 'Both Go roots must restore their independently expanded directories.',
  );

  Future<void> mountCards(
    WidgetTester tester,
    RetainedEditorController host, {
    WorkspaceStore? workspaceStore,
  }) async {
    await tester.pumpWidget(
      _app(
        RetainedEditorScope(
          controller: host,
          child: Scaffold(
            body: SavedWorkspacesTab(
              store: projects,
              auth: auth,
              settings: settings,
              workspaceStore: workspaceStore ?? workspaces,
            ),
          ),
        ),
      ),
    );
    await _pumpUntil(
      tester,
      () => find.text('Go workbench').hitTestable().evaluate().isNotEmpty,
      reason: 'The real saved workspace card must be ready for input.',
    );
  }

  void expectSourcesUnchanged() {
    expect(
      File(p.join(first.path, 'src', 'main.go')).readAsStringSync(),
      firstSource,
    );
    expect(
      File(p.join(second.path, 'cmd', 'worker.go')).readAsStringSync(),
      secondSource,
    );
    expect(
      File(p.join(first.path, 'legacy.go')).readAsStringSync(),
      firstSource,
    );
  }

  Future<void> unmount(WidgetTester tester) async {
    FocusManager.instance.primaryFocus?.unfocus();
    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpWidget(const SizedBox.shrink());
    // Queued writes originate in the fake zone. Pump that zone while allowing
    // real IO; awaiting their whole queue inside runAsync would deadlock.
    var complete = false;
    Object? writeError;
    Future.wait<void>([
      WorkspaceStore.instance.settle(),
      workspaces.settle(),
      for (final store in _extraStores) store.settle(),
      for (final project in [first, second])
        ProjectHistory.load(project.path).then<void>((_) {}),
    ]).then<void>(
      (_) {
        complete = true;
      },
      onError: (Object error, StackTrace stack) {
        writeError = error;
        complete = true;
      },
    );
    await _pumpUntil(
      tester,
      () => complete,
      reason:
          'Workspace and each project history must drain before fixture deletion.',
    );
    expect(writeError, isNull);
    expect(tester.takeException(), isNull);
  }

  Future<void> dispose(WidgetTester tester) async {
    await unmount(tester);
    _explorerEditor?.dispose();
    for (final host in hosts) {
      host.dispose();
    }
    for (final store in _extraStores) {
      store.dispose();
    }
    workspaces.dispose();
    projects.dispose();
    auth.dispose();
    settings.dispose();
    directory.deleteSync(recursive: true);
  }
}
