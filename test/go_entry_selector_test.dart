import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:qfli_go/go_entry_selector.dart';

void main() {
  group('inspect', () {
    GoSourceFacts inspect(String source) => GoEntrySelector.inspect(source);

    test('detects a package main entry', () {
      final facts = inspect('package main\nfunc main() { println("x") }\n');
      expect(facts.packageName, 'main');
      expect(facts.hasTopLevelMain, isTrue);
      expect(facts.isRunnableEntry, isTrue);
    });

    test('does not treat a main in another package as an entry', () {
      final facts = inspect('package tool\nfunc main() {}\n');
      expect(facts.packageName, 'tool');
      expect(facts.hasTopLevelMain, isTrue);
      expect(facts.isRunnableEntry, isFalse);
    });

    test('accepts the leading byte order mark permitted by Go', () {
      expect(
        inspect('\ufeffpackage main\nfunc main() {}\n').isRunnableEntry,
        isTrue,
      );
    });

    test('reads the package clause despite a leading comment', () {
      expect(
        inspect('// note\npackage main\nfunc main() {}\n').packageName,
        'main',
      );
    });

    test('ignores a main inside a line comment', () {
      final facts = inspect(
        'package main\n// func main() {}\nfunc helper() {}\n',
      );
      expect(facts.hasTopLevelMain, isFalse);
    });

    test('ignores a main inside a block comment', () {
      expect(
        inspect('package main\n/*\nfunc main() {}\n*/\n').hasTopLevelMain,
        isFalse,
      );
    });

    test('ignores a main inside an interpreted string', () {
      expect(
        inspect(
          'package main\nvar s = "func main() { println() }"\n',
        ).hasTopLevelMain,
        isFalse,
      );
    });

    test('ignores a main inside a raw string', () {
      expect(
        inspect('package main\nvar s = `func main() {}`\n').hasTopLevelMain,
        isFalse,
      );
    });

    test('ignores a main inside a rune literal', () {
      expect(inspect("package main\nvar r = 'm'\n").hasTopLevelMain, isFalse);
    });

    test('ignores a method named main', () {
      expect(
        inspect(
          'package main\ntype T struct{}\nfunc (t T) main() {}\n',
        ).hasTopLevelMain,
        isFalse,
      );
    });

    test('still sees the outer main around a nested literal', () {
      expect(
        inspect(
          'package main\nfunc main() {\n\tfunc main() {}\n}\n',
        ).hasTopLevelMain,
        isTrue,
      );
    });

    test('ignores func used as a type', () {
      expect(inspect('package main\nvar f func()\n').hasTopLevelMain, isFalse);
    });

    test('keeps a malformed source scannable for the compiler', () {
      // The lexer must not throw on invalid source; the compiler diagnoses it.
      final facts = inspect('package main\nfunc main() {\n');
      expect(facts.packageName, 'main');
      expect(facts.hasTopLevelMain, isTrue);
    });

    test('handles missing package clause without throwing', () {
      final facts = inspect('func main() {}\n');
      expect(facts.packageName, isNull);
      expect(facts.isRunnableEntry, isFalse);
    });
  });

  group('competingMainSiblings', () {
    late Directory project;

    setUp(() {
      project = Directory.systemTemp.createTempSync('qfli_go_selector_');
    });

    tearDown(() {
      if (project.existsSync()) project.deleteSync(recursive: true);
    });

    test(
      'returns the other package main entry and ignores helpers and tests',
      () {
        File(
          p.join(project.path, 'main.go'),
        ).writeAsStringSync('package main\nfunc main() {}\n');
        File(
          p.join(project.path, 'main2.go'),
        ).writeAsStringSync('package main\nfunc main() {}\n');
        File(
          p.join(project.path, 'helper.go'),
        ).writeAsStringSync('package main\nfunc helper() {}\n');
        File(
          p.join(project.path, 'helper_test.go'),
        ).writeAsStringSync('package main\nfunc TestX() {}\n');
        final competing = GoEntrySelector.competingMainSiblings(
          entryDirectory: project.path,
          entryFile: p.join(project.path, 'main.go'),
        );
        expect(competing, [p.join(project.path, 'main2.go')]);
      },
    );

    test('ignores a main declared in another package', () {
      File(
        p.join(project.path, 'main.go'),
      ).writeAsStringSync('package main\nfunc main() {}\n');
      File(
        p.join(project.path, 'tool.go'),
      ).writeAsStringSync('package tool\nfunc main() {}\n');
      expect(
        GoEntrySelector.competingMainSiblings(
          entryDirectory: project.path,
          entryFile: p.join(project.path, 'main.go'),
        ),
        isEmpty,
      );
    });

    test('leaves a malformed helper sibling in the compiler view', () {
      File(
        p.join(project.path, 'main.go'),
      ).writeAsStringSync('package main\nfunc main() {}\n');
      // A malformed sibling that declares no main is not a competing entry; the
      // compiler diagnoses it rather than it being silently hidden.
      File(
        p.join(project.path, 'broken.go'),
      ).writeAsStringSync('package main\nfunc helper(\n');
      expect(
        GoEntrySelector.competingMainSiblings(
          entryDirectory: project.path,
          entryFile: p.join(project.path, 'main.go'),
        ),
        isEmpty,
      );
    });

    test('returns empty for an ordinary single-entry directory', () {
      File(
        p.join(project.path, 'main.go'),
      ).writeAsStringSync('package main\nfunc main() {}\n');
      File(
        p.join(project.path, 'helper.go'),
      ).writeAsStringSync('package main\nfunc helper() {}\n');
      expect(
        GoEntrySelector.competingMainSiblings(
          entryDirectory: project.path,
          entryFile: p.join(project.path, 'main.go'),
        ),
        isEmpty,
      );
    });

    test(
      'keeps the selected Windows path despite different casing',
      () {
        File(
          p.join(project.path, 'main.go'),
        ).writeAsStringSync('package main\nfunc main() {}\n');
        expect(
          GoEntrySelector.competingMainSiblings(
            entryDirectory: project.path,
            entryFile: p.join(project.path, 'MAIN.GO'),
          ),
          isEmpty,
        );
      },
      skip: !Platform.isWindows,
    );

    test('uses the Go compiler case-sensitive source filename rules', () {
      File(
        p.join(project.path, 'main.go'),
      ).writeAsStringSync('package main\nfunc main() {}\n');
      final other = p.join(project.path, 'other_TEST.go');
      File(other).writeAsStringSync('package main\nfunc main() {}\n');
      expect(
        GoEntrySelector.competingMainSiblings(
          entryDirectory: project.path,
          entryFile: p.join(project.path, 'main.go'),
        ),
        [other],
      );
    });

    test('includes competing symlink files in the compiler view', () {
      final target = File(p.join(project.path, 'target.txt'))
        ..writeAsStringSync('package main\nfunc main() {}\n');
      final link = Link(p.join(project.path, 'other.go'));
      try {
        link.createSync(target.path);
      } on FileSystemException catch (error) {
        markTestSkipped('Symlinks unavailable: ${error.message}');
        return;
      }
      File(
        p.join(project.path, 'main.go'),
      ).writeAsStringSync('package main\nfunc main() {}\n');
      expect(
        GoEntrySelector.competingMainSiblings(
          entryDirectory: project.path,
          entryFile: p.join(project.path, 'main.go'),
        ),
        [link.path],
      );
    });

    test('throws when the directory cannot be listed', () {
      expect(
        () => GoEntrySelector.competingMainSiblings(
          entryDirectory: p.join(project.path, 'missing'),
          entryFile: p.join(project.path, 'missing', 'main.go'),
        ),
        throwsA(isA<FileSystemException>()),
      );
    });

    test('writes a valid exclusion overlay with jsonEncode', () {
      final path = p.join(project.path, 'main2.go');
      final overlay = GoEntrySelector.writeOverlay(
        directory: project,
        excluded: [path],
      );
      final decoded = jsonDecode(overlay.readAsStringSync()) as Map;
      final replace = decoded['Replace'] as Map;
      expect(replace[p.absolute(path).replaceAll(r'\', '/')], '');
    });
  });
}
