package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"testing"
	"unicode/utf16"
)

func utf16Count(source string) int { return len(utf16.Encode([]rune(source))) }

func TestGoAnalysisUsesSnapshotWithoutExecutionOrFileWrites(t *testing.T) {
	root := t.TempDir()
	filePath := filepath.Join(root, "main.go")
	marker := filepath.Join(root, "executed.txt")
	saved := []byte("saved source is intentionally invalid Go")
	if err := os.WriteFile(filePath, saved, 0600); err != nil {
		t.Fatal(err)
	}
	source := `package main
import "os"
var created = func() int { os.WriteFile(` + strconv.Quote(marker) + `, []byte("variable"), 0600); return 1 }()
func init() { os.WriteFile(` + strconv.Quote(marker) + `, []byte("init"), 0600) }
func main() { go os.WriteFile(` + strconv.Quote(marker) + `, []byte("main"), 0600) }
`
	for _, operation := range []struct {
		name string
		run  func(string, string) goSourceAnalysis
	}{{"analyze", analyzeGoSource}, {"format", formatGoSource}} {
		t.Run(operation.name, func(t *testing.T) {
			result := operation.run(filePath, source)
			if result.Error != "" || len(result.Diagnostics) != 0 || result.PackageName != "main" {
				t.Fatalf("unexpected snapshot analysis: %+v", result)
			}
			if _, err := os.Stat(marker); !os.IsNotExist(err) {
				t.Fatalf("source side effect occurred: %v", err)
			}
			actual, err := os.ReadFile(filePath)
			if err != nil || string(actual) != string(saved) {
				t.Fatalf("saved source changed: %q, %v", actual, err)
			}
		})
	}
	// A nonexistent import is an AST fact, not a request to resolve a package.
	result := analyzeGoSource(filepath.Join(root, "unsaved.go"), "package p\nimport \"not.installed.invalid/pkg\"\n")
	if result.Error != "" || len(result.Diagnostics) != 0 || len(result.Imports) != 1 {
		t.Fatalf("syntax analysis attempted import resolution: %+v", result)
	}
}

func TestGoAnalysisUTF16RangesWithCRLFUnicodeAndLineDirectives(t *testing.T) {
	for _, badToken := range []string{"@", "💥"} {
		source := "package main\r\n//line foreign.go:500\r\nvar 中文 = \"😀\"; var bad = " + badToken + "\r\n"
		result := analyzeGoSource("/project/main.go", source)
		if result.UTF16Length != utf16Count(source) || result.FilePath != "/project/main.go" {
			t.Fatalf("wrong source identity/length: %+v", result)
		}
		byteStart := strings.Index(source, badToken)
		wantStart := utf16Count(source[:byteStart])
		wantEnd := wantStart + utf16Count(badToken)
		found := false
		for _, diagnostic := range result.Diagnostics {
			if diagnostic.StartOffset == wantStart && diagnostic.EndOffset == wantEnd {
				found = true
			}
			if diagnostic.StartOffset < 0 || diagnostic.EndOffset < diagnostic.StartOffset || diagnostic.EndOffset > result.UTF16Length {
				t.Fatalf("out-of-bounds diagnostic: %+v", diagnostic)
			}
		}
		if !found {
			t.Fatalf("missing UTF-16 [%d, %d) for %s: %+v", wantStart, wantEnd, badToken, result.Diagnostics)
		}
	}
	source := "package main\r\nfunc main() {"
	result := analyzeGoSource("/project/main.go", source)
	foundEOF := false
	for _, diagnostic := range result.Diagnostics {
		if diagnostic.StartOffset == len(source) && diagnostic.EndOffset == len(source) {
			foundEOF = true
		}
	}
	if !foundEOF {
		t.Fatalf("EOF must be an insertion point: %+v", result.Diagnostics)
	}
}

func TestGoAnalysisASTImportsSymbolsAndUnicodeNames(t *testing.T) {
	source := "package sample\r\n" +
		"import ( f \"fmt\"; _ \"os\"; . `math` )\r\n" +
		"const 名称 = \"😀\"\r\nvar 一, 二 int\r\n" +
		"type 数据[T any] struct { Value T }\r\n" +
		"func (d *数据[T]) 方法() { local := 1; _ = local }\r\n" +
		"func main() {}\r\n"
	result := analyzeGoSource("/p/main.go", source)
	if result.Error != "" || len(result.Diagnostics) != 0 || result.PackageName != "sample" {
		t.Fatalf("unexpected analysis: %+v", result)
	}
	var imports []string
	for _, spec := range result.Imports {
		imports = append(imports, spec.Alias+":"+spec.Path)
	}
	if !reflect.DeepEqual(imports, []string{"f:fmt", "_:os", ".:math"}) {
		t.Fatalf("imports: %v", imports)
	}
	var symbols []string
	for _, symbol := range result.Symbols {
		symbols = append(symbols, symbol.Kind+":"+symbol.Receiver+":"+symbol.Name)
		byteStart := strings.Index(source, symbol.Name)
		if symbol.StartOffset != utf16Count(source[:byteStart]) || symbol.EndOffset != utf16Count(source[:byteStart+len(symbol.Name)]) {
			t.Fatalf("wrong symbol range: %+v", symbol)
		}
	}
	want := []string{"const::名称", "var::一", "var::二", "type::数据", "method:*数据[T]:方法", "function::main"}
	if !reflect.DeepEqual(symbols, want) {
		t.Fatalf("symbols: got %v, want %v", symbols, want)
	}
}

func TestGoFormatReturnsNewTextAndPreservesSyntaxErrors(t *testing.T) {
	result := formatGoSource("main.go", "package main\r\nfunc main(){println(\"中文😀\")}\r\n")
	if result.FormattedSource == nil || *result.FormattedSource != "package main\n\nfunc main() { println(\"中文😀\") }\n" {
		t.Fatalf("unexpected formatted source: %+v", result)
	}
	invalid := formatGoSource("main.go", "package main\nfunc main( {\n")
	if invalid.FormattedSource != nil || len(invalid.Diagnostics) == 0 {
		t.Fatalf("invalid source must retain parser errors: %+v", invalid)
	}
	encoded, err := json.Marshal(invalid)
	if err != nil || !strings.Contains(string(encoded), `"schemaVersion":1`) || !strings.Contains(string(encoded), `"imports":[]`) {
		t.Fatalf("invalid JSON boundary: %s, %v", encoded, err)
	}
}

func TestGoAnalysisInvalidUTF8AndByteBoundaries(t *testing.T) {
	source := "A😀中\r\n" + string([]byte{0xff})
	want := []int{0, 1, 1, 1, 1, 3, 3, 3, 4, 5, 6, 7}
	if actual := byteToUTF16(source); !reflect.DeepEqual(actual, want) {
		t.Fatalf("byte-to-UTF16: got %v, want %v", actual, want)
	}
	result := analyzeGoSource("main.go", "package main\nvar x = \""+string([]byte{0xff})+"\"\n")
	if len(result.Diagnostics) == 0 {
		t.Fatal("invalid UTF-8 must produce syntax diagnostics")
	}
	for _, diagnostic := range result.Diagnostics {
		if diagnostic.EndOffset > result.UTF16Length {
			t.Fatalf("invalid UTF-8 range: %+v", diagnostic)
		}
	}
}

func TestGoAnalysisSizeLimit(t *testing.T) {
	result := analyzeGoSource("main.go", strings.Repeat(" ", maxGoAnalysisBytes+1))
	if result.Error == "" {
		t.Fatal("oversized source must be unavailable, not reported as clean")
	}
}
