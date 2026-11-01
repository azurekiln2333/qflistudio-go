import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_tools.dart';
import 'package:qfli_studio_core/models/project.dart';
import 'package:qfli_studio_core/store/project_store.dart';

void main() {
  group('JSON to Go struct', () {
    test('merges all object samples, nullable fields and numeric arrays', () {
      final generated = GoJsonStruct.generate('''{
        "user_id": 7,
        "samples": [1, 2.5, 3],
        "items": [{"name":"first", "enabled":true}, {"name":null, "score":2}],
        "metadata": {}, "empty": [], "mixed": [false, "yes"]
      }''', typeName: 'Response');
      expect(generated.source, contains('type Response struct {'));
      expect(generated.source, contains('UserID int64 `json:"user_id"`'));
      expect(generated.source, contains('Samples []float64'));
      expect(generated.source, contains('Items []struct {'));
      expect(generated.source, contains('Name *string'));
      expect(generated.source, contains('Enabled *bool'));
      expect(generated.source, contains('Score *int64'));
      expect(generated.source, contains('Metadata map[string]any'));
      expect(generated.source, contains('Mixed []any'));
      expect(generated.notes, isNotEmpty);
    });

    test('keeps keys and generates distinct exported identifiers', () {
      final generated = GoJsonStruct.generate(
        '''{"a-b":1,"a_b":2,"9lives":true,"中文":"ok","url":"local"}''',
      );
      expect(generated.source, contains('AB int64 `json:"a-b"`'));
      expect(generated.source, contains('AB2 int64 `json:"a_b"`'));
      expect(generated.source, contains('Field9lives bool'));
      expect(generated.source, contains('Field string `json:"中文"`'));
      expect(generated.source, contains('URL string'));
    });

    test('rejects invalid input and keys that would change JSON meaning', () {
      for (final input in [
        '{',
        '[]',
        'null',
        '{"":1}',
        '{"-":1}',
        '{"x,y":1}',
        '{"x\\\\y":1}',
        '{"emoji😀":1}',
        '{"zero\u200bwidth":1}',
      ]) {
        expect(
          () => GoJsonStruct.generate(input),
          throwsFormatException,
          reason: input,
        );
      }
      expect(
        () => GoJsonStruct.generate('{}', typeName: 'private'),
        throwsFormatException,
      );
      expect(
        () => GoJsonStruct.generate('{}', typeName: 'X; import'),
        throwsFormatException,
      );
      expect(
        () => GoJsonStruct.generate('${'{"child":' * 42}null${'}' * 42}'),
        throwsFormatException,
      );
    });

    test(
      'generated types compile and round-trip with the official SDK',
      () async {
        final executable = Platform.environment['QFLI_GO_TEST_EXECUTABLE'];
        if (executable == null) return;
        final temporary = Directory.systemTemp.createTempSync(
          'go_struct_test_',
        );
        addTearDown(() => temporary.deleteSync(recursive: true));
        const input =
            '{"user_id":7,"items":[{"name":"one","count":2},{"name":null,"active":true}],"samples":[1,2.5]}';
        final generated = GoJsonStruct.generate(input);
        final file = File(p.join(temporary.path, 'main.go'));
        await file.writeAsString('''package main
import ("encoding/json"; "fmt")
${generated.source}
func main() {
  var value Payload
  if err := json.Unmarshal([]byte(${jsonEncode(input)}), &value); err != nil { panic(err) }
  if value.UserID != 7 || value.Items[0].Name == nil || *value.Items[0].Name != "one" || value.Items[1].Active == nil || !*value.Items[1].Active { panic("incorrect fields") }
  encoded, err := json.Marshal(value); if err != nil { panic(err) }; fmt.Println(string(encoded))
}
''');
        final result = await Process.run(
          executable,
          ['run', file.path],
          workingDirectory: temporary.path,
          environment: {
            'GOTOOLCHAIN': 'local',
            'GOPROXY': 'off',
            'GOSUMDB': 'off',
            'GOFLAGS': '-p=1',
            'GOMAXPROCS': '2',
          },
        );
        expect(result.exitCode, 0, reason: '${result.stderr}');
        final output =
            jsonDecode((result.stdout as String).trim())
                as Map<String, dynamic>;
        expect(output['user_id'], 7);
        expect((output['items'] as List)[1]['active'], true);
      },
      skip: Platform.environment['QFLI_GO_TEST_EXECUTABLE'] == null
          ? 'Set QFLI_GO_TEST_EXECUTABLE to run the real SDK round-trip'
          : false,
    );
  });

  group('Go module metadata', () {
    test(
      'reads comments, blocks, quoted replacements and other directives',
      () {
        final manifest = GoModuleManifest.parse('''module example.local/app
go 1.23
toolchain go1.23.2
require (
  example.local/a v1.2.0 // indirect
  "example.local/b" v2.0.0
)
replace (
  example.local/a => "./local dir"
  example.local/b v2.0.0 => example.local/fork v2.1.0
)
exclude example.local/c v1.0.0
''');
        expect(manifest.module, 'example.local/app');
        expect(manifest.goVersion, '1.23');
        expect(manifest.toolchain, 'go1.23.2');
        expect(manifest.requirements.first.indirect, isTrue);
        expect(manifest.replacements.first.target, './local dir');
        expect(manifest.replacements.last.targetVersion, 'v2.1.0');
        expect(manifest.otherDirectives, ['exclude example.local/c v1.0.0']);
      },
    );

    test('does not accept malformed or truncated metadata', () {
      for (final input in [
        'require a v1.0.0',
        'module a\nrequire (\na v1.0.0',
        'module a\nrequire a',
        'module a\nreplace a b',
        'module "a',
        'module a\n)',
      ]) {
        expect(
          () => GoModuleManifest.parse(input),
          throwsFormatException,
          reason: input,
        );
      }
    });
  });

  group('local project tools', () {
    late Directory temporary;
    late Project project;
    late GoTools tools;
    setUp(() {
      temporary = Directory.systemTemp.createTempSync('go_tools_');
      project = Project.create(
        name: 'Go app',
        path: temporary.path,
        language: 'Go',
        type: 'go',
      );
      tools = GoTools();
    });
    tearDown(() => temporary.deleteSync(recursive: true));

    test('uses browsed project, excludes cloud and other languages', () {
      final second = Project.create(
        name: 'second',
        path: temporary.path,
        type: 'go',
      );
      final store = _MemoryStore([
        project,
        second,
        Project.create(
          name: 'Python',
          path: temporary.path,
          language: 'Python',
        ),
        Project.create(
          name: 'cloud',
          path: temporary.path,
          type: 'go',
          cloudId: 'cloud',
        ),
      ]);
      addTearDown(store.dispose);
      store.lastBrowsedProjectId = second.id;
      expect(GoTools.currentProject(store), same(second));
      expect(GoTools.localProjects(store), [project, second]);
    });

    test(
      'enumerates only local source and does not write edited files',
      () async {
        for (final path in [
          'src/main.go',
          'src/helper.go',
          'vendor/dep/a.go',
          '.git/hooks/b.go',
          'notes.txt',
        ]) {
          final file = File(p.join(temporary.path, path));
          file.parent.createSync(recursive: true);
          file.writeAsStringSync('package main\n');
        }
        expect(await tools.sourceFiles(project), [
          p.join('src', 'helper.go'),
          p.join('src', 'main.go'),
        ]);
        expect(
          await tools.readSource(project, p.join('src', 'main.go')),
          'package main\n',
        );
        await expectLater(
          tools.readSource(project, '../outside.go'),
          throwsFormatException,
        );
        await expectLater(
          tools.readSource(project, 'notes.txt'),
          throwsFormatException,
        );
        expect(
          File(p.join(temporary.path, 'src/main.go')).readAsStringSync(),
          'package main\n',
        );
      },
    );

    test('reports actual vendoring and local replacement state', () async {
      File(p.join(temporary.path, 'go.mod')).writeAsStringSync(
        '''module app.local/demo
go 1.23
require (
  dep.local/vendor v1.0.0
  dep.local/local v1.1.0
  dep.local/missing v1.2.0
  dep.local/outside v1.3.0
)
replace dep.local/local => ./lib
replace dep.local/outside => ../other
''',
      );
      Directory(p.join(temporary.path, 'vendor')).createSync();
      File(p.join(temporary.path, 'vendor/modules.txt')).writeAsStringSync(
        '# dep.local/vendor v1.0.0\n## explicit; go 1.23\ndep.local/vendor/pkg\n',
      );
      Directory(p.join(temporary.path, 'lib')).createSync();
      File(
        p.join(temporary.path, 'lib/go.mod'),
      ).writeAsStringSync('module dep.local/local\n');
      final report = await tools.inspectModule(project);
      expect(report.dependencies[0].status, contains('vendor 清单有记录'));
      expect(report.dependencies[1].status, contains('存在 go.mod'));
      expect(report.dependencies[2].status, contains('未在 vendor'));
      expect(report.dependencies[3].status, contains('项目外'));
      expect(report.text, contains('不下载依赖'));
    });

    test('missing manifests and oversized files fail explicitly', () async {
      await expectLater(tools.inspectModule(project), throwsFormatException);
      File(
        p.join(temporary.path, 'large.go'),
      ).writeAsStringSync('x' * (GoTools.maxFileBytes + 1));
      await expectLater(
        tools.readSource(project, 'large.go'),
        throwsFormatException,
      );
    });

    test(
      'source actions preserve backend result and unsupported state',
      () async {
        final unavailable = await tools.format('package main', 'a.go');
        expect(unavailable.unavailableReason, isNotEmpty);
        final wired = GoTools(
          formatter: (source, file) async =>
              GoToolSourceResult(formattedSource: '$source\n', report: file),
        );
        final result = await wired.format('package main', 'edited.go');
        expect(result.formattedSource, 'package main\n');
        expect(result.report, 'edited.go');
      },
    );
  });
}

class _MemoryStore extends ProjectStore {
  _MemoryStore(this.items);
  final List<Project> items;
  @override
  List<Project> get projects => items;
}
