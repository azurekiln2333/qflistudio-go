import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/main.dart' show goProfile;
import 'package:qfli_studio_core/content/asset_content_repository.dart';
import 'package:qfli_studio_core/content/content_repository.dart';
import 'package:qfli_studio_core/editor/editor_fonts.dart';
import 'package:qfli_studio_core/editor/editor_page.dart';
import 'package:qfli_studio_core/editor/file_explorer.dart';
import 'package:qfli_studio_core/editor/project_history.dart';
import 'package:qfli_studio_core/i18n/studio_localizations.dart';
import 'package:qfli_studio_core/models/tutorial.dart';
import 'package:qfli_studio_core/pages/local_content_pages.dart';
import 'package:qfli_studio_core/services/app_paths.dart';
import 'package:qfli_studio_core/services/code_import_service.dart';
import 'package:qfli_studio_core/services/project_config.dart';
import 'package:qfli_studio_core/services/project_templates.dart';
import 'package:qfli_studio_core/services/runner_service.dart';
import 'package:qfli_studio_core/services/studio_profile.dart';
import 'package:qfli_studio_core/services/task_activity_service.dart';
import 'package:qfli_studio_core/store/auth_store.dart';
import 'package:qfli_studio_core/store/project_store.dart';
import 'package:qfli_studio_core/store/settings_store.dart';
import 'package:qfli_studio_core/theme/app_theme.dart';
import 'package:qfli_studio_core/widgets/code_snippet.dart';

const _code =
    'package main\n\nimport "fmt"\n\n'
    'func main() { fmt.Println("imported lesson") }\n';
const _editedCode =
    'package main\n\nimport "fmt"\n\n'
    'func main() { fmt.Println("edited before import") }\n';
const _example = ExampleCode(
  id: 'go-import-example',
  type: 'go',
  title: 'Print a message',
  summary: 'Write a message to standard output.',
  code: _code,
  output: 'imported lesson',
);
const _fileNameKey = ValueKey('import-file-name');
const _projectNameKey = ValueKey('import-project-name');
const _editorIcon = Icons.edit_note_outlined;
const _projectIcon = Icons.drive_file_move_outlined;

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const pathProvider = MethodChannel('plugins.flutter.io/path_provider');
  late Directory scratchStorage;
  late Directory temporary;
  late File registry;
  late _RedirectedProjectStore store;
  late AuthStore auth;
  late SettingsStore settings;
  StudioProfile? previousProfile;
  String? clipboard;

  setUpAll(() async {
    scratchStorage = Directory.systemTemp.createTempSync(
      'qfli_import_scratch_',
    );
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      pathProvider,
      (call) async => scratchStorage.path,
    );
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      SystemChannels.platform,
      (call) async {
        if (call.method == 'Clipboard.setData') {
          clipboard = (call.arguments as Map)['text'] as String?;
        }
        if (call.method == 'Clipboard.getData') return {'text': clipboard};
        return null;
      },
    );
    // Initialize cached I/O before widget tests enter Flutter's fake clock.
    expect(await AppPaths.storageDirectory(), scratchStorage.path);
    await TaskActivityService.instance.initialize();
    await _loadRenderFonts();
  });

  setUp(() async {
    previousProfile = StudioProfile.current;
    StudioProfile.current = goProfile;
    clipboard = null;
    temporary = Directory.systemTemp.createTempSync('qfli_content_import_');
    registry = File(p.join(temporary.path, 'projects.json'));
    store = _RedirectedProjectStore(
      registry: registry,
      location: temporary.path,
    );
    auth = AuthStore(storageFile: File(p.join(temporary.path, 'auth.json')));
    settings = SettingsStore(
      storageFile: File(p.join(temporary.path, 'settings.json')),
    );
    await store.load();
  });

  tearDown(() {
    StudioProfile.current = previousProfile;
    store.dispose();
    auth.dispose();
    settings.dispose();
    if (temporary.existsSync()) temporary.deleteSync(recursive: true);
  });

  tearDownAll(() {
    binding.defaultBinaryMessenger.setMockMethodCallHandler(pathProvider, null);
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      SystemChannels.platform,
      null,
    );
    if (scratchStorage.existsSync()) scratchStorage.deleteSync(recursive: true);
  });

  group('Code imports on the real filesystem', () {
    test(
      'invalid paths and reserved filenames create no files or projects',
      () async {
        expect(CodeImportService.suggestedFileName('go'), 'main.go');
        final before = _filesUnder(temporary);
        for (final name in [
          '',
          '.',
          '..',
          '../outside.go',
          'src/nested.go',
          r'src\nested.go',
          r'C:\outside.go',
          'CON.go',
          'nul',
          'LPT1.txt',
          'bad?.go',
          'name.',
          ' padded.go',
          'bad\u0000.go',
        ]) {
          expect(
            CodeImportService.isValidFileName(name),
            isFalse,
            reason: name,
          );
          await expectLater(
            CodeImportService.openInEditor(
              example: _example,
              fileName: name,
              location: temporary.path,
            ),
            throwsA(_failure(CodeImportFailure.invalidFileName)),
            reason: name,
          );
          await expectLater(
            store.createProjectFromExample(
              name: 'Invalid import',
              example: _example,
              fileName: name,
            ),
            throwsA(_failure(CodeImportFailure.invalidFileName)),
            reason: name,
          );
        }
        expect(_filesUnder(temporary), before);
        expect(store.projects, isEmpty);
      },
    );

    test(
      'editor import writes exact code without changing the registry',
      () async {
        final existing = await store.createProject(
          name: 'Existing project',
          location: temporary.path,
          template: ProjectTemplate.go,
        );
        expect(existing.error, isNull);
        final registryBefore = registry.readAsStringSync();
        final imported = await CodeImportService.openInEditor(
          example: _example,
          fileName: 'scratch_lesson.go',
          location: temporary.path,
        );
        expect(
          imported.path,
          p.join(imported.project.path, 'src', 'scratch_lesson.go'),
        );
        expect(File(imported.path).readAsStringSync(), _code);
        expect(RunnerService.findEntry(imported.project.path), imported.path);
        expect(
          ProjectConfig.read(imported.project.path)!['entryFile'],
          p.join('src', 'scratch_lesson.go'),
        );
        expect(registry.readAsStringSync(), registryBefore);
        expect(store.projects.map((project) => project.id), [
          existing.project!.id,
        ]);
        File(imported.path).writeAsStringSync(_editedCode);
        expect(File(imported.path).readAsStringSync(), _editedCode);
      },
    );

    test(
      'custom new-project entry persists without a second main function',
      () async {
        final result = await store.createProjectFromExample(
          name: 'Custom entry project',
          example: _example,
          fileName: 'lesson_entry.go',
        );
        expect(result.error, isNull);
        final project = result.project!;
        final entry = p.join(project.path, 'src', 'lesson_entry.go');
        expect(File(entry).readAsStringSync(), _code);
        expect(
          File(p.join(project.path, 'src', 'main.go')).existsSync(),
          isFalse,
        );
        expect(
          _filesUnder(
            Directory(project.path),
          ).keys.where((name) => name.endsWith('.go')),
          [p.join('src', 'lesson_entry.go')],
        );
        expect(RunnerService.findEntry(project.path), entry);
        final reloaded = ProjectStore(storageFile: registry);
        await reloaded.load();
        expect(reloaded.projects.single.id, project.id);
        expect(reloaded.projects.single.path, project.path);
        expect(reloaded.projects.single.name, 'Custom entry project');
        reloaded.dispose();
      },
    );

    test(
      'existing project import preserves occupied files and allows a new name',
      () async {
        final result = await store.createProject(
          name: 'Existing project',
          location: temporary.path,
          template: ProjectTemplate.go,
        );
        final project = result.project!;
        final previous = _filesUnder(Directory(project.path));
        final registryBefore = registry.readAsStringSync();
        await expectLater(
          CodeImportService.importIntoProject(
            project: project,
            example: _example,
            fileName: 'main.go',
          ),
          throwsA(_failure(CodeImportFailure.fileExists)),
        );
        expect(_filesUnder(Directory(project.path)), previous);
        final imported = await CodeImportService.importIntoProject(
          project: project,
          example: _example,
          fileName: 'next_lesson.go',
        );
        expect(imported.project, same(project));
        expect(imported.path, p.join(project.path, 'src', 'next_lesson.go'));
        expect(File(imported.path).readAsStringSync(), _code);
        for (final file in previous.entries) {
          expect(
            File(p.join(project.path, file.key)).readAsStringSync(),
            file.value,
          );
        }
        expect(registry.readAsStringSync(), registryBefore);
      },
    );
  });

  for (final tutorials in [true, false]) {
    testWidgets(
      '${tutorials ? 'Tutorial' : 'Example'} list opens code only in detail',
      (tester) async {
        await tester.pumpWidget(
          _app(
            home: tutorials
                ? LocalTutorialsTab(
                    language: 'go',
                    repository: const _FixtureRepository(),
                    store: store,
                    auth: auth,
                    settings: settings,
                  )
                : ExampleCodeTab(
                    language: 'go',
                    repository: const _FixtureRepository(),
                    store: store,
                    auth: auth,
                    settings: settings,
                  ),
          ),
        );
        await tester.pumpAndSettle();
        expect(find.byType(ListTile), findsOneWidget);
        expect(find.byType(CodeSnippet), findsNothing);
        expect(find.text(_code), findsNothing);
        expect(find.byIcon(Icons.copy_outlined), findsNothing);
        expect(find.byIcon(_editorIcon), findsNothing);
        expect(find.byIcon(_projectIcon), findsNothing);
        expect(
          Theme.of(tester.element(find.byType(Scaffold))).useMaterial3,
          isTrue,
        );

        await tester.tap(find.byType(ListTile));
        await tester.pumpAndSettle();
        expect(find.byType(CodeSnippet), findsOneWidget);
        for (final icon in [Icons.copy_outlined, _editorIcon, _projectIcon]) {
          expect(find.byIcon(icon), findsOneWidget);
          expect(
            tester
                .widget<IconButton>(
                  find.ancestor(
                    of: find.byIcon(icon),
                    matching: find.byType(IconButton),
                  ),
                )
                .onPressed,
            isNotNull,
          );
        }
        if (tutorials) {
          expect(find.text(_code), findsOneWidget);
        } else {
          expect(
            tester.widget<TextField>(find.byType(TextField)).controller!.text,
            _code,
          );
          await tester.enterText(find.byType(TextField), _editedCode);
        }
        await tester.tap(find.byIcon(Icons.copy_outlined));
        await tester.pumpAndSettle();
        expect(clipboard, tutorials ? _code : _editedCode);

        for (final icon in [_editorIcon, _projectIcon]) {
          await tester.tap(find.byIcon(icon));
          await tester.pumpAndSettle();
          expect(find.byType(AlertDialog), findsOneWidget);
          expect(
            tester
                .widget<TextFormField>(find.byKey(_fileNameKey))
                .controller!
                .text,
            'main.go',
          );
          await tester.tap(find.text('Cancel'));
          await tester.pumpAndSettle();
        }
        expect(store.projects, isEmpty);
        expect(_filesUnder(temporary), isEmpty);
        await _unmount(tester);
      },
    );
  }

  for (final icon in [_editorIcon, _projectIcon]) {
    testWidgets(
      '${icon == _editorIcon ? 'Editor' : 'Project'} dialog rejects invalid names and cancels without writes',
      (tester) async {
        final filesBefore = _filesUnder(temporary);
        final scratchBefore = _filesUnder(scratchStorage);
        await tester.pumpWidget(
          _app(
            home: ExampleDetailPage(
              example: _example,
              store: store,
              auth: auth,
              settings: settings,
            ),
          ),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.byIcon(icon));
        await tester.pumpAndSettle();
        await tester.enterText(find.byKey(_fileNameKey), '../outside.go');
        await tester.tap(find.text('Import and open'));
        await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsOneWidget);
        expect(find.byType(EditorPage), findsNothing);
        expect(find.textContaining('valid file name'), findsOneWidget);
        expect(store.projects, isEmpty);
        expect(_filesUnder(temporary), filesBefore);
        expect(_filesUnder(scratchStorage), scratchBefore);
        await tester.enterText(find.byKey(_fileNameKey), 'cancelled_lesson.go');
        await tester.tap(find.text('Cancel'));
        await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsNothing);
        expect(_filesUnder(temporary), filesBefore);
        expect(_filesUnder(scratchStorage), scratchBefore);
        await _unmount(tester);
      },
    );
  }

  testWidgets(
    'existing-project import selects the new file after restoring old tabs',
    (tester) async {
      final result = await tester.runAsync(
        () => store.createProject(
          name: 'Existing workspace',
          location: temporary.path,
          template: ProjectTemplate.go,
        ),
      );
      final project = result!.project!;
      final remembered = await tester.runAsync(
        () => store.createProject(
          name: 'Previously browsed workspace',
          location: temporary.path,
        ),
      );
      await tester.runAsync(() async {
        store.setBrowsedProject(remembered!.project!);
        await store.refresh();
      });
      expect(store.lastBrowsedProjectId, remembered!.project!.id);
      final oldEntry = File(p.join(project.path, 'src', 'main.go'));
      final previousCode = oldEntry.readAsStringSync();
      await tester.runAsync(
        () => ProjectHistory.save(
          project.path,
          cursors: const {},
          openFiles: const ['src/main.go'],
          activeFile: 'src/main.go',
        ),
      );
      await tester.pumpWidget(
        _app(
          home: ExampleDetailPage(
            example: _example,
            store: store,
            auth: auth,
            settings: settings,
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField), _editedCode);
      await tester.tap(find.byIcon(_projectIcon));
      await tester.pumpAndSettle();
      await _selectProject(tester, project.name);
      await tester.enterText(find.byKey(_fileNameKey), 'imported_lesson.go');
      await tester.tap(find.text('Import and open'));
      await _pumpUntil(
        tester,
        () => _activeTabIs(tester, 'imported_lesson.go'),
      );
      final editor = tester.widget<EditorPage>(find.byType(EditorPage));
      final importedPath = p.join(project.path, 'src', 'imported_lesson.go');
      expect(editor.project.id, project.id);
      expect(editor.initialOpenPath, importedPath);
      expect(File(importedPath).readAsStringSync(), _editedCode);
      expect(oldEntry.readAsStringSync(), previousCode);
      expect(
        find.descendant(
          of: find.byType(TabBar),
          matching: find.text('main.go'),
        ),
        findsOneWidget,
      );
      expect(store.projects, hasLength(2));
      expect(store.lastBrowsedProjectId, project.id);
      expect(
        find.descendant(
          of: find.byType(FileExplorer),
          matching: find.text('Existing workspace'),
        ),
        findsWidgets,
      );
      expect(
        find.descendant(
          of: find.byType(FileExplorer),
          matching: find.text('Previously browsed workspace'),
        ),
        findsNothing,
      );
      await _unmount(tester);
      final session = await ProjectHistory.load(project.path);
      expect(
        session.openFiles,
        containsAll(['src/main.go', 'src/imported_lesson.go']),
      );
      expect(session.activeFile, 'src/imported_lesson.go');
    },
  );

  testWidgets(
    'new-project dialog uses custom entry and opens the registered project',
    (tester) async {
      await tester.pumpWidget(
        _app(
          home: ExampleDetailPage(
            example: _example,
            store: store,
            auth: auth,
            settings: settings,
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(_projectIcon));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(_projectNameKey),
        'Named learning project',
      );
      await tester.enterText(find.byKey(_fileNameKey), 'custom_start.go');
      await tester.tap(find.text('Import and open'));
      await _pumpUntil(tester, () => _activeTabIs(tester, 'custom_start.go'));
      final editor = tester.widget<EditorPage>(find.byType(EditorPage));
      expect(editor.project.name, 'Named learning project');
      expect(
        editor.initialOpenPath,
        p.join(editor.project.path, 'src', 'custom_start.go'),
      );
      expect(File(editor.initialOpenPath!).readAsStringSync(), _code);
      expect(
        File(p.join(editor.project.path, 'src', 'main.go')).existsSync(),
        isFalse,
      );
      expect(store.projects.single.id, editor.project.id);
      await _refreshProjects(tester, store);
      final reloaded = ProjectStore(storageFile: registry);
      await tester.runAsync(reloaded.load);
      expect(reloaded.projects.single.id, editor.project.id);
      reloaded.dispose();
      await _unmount(tester);
    },
  );

  testWidgets('file conflict stays in the dialog and imports after renaming', (
    tester,
  ) async {
    final result = await tester.runAsync(
      () => store.createProject(
        name: 'Existing workspace',
        location: temporary.path,
        template: ProjectTemplate.go,
      ),
    );
    final project = result!.project!;
    final occupied = File(p.join(project.path, 'src', 'main.go'));
    final previousCode = occupied.readAsStringSync();
    await tester.pumpWidget(
      _app(
        home: ExampleDetailPage(
          example: _example,
          store: store,
          auth: auth,
          settings: settings,
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(_projectIcon));
    await tester.pumpAndSettle();
    await _selectProject(tester, project.name);
    await tester.tap(find.text('Import and open'));
    await _pumpUntil(tester, () => find.text('Replace').evaluate().isNotEmpty);
    expect(find.byType(AlertDialog), findsNWidgets(2));
    expect(find.byType(EditorPage), findsNothing);
    expect(occupied.readAsStringSync(), previousCode);
    expect(store.projects, hasLength(1));
    await tester.tap(find.text('Cancel').last);
    await tester.pumpAndSettle();
    expect(find.byType(AlertDialog), findsOneWidget);
    expect(occupied.readAsStringSync(), previousCode);
    expect(find.byType(EditorPage), findsNothing);
    await tester.enterText(find.byKey(_fileNameKey), 'renamed_lesson.go');
    await tester.tap(find.text('Import and open'));
    await _pumpUntil(tester, () => _activeTabIs(tester, 'renamed_lesson.go'));
    expect(
      File(p.join(project.path, 'src', 'renamed_lesson.go')).readAsStringSync(),
      _code,
    );
    expect(occupied.readAsStringSync(), previousCode);
    expect(find.byType(AlertDialog), findsNothing);
    await _unmount(tester);
  });

  testWidgets(
    'confirmed replacement writes edited code and opens the existing filename',
    (tester) async {
      final result = await tester.runAsync(
        () => store.createProject(
          name: 'Replace workspace',
          location: temporary.path,
          template: ProjectTemplate.go,
        ),
      );
      final project = result!.project!;
      final occupied = File(p.join(project.path, 'src', 'main.go'));
      final original = _filesUnder(Directory(project.path));
      await tester.pumpWidget(
        _app(
          home: ExampleDetailPage(
            example: _example,
            store: store,
            auth: auth,
            settings: settings,
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField), _editedCode);
      await tester.tap(find.byIcon(_projectIcon));
      await tester.pumpAndSettle();
      await _selectProject(tester, project.name);
      await tester.tap(find.text('Import and open'));
      await _pumpUntil(
        tester,
        () => find.text('Replace').evaluate().isNotEmpty,
      );
      expect(occupied.readAsStringSync(), original[p.join('src', 'main.go')]);
      await tester.tap(find.text('Replace'));
      await _pumpUntil(tester, () => _activeTabIs(tester, 'main.go'));
      final editor = tester.widget<EditorPage>(find.byType(EditorPage));
      expect(editor.project.id, project.id);
      expect(editor.initialOpenPath, occupied.path);
      expect(occupied.readAsStringSync(), _editedCode);
      expect(store.projects.single.id, project.id);
      for (final file in original.entries) {
        if (file.key == p.join('src', 'main.go')) continue;
        expect(
          File(p.join(project.path, file.key)).readAsStringSync(),
          file.value,
        );
      }
      await _unmount(tester);
    },
  );

  testWidgets(
    'editor command opens a writable independent workspace that can be reopened',
    (tester) async {
      final storage = await tester.runAsync(AppPaths.storageDirectory);
      expect(storage, scratchStorage.path);
      await tester.pumpWidget(
        _app(
          home: ExampleDetailPage(
            example: _example,
            store: store,
            auth: auth,
            settings: settings,
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(_editorIcon));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(_fileNameKey), 'my_scratch.go');
      await tester.tap(find.text('Import and open'));
      await _pumpUntil(tester, () => _activeTabIs(tester, 'my_scratch.go'));
      final editor = tester.widget<EditorPage>(find.byType(EditorPage));
      expect(p.isWithin(scratchStorage.path, editor.project.path), isTrue);
      expect(p.basename(editor.initialOpenPath!), 'my_scratch.go');
      expect(File(editor.initialOpenPath!).readAsStringSync(), _code);
      expect(store.projects.single.id, editor.project.id);
      expect(store.lastBrowsedProjectId, editor.project.id);
      await _refreshProjects(tester, store);
      final reloaded = ProjectStore(storageFile: registry);
      await tester.runAsync(reloaded.load);
      expect(reloaded.projects.single.id, editor.project.id);
      expect(reloaded.projects.single.path, editor.project.path);
      reloaded.dispose();
      await _unmount(tester);
    },
  );

  for (final viewport in [
    (name: 'phone', size: const Size(360, 800), scale: 1.0, dark: false),
    (name: 'desktop', size: const Size(1280, 900), scale: 1.0, dark: false),
    (name: 'large-text', size: const Size(360, 800), scale: 2.0, dark: false),
    (name: 'dark-phone', size: const Size(360, 800), scale: 1.0, dark: true),
  ]) {
    testWidgets('render actual Go content at ${viewport.name}', (tester) async {
      await tester.binding.setSurfaceSize(viewport.size);
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final repository = AssetContentRepository();
      await tester.runAsync(repository.load);
      final boundary = GlobalKey();
      Widget frame(Widget page) => _app(
        home: page,
        boundary: boundary,
        textScale: viewport.scale,
        dark: viewport.dark,
      );

      await tester.pumpWidget(
        frame(
          LocalTutorialsTab(
            language: 'go',
            repository: repository,
            store: store,
            auth: auth,
            settings: settings,
          ),
        ),
      );
      await _pumpUntil(
        tester,
        () => find.byType(ListTile).evaluate().isNotEmpty,
      );
      await tester.pumpAndSettle();
      expect(find.byType(ListTile), findsWidgets);
      expect(find.byType(CodeSnippet), findsNothing);
      await _capture(tester, boundary, '${viewport.name}-tutorials');
      await tester.tap(find.byType(ListTile).first);
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.byIcon(Icons.copy_outlined),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();
      _expectCodeActionsFit(tester, viewport.size.width);
      await _capture(tester, boundary, '${viewport.name}-lesson');

      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpWidget(
        frame(
          ExampleCodeTab(
            language: 'go',
            repository: repository,
            store: store,
            auth: auth,
            settings: settings,
          ),
        ),
      );
      await _pumpUntil(
        tester,
        () => find.byType(ListTile).evaluate().isNotEmpty,
      );
      await tester.pumpAndSettle();
      expect(find.byType(ListTile), findsWidgets);
      expect(find.byType(CodeSnippet), findsNothing);
      await _capture(tester, boundary, '${viewport.name}-examples');
      await tester.tap(find.byType(ListTile).first);
      await tester.pumpAndSettle();
      _expectCodeActionsFit(tester, viewport.size.width);
      await _capture(tester, boundary, '${viewport.name}-example');

      for (final action in [
        (icon: _editorIcon, label: 'editor-dialog'),
        (icon: _projectIcon, label: 'project-dialog'),
      ]) {
        await tester.ensureVisible(find.byIcon(action.icon));
        await tester.tap(find.byIcon(action.icon));
        await tester.pumpAndSettle();
        expect(find.byKey(_fileNameKey), findsOneWidget);
        final dialog = tester.getRect(find.byType(AlertDialog));
        expect(dialog.left, greaterThanOrEqualTo(0));
        expect(dialog.right, lessThanOrEqualTo(viewport.size.width));
        expect(dialog.bottom, lessThanOrEqualTo(viewport.size.height));
        await _capture(tester, boundary, '${viewport.name}-${action.label}');
        await tester.ensureVisible(find.text('Cancel'));
        await tester.tap(find.text('Cancel'));
        await tester.pumpAndSettle();
      }
      expect(tester.takeException(), isNull);
      await _unmount(tester);
    });
  }
}

Widget _app({
  required Widget home,
  GlobalKey? boundary,
  double textScale = 1,
  bool dark = false,
}) {
  ThemeData renderedTheme(ThemeData theme) => theme.copyWith(
    textTheme: theme.textTheme.apply(fontFamilyFallback: const ['ContentCjk']),
  );
  final app = MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: renderedTheme(AppTheme.light),
    darkTheme: renderedTheme(AppTheme.dark),
    themeMode: dark ? ThemeMode.dark : ThemeMode.light,
    locale: const Locale('en'),
    supportedLocales: StudioLocalizations.supportedLocales,
    localizationsDelegates: const [StudioLocalizations.delegate],
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(
        context,
      ).copyWith(textScaler: TextScaler.linear(textScale)),
      child: child!,
    ),
    home: home,
  );
  return boundary == null ? app : RepaintBoundary(key: boundary, child: app);
}

Matcher _failure(CodeImportFailure reason) => isA<CodeImportException>().having(
  (error) => error.reason,
  'reason',
  reason,
);

Map<String, String> _filesUnder(Directory directory) => {
  for (final file in directory.listSync(recursive: true, followLinks: false))
    if (file is File)
      p.relative(file.path, from: directory.path): file.readAsStringSync(),
};

Future<void> _selectProject(WidgetTester tester, String name) async {
  await tester.tap(find.byType(DropdownButtonFormField<String>));
  await tester.pumpAndSettle();
  await tester.tap(find.text(name).last);
  await tester.pumpAndSettle();
  expect(find.byKey(_projectNameKey), findsNothing);
}

bool _activeTabIs(WidgetTester tester, String name) {
  final bars = find.byType(TabBar);
  if (bars.evaluate().isEmpty) return false;
  final bar = tester.widget<TabBar>(bars);
  final controller = bar.controller;
  if (controller == null || controller.index >= bar.tabs.length) return false;
  return find
      .descendant(
        of: find.byWidget(bar.tabs[controller.index]),
        matching: find.text(name),
      )
      .evaluate()
      .isNotEmpty;
}

Future<void> _refreshProjects(WidgetTester tester, ProjectStore store) async {
  // Queued registry writes originated in the fake clock; keep pumping it
  // while allowing filesystem and isolate callbacks to finish.
  var completed = false;
  final refresh = store.refresh().whenComplete(() => completed = true);
  await _pumpUntil(tester, () => completed);
  await refresh;
}

Future<void> _pumpUntil(WidgetTester tester, bool Function() completed) async {
  for (var frame = 0; frame < 100; frame++) {
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 20)),
    );
    await tester.pump(const Duration(milliseconds: 50));
    if (completed()) {
      await _drainIo(tester);
      expect(tester.takeException(), isNull);
      return;
    }
  }
  fail('The import did not reach its expected editor or error state.');
}

Future<void> _unmount(WidgetTester tester) async {
  await tester.pumpWidget(const SizedBox.shrink());
  await _drainIo(tester);
}

Future<void> _drainIo(WidgetTester tester) async {
  // Saving history yields at multiple file operations during editor disposal.
  for (var step = 0; step < 12; step++) {
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 20)),
    );
    await tester.pump(const Duration(milliseconds: 50));
  }
}

void _expectCodeActionsFit(WidgetTester tester, double width) {
  Rect? previous;
  for (final icon in [Icons.copy_outlined, _editorIcon, _projectIcon]) {
    final button = find.ancestor(
      of: find.byIcon(icon),
      matching: find.byType(IconButton),
    );
    expect(button, findsOneWidget);
    final bounds = tester.getRect(button);
    expect(bounds.left, greaterThanOrEqualTo(0));
    expect(bounds.right, lessThanOrEqualTo(width));
    expect(bounds.width, greaterThanOrEqualTo(48));
    expect(bounds.height, greaterThanOrEqualTo(48));
    if (previous != null) expect(previous.overlaps(bounds), isFalse);
    previous = bounds;
  }
}

Future<void> _capture(WidgetTester tester, GlobalKey key, String name) async {
  expect(tester.takeException(), isNull);
  await tester.pump();
  final boundary =
      key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
  await tester.runAsync(() async {
    final image = await boundary.toImage(pixelRatio: 1);
    final rgba = await image.toByteData(format: ui.ImageByteFormat.rawRgba);
    expect(rgba, isNotNull);
    final colors = <int>{};
    for (var offset = 0; offset < rgba!.lengthInBytes; offset += 256) {
      colors.add(rgba.getUint32(offset));
    }
    expect(
      colors.length,
      greaterThan(8),
      reason: '$name must contain rendered content',
    );
    final png = await image.toByteData(format: ui.ImageByteFormat.png);
    final file = File(
      p.join(
        Directory.current.path,
        '.artifacts',
        'content-import',
        'screenshots',
        'content-tests',
        '$name.png',
      ),
    );
    await file.parent.create(recursive: true);
    await file.writeAsBytes(png!.buffer.asUint8List(), flush: true);
    image.dispose();
  });
}

Future<void> _loadRenderFonts() async {
  // Real fonts keep render artifacts readable instead of Flutter's test Ahem font.
  for (final font in [
    (family: 'Roboto', path: 'C:/Windows/Fonts/segoeui.ttf'),
    (family: 'ContentCjk', path: 'C:/Windows/Fonts/msyh.ttc'),
  ]) {
    final file = File(font.path);
    if (file.existsSync()) {
      await (FontLoader(font.family)..addFont(
            Future.value(ByteData.sublistView(file.readAsBytesSync())),
          ))
          .load();
    }
  }
  await (FontLoader(
    'MaterialIcons',
  )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
  await (FontLoader(EditorFonts.bundledFamily)..addFont(
        rootBundle.load(
          'packages/qfli_studio_core/assets/fonts/roboto_mono/static/RobotoMono-Regular.ttf',
        ),
      ))
      .load();
}

class _RedirectedProjectStore extends ProjectStore {
  _RedirectedProjectStore({required File registry, required this.location})
    : super(storageFile: registry);

  final String location;

  @override
  Future<ProjectResult> createProjectFromExample({
    required String name,
    required ExampleCode example,
    String? location,
    String? fileName,
  }) => super.createProjectFromExample(
    name: name,
    example: example,
    location: location ?? this.location,
    fileName: fileName,
  );
}

class _FixtureRepository implements ContentRepository {
  const _FixtureRepository();

  static const _catalog = ContentCatalog(
    schemaVersion: 1,
    tutorials: [
      TutorialContent(
        id: 'go-import-tutorial',
        language: 'go',
        type: 'go',
        locale: 'en',
        level: 'beginner',
        title: 'Go output',
        summary: 'Print a message.',
        concepts: ['output'],
        source: 'test fixture',
        license: 'test fixture',
        updatedAt: '2026-10-01',
        lessons: [
          TutorialLessonContent(
            id: 'go-import-lesson',
            title: 'Print a message',
            summary: 'Write a message to standard output.',
            concepts: ['output'],
            explain: 'Use fmt.Println to write a line.',
            code: _code,
            output: 'imported lesson',
            exercises: [],
          ),
        ],
      ),
    ],
    examples: [
      ExampleContent(
        id: 'go-import-example',
        language: 'go',
        type: 'go',
        locale: 'en',
        level: 'beginner',
        title: 'Print a message',
        summary: 'Write a message to standard output.',
        concepts: ['output'],
        source: 'test fixture',
        license: 'test fixture',
        updatedAt: '2026-10-01',
        code: _code,
        expectedOutput: 'imported lesson',
        inputFixtures: {},
        templateType: 'go',
      ),
    ],
  );

  @override
  Future<ContentCatalog> load() async => _catalog;

  @override
  Future<List<TutorialContent>> tutorials({
    ContentFilter filter = const ContentFilter(),
  }) async => [
    for (final tutorial in _catalog.tutorials)
      if (filter.matches(tutorial)) tutorial,
  ];

  @override
  Future<List<ExampleContent>> examples({
    ContentFilter filter = const ContentFilter(),
  }) async => [
    for (final example in _catalog.examples)
      if (filter.matches(example)) example,
  ];
}
