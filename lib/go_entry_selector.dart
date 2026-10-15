import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;

/// Lexical facts about one Go source file needed to choose a run entry.
class GoSourceFacts {
  const GoSourceFacts({
    required this.packageName,
    required this.hasTopLevelMain,
  });

  /// The package clause name, or `null` when no `package` clause was found.
  final String? packageName;

  /// Whether the file declares a receiver-free top-level `func main`.
  final bool hasTopLevelMain;

  /// A file is a runnable entry when it is package `main` with a top-level
  /// `func main`. A function named `main` in another package is not an entry.
  bool get isRunnableEntry => packageName == 'main' && hasTopLevelMain;
}

/// Selects the runnable Go entry among the files of one source directory.
///
/// Go's `go run .` compiles the whole directory package, so a directory that
/// holds two top-level `func main` files cannot be built. When the selected
/// entry is one of those competing mains, the runner excludes the others from
/// the compiler view with a `-overlay` map, keeping every helper, imported
/// subpackage, build constraint and asset in place. Ordinary packages without a
/// competing main keep the plain `go run .` command.
abstract final class GoEntrySelector {
  /// Scans [source] for its package clause and top-level `main` declaration.
  ///
  /// Comment-, string-, rune- and raw-literal-aware: names that merely appear
  /// inside a comment or a literal never count. Method receivers such as
  /// `func (r T) main()` and nested function literals never count.
  static GoSourceFacts inspect(String source) {
    final scanner = _GoScanner(source);
    String? packageName;
    var hasMain = false;
    while (scanner.moveNext()) {
      if (scanner.token != _TokenKind.ident) continue;
      if (scanner.braceDepth != 0) continue;
      if (scanner.word == 'package' && packageName == null) {
        packageName = scanner.peekIdentifierAfterFunc();
        continue;
      }
      if (scanner.word == 'func') {
        final name = scanner.peekIdentifierAfterFunc();
        if (name == 'main') hasMain = true;
      }
    }
    return GoSourceFacts(packageName: packageName, hasTopLevelMain: hasMain);
  }

  /// Returns the sibling `.go` files in [entryDirectory] that are competing
  /// runnable entries, excluding [entryFile] itself.
  ///
  /// Competing files are package `main` files with a top-level `func main`.
  /// Files that cannot be listed or read throw [FileSystemException] so the
  /// caller surfaces the real error instead of running an unfiltered package.
  /// An identifiable competing main is excluded even if its body is unfinished.
  /// Other files remain in the compiler view for normal filtering/diagnostics;
  /// this lexical scan does not validate Go syntax.
  static List<String> competingMainSiblings({
    required String entryDirectory,
    required String entryFile,
  }) {
    final entryPath = p.absolute(entryFile);
    final directory = Directory(entryDirectory);
    final siblings = <String>[];
    for (final entity in directory.listSync(followLinks: false)) {
      if (entity is! File && entity is! Link) continue;
      final name = p.basename(entity.path);
      if (p.equals(p.absolute(entity.path), entryPath)) continue;
      if (!name.endsWith('.go')) continue;
      if (name.startsWith('_') || name.startsWith('.')) continue;
      if (name.endsWith('_test.go')) continue;
      if (entity is Link &&
          FileSystemEntity.typeSync(entity.path) != FileSystemEntityType.file) {
        continue;
      }
      // Decode lossily only for discovery. The Go compiler still reads the
      // original bytes and diagnoses invalid UTF-8 in files it actually builds.
      final facts = inspect(
        File(
          entity.path,
        ).readAsStringSync(encoding: const Utf8Codec(allowMalformed: true)),
      );
      if (facts.isRunnableEntry) siblings.add(entity.path);
    }
    siblings.sort();
    return siblings;
  }

  /// Writes a Go `-overlay` JSON file mapping each path in [excluded] to an
  /// empty string, so the compiler treats those sources as absent.
  ///
  /// The file lives in [directory], which the caller owns and must remove after
  /// the run. Paths are written as absolute, slash-normalized strings.
  static File writeOverlay({
    required Directory directory,
    required List<String> excluded,
  }) {
    final replace = <String, String>{
      for (final path in excluded) _overlayPath(path): '',
    };
    final overlay = File(p.join(directory.path, 'overlay.json'));
    overlay.writeAsStringSync(jsonEncode({'Replace': replace}));
    return overlay;
  }

  static String _overlayPath(String path) =>
      p.absolute(path).replaceAll(r'\', '/');
}

enum _TokenKind { ident, other }

/// Minimal Go lexical scanner sufficient to find the package clause and
/// top-level `func main`.
///
/// It skips line comments, block comments, interpreted strings, raw strings and
/// rune literals, tracks brace depth outside those literals, and exposes the
/// identifier following a keyword so receivers and closures are ignored.
class _GoScanner {
  _GoScanner(this._source);

  final String _source;
  int _index = 0;

  int braceDepth = 0;
  _TokenKind token = _TokenKind.other;
  String word = '';

  bool moveNext() {
    while (_index < _source.length) {
      final char = _source.codeUnitAt(_index);
      if (_index == 0 && char == 0xfeff) {
        _index++;
        continue;
      }
      if (_isSpace(char)) {
        _index++;
        continue;
      }
      if (char == 0x2f && _peek(1) == 0x2f) {
        _skipLineComment();
        continue;
      }
      if (char == 0x2f && _peek(1) == 0x2a) {
        _skipBlockComment();
        continue;
      }
      if (char == 0x22) {
        _skipInterpretedString();
        continue;
      }
      if (char == 0x60) {
        _skipRawString();
        continue;
      }
      if (char == 0x27) {
        _skipRune();
        continue;
      }
      if (char == 0x7b) {
        braceDepth++;
        _advanceOther();
        continue;
      }
      if (char == 0x7d) {
        if (braceDepth > 0) braceDepth--;
        _advanceOther();
        continue;
      }
      if (_isIdentStart(char)) {
        _readIdentifier();
        token = _TokenKind.ident;
        return true;
      }
      _advanceOther();
    }
    return false;
  }

  /// Looks ahead from the current keyword for the declared name.
  ///
  /// Returns `null` for receiver methods (`func (r T) main`), for a keyword
  /// without a name and for `func` used as a type.
  String? peekIdentifierAfterFunc() {
    var cursor = _index;
    while (true) {
      while (cursor < _source.length && _isSpace(_source.codeUnitAt(cursor))) {
        cursor++;
      }
      if (cursor + 1 < _source.length &&
          _source.codeUnitAt(cursor) == 0x2f &&
          _source.codeUnitAt(cursor + 1) == 0x2f) {
        while (cursor < _source.length && _source.codeUnitAt(cursor) != 0x0a) {
          cursor++;
        }
        continue;
      }
      if (cursor + 1 < _source.length &&
          _source.codeUnitAt(cursor) == 0x2f &&
          _source.codeUnitAt(cursor + 1) == 0x2a) {
        cursor += 2;
        while (cursor + 1 < _source.length &&
            !(_source.codeUnitAt(cursor) == 0x2a &&
                _source.codeUnitAt(cursor + 1) == 0x2f)) {
          cursor++;
        }
        cursor += 2;
        continue;
      }
      break;
    }
    if (cursor >= _source.length) return null;
    // A receiver or an anonymous func starts with '('. A `func` used as a type
    // means no name follows either; both are not a top-level entry.
    if (_source.codeUnitAt(cursor) == 0x28) return null;
    if (!_isIdentStart(_source.codeUnitAt(cursor))) return null;
    final start = cursor;
    while (cursor < _source.length &&
        _isIdentPart(_source.codeUnitAt(cursor))) {
      cursor++;
    }
    return _source.substring(start, cursor);
  }

  int _peek(int offset) => _index + offset < _source.length
      ? _source.codeUnitAt(_index + offset)
      : -1;

  void _advanceOther() {
    _index++;
    token = _TokenKind.other;
    word = '';
  }

  void _readIdentifier() {
    final start = _index;
    while (_index < _source.length &&
        _isIdentPart(_source.codeUnitAt(_index))) {
      _index++;
    }
    word = _source.substring(start, _index);
  }

  void _skipLineComment() {
    while (_index < _source.length && _source.codeUnitAt(_index) != 0x0a) {
      _index++;
    }
  }

  void _skipBlockComment() {
    _index += 2;
    while (_index < _source.length && !(_peek(0) == 0x2a && _peek(1) == 0x2f)) {
      _index++;
    }
    if (_index < _source.length) _index += 2;
  }

  void _skipInterpretedString() {
    _index++;
    while (_index < _source.length) {
      final char = _source.codeUnitAt(_index);
      if (char == 0x5c) {
        _index += 2;
        continue;
      }
      if (char == 0x22) {
        _index++;
        return;
      }
      if (char == 0x0a) return; // Unterminated: stop at the line end.
      _index++;
    }
  }

  void _skipRawString() {
    _index++;
    while (_index < _source.length && _source.codeUnitAt(_index) != 0x60) {
      _index++;
    }
    if (_index < _source.length) _index++;
  }

  void _skipRune() {
    _index++;
    while (_index < _source.length) {
      final char = _source.codeUnitAt(_index);
      if (char == 0x5c) {
        _index += 2;
        continue;
      }
      if (char == 0x27) {
        _index++;
        return;
      }
      if (char == 0x0a) return;
      _index++;
    }
  }

  static bool _isSpace(int char) =>
      char == 0x20 || char == 0x09 || char == 0x0a || char == 0x0d;

  static bool _isIdentStart(int char) =>
      (char >= 0x41 && char <= 0x5a) ||
      (char >= 0x61 && char <= 0x7a) ||
      char == 0x5f ||
      char > 0x7f;

  static bool _isIdentPart(int char) =>
      _isIdentStart(char) || (char >= 0x30 && char <= 0x39);
}
