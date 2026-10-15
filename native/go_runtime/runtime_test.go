package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

func TestRunGoExcludesUnfinishedCompetingEntry(t *testing.T) {
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	writeGoSource(t, entry, "package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"selected\") }\n")
	writeGoSource(t, filepath.Join(project, "main2.go"), "package main\nfunc main() {\n")
	result := runGo(project, entry)
	if result.ExitCode != 0 || result.Stdout != "selected\n" {
		t.Fatalf("an identifiable competing entry was not excluded: %+v", result)
	}
}

func TestRunGoRejectsIgnoredEntry(t *testing.T) {
	otherOS := "windows"
	if runtime.GOOS == otherOS {
		otherOS = "linux"
	}
	for _, test := range []struct{ name, header string }{
		{"_selected.go", ""},
		{".selected.go", ""},
		{"selected_test.go", ""},
		{"selected_" + otherOS + ".go", ""},
		{"selected.go", "// +build qfli_never_enabled\n\n"},
	} {
		t.Run(test.name+test.header, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, test.name)
			writeGoSource(t, entry, test.header+"package main\nfunc main() { println(\"selected\") }\n")
			writeGoSource(t, filepath.Join(project, "main.go"), "package main\nfunc main() { println(\"other\") }\n")
			writeGoSource(t, filepath.Join(project, "helper.go"), "package main\nfunc helper() {}\n")
			result := runGo(project, entry)
			if result.ExitCode == 0 || result.ExitCode == 127 || result.Stderr == "" || result.Stdout != "" {
				t.Fatalf("an ignored entry reported successful execution: %+v", result)
			}
		})
	}
}

func TestRunGoRejectsModernBuildTaggedEntry(t *testing.T) {
	// The reported mobile defect: a selected file gated by the modern
	// `//go:build` syntax must be excluded by the interpreter's own build view,
	// exactly as the official Go compiler excludes it. Another main in the same
	// directory must not be run in its place, and the run must fail visibly.
	for _, header := range []string{
		"//go:build qfli_never_enabled\n\n",
		"//go:build qfli_never_enabled && !qfli_other\n\n",
		"//go:build (qfli_never_enabled || qfli_also_disabled) && !qfli_other\n\n",
	} {
		t.Run(header, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, "selected.go")
			writeGoSource(t, entry, header+"package main\nfunc main() { println(\"SELECTED\") }\n")
			writeGoSource(t, filepath.Join(project, "other.go"), "package main\nfunc main() { println(\"OTHER\") }\n")
			result := runGo(project, entry)
			if result.ExitCode == 0 {
				t.Fatalf("a modern build-tag-excluded entry executed successfully: %+v", result)
			}
			if strings.Contains(result.Stdout, "SELECTED") || strings.Contains(result.Stdout, "OTHER") {
				t.Fatalf("an excluded entry or its sibling main ran: %+v", result)
			}
			if result.Stderr == "" {
				t.Fatalf("an excluded entry produced no diagnostic: %+v", result)
			}
		})
	}
}

func TestRunGoExcludesModernTaggedHelper(t *testing.T) {
	// A helper gated by a never-enabled `//go:build` tag must stay out of the
	// interpreter's package view. The selected main references its symbol, so a
	// leaked helper would print OK while the real build fails; the run must
	// surface the undefined-symbol diagnostic instead.
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	writeGoSource(t, entry, "package main\nfunc main() { println(hiddenHelper()) }\n")
	writeGoSource(t, filepath.Join(project, "helper.go"),
		"//go:build qfli_never_enabled\n\npackage main\nfunc hiddenHelper() string { return \"LEAKED\" }\n")
	result := runGo(project, entry)
	if result.ExitCode == 0 || strings.Contains(result.Stdout, "LEAKED") {
		t.Fatalf("a modern build-tag-excluded helper leaked into the package: %+v", result)
	}
	if !strings.Contains(result.Stderr, "hiddenHelper") {
		t.Fatalf("the excluded helper did not produce an undefined-symbol diagnostic: %+v", result)
	}
}

func TestRunGoExcludesModernTaggedImportedSource(t *testing.T) {
	// The build filter also runs for imported subpackage sources. A file gated
	// by a false `//go:build` expression must stay out of an imported package's
	// view, so the selected main sees the real undefined-symbol diagnostic
	// instead of a leaked symbol.
	project := t.TempDir()
	source := filepath.Join(project, "src")
	pkg := filepath.Join(source, "localpkg")
	if err := os.MkdirAll(pkg, 0755); err != nil {
		t.Fatal(err)
	}
	writeGoSource(t, filepath.Join(pkg, "visible.go"),
		"package localpkg\nfunc Visible() string { return \"visible\" }\n")
	writeGoSource(t, filepath.Join(pkg, "hidden.go"),
		"//go:build qfli_never_enabled\n\npackage localpkg\nfunc Hidden() string { return \"HIDDEN\" }\n")
	entry := filepath.Join(source, "main.go")
	writeGoSource(t, entry,
		"package main\nimport (\"fmt\"; \"qfli-project/src/localpkg\")\n"+
			"func main() { fmt.Println(localpkg.Visible(), localpkg.Hidden()) }\n")
	result := runGo(project, entry)
	if result.ExitCode == 0 || strings.Contains(result.Stdout, "HIDDEN") {
		t.Fatalf("a modern build-tag-excluded imported source leaked: %+v", result)
	}
	if !strings.Contains(result.Stderr, "Hidden") {
		t.Fatalf("the excluded import did not produce an undefined-symbol diagnostic: %+v", result)
	}
}

func TestRunGoAcceptsEnabledModernBuildTag(t *testing.T) {
	// A satisfied `//go:build` expression must still include the source, so the
	// new parser cannot over-exclude valid modern files.
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	writeGoSource(t, entry,
		"//go:build "+runtime.GOOS+" || qfli_other\n\npackage main\nimport \"fmt\"\nfunc main() { fmt.Println(\"enabled\") }\n")
	result := runGo(project, entry)
	if result.ExitCode != 0 || result.Stdout != "enabled\n" {
		t.Fatalf("a satisfied modern build tag excluded the entry: %+v", result)
	}
}

func TestRunGoAcceptsLegacyPlusBuildTag(t *testing.T) {
	// The legacy `// +build` syntax keeps its semantics, including the OR of
	// space options and the AND of comma options.
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	writeGoSource(t, entry,
		"// +build qfli_never_enabled,"+runtime.GOOS+" "+runtime.GOOS+"\n\npackage main\nimport \"fmt\"\nfunc main() { fmt.Println(\"legacy\") }\n")
	result := runGo(project, entry)
	if result.ExitCode != 0 || result.Stdout != "legacy\n" {
		t.Fatalf("a satisfied legacy build tag excluded the entry: %+v", result)
	}
}

func TestRunGoPrefersModernBuildExpression(t *testing.T) {
	// When both syntaxes are present, the `//go:build` expression is
	// authoritative. A satisfied expression must include the file; the legacy
	// mirror line is parsed but must not override the expression.
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	writeGoSource(t, entry,
		"//go:build "+runtime.GOOS+"\n// +build "+runtime.GOOS+"\n\npackage main\nimport \"fmt\"\nfunc main() { fmt.Println(\"modern\") }\n")
	result := runGo(project, entry)
	if result.ExitCode != 0 || result.Stdout != "modern\n" {
		t.Fatalf("a consistent modern+legacy pair excluded the entry: %+v", result)
	}
}

func TestRunGoReportsInvalidBuildExpression(t *testing.T) {
	// An unparsable `//go:build` expression is a real diagnostic, not a silent
	// inclusion or exclusion.
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	writeGoSource(t, entry, "//go:build &&\n\npackage main\nfunc main() { println(\"SELECTED\") }\n")
	result := runGo(project, entry)
	if result.ExitCode == 0 || strings.Contains(result.Stdout, "SELECTED") {
		t.Fatalf("an invalid build expression executed: %+v", result)
	}
	if !strings.Contains(result.Stderr, "unexpected token") {
		t.Fatalf("an invalid build expression produced no build diagnostic: %+v", result)
	}
}

func TestRunGoRejectsMultipleModernBuildDirectives(t *testing.T) {
	for _, test := range []struct{ name, firstTag string }{
		{"enabled first", runtime.GOOS},
		{"disabled first", "qfli_never_enabled"},
	} {
		t.Run(test.name, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, "main.go")
			writeGoSource(t, entry,
				"//go:build "+test.firstTag+"\n//go:build "+runtime.GOOS+
					"\n\npackage main\nfunc main() { println(\"SELECTED\") }\n")
			result := runGo(project, entry)
			if result.ExitCode != 1 || result.Stdout != "" ||
				!strings.Contains(result.Stderr, "multiple //go:build comments") {
				t.Fatalf("duplicate build directives did not produce a diagnostic: %+v", result)
			}
		})
	}
}

func TestRunGoIgnoresBuildDirectiveTextInBlockComments(t *testing.T) {
	block := "/*\n//go:build qfli_never_enabled\n// +build qfli_never_enabled\n*/\n\n"
	for _, test := range []struct{ name, header string }{
		{"block only", block},
		{"block and enabled directive", block + "//go:build " + runtime.GOOS + "\n\n"},
	} {
		t.Run(test.name, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, "main.go")
			writeGoSource(t, entry,
				test.header+"package main\nfunc main() { println(\"SELECTED\") }\n")
			result := runGo(project, entry)
			if result.ExitCode != 0 || result.Stdout != "SELECTED\n" {
				t.Fatalf("directive text in a block comment changed the build: %+v", result)
			}
		})
	}
}

func TestRunGoWindowsEntryCase(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("case-insensitive Windows paths")
	}
	project := t.TempDir()
	writeGoSource(t, filepath.Join(project, "main.go"), "package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"selected\") }\n")
	writeGoSource(t, filepath.Join(project, "main2.go"), "package main\nfunc main() {}\n")
	result := runGo(project, filepath.Join(project, "MAIN.GO"))
	if result.ExitCode != 0 || result.Stdout != "selected\n" {
		t.Fatalf("the selected entry was excluded because of path casing: %+v", result)
	}
}

func TestRunGoSelectedEntryInSpacedDirectory(t *testing.T) {
	project := t.TempDir()
	source := filepath.Join(project, "Go 示例")
	if err := os.Mkdir(source, 0755); err != nil {
		t.Fatal(err)
	}
	entry := filepath.Join(source, "main.go")
	writeGoSource(t, entry, "package main\nimport \"fmt\"\nfunc init() { fmt.Println(\"init\") }; func main() { fmt.Println(\"selected\") }\n")
	result := runGo(project, entry)
	if result.ExitCode != 0 || result.Stdout != "init\nselected\n" {
		t.Fatalf("entry reference check repeated code or rejected its directory: %+v", result)
	}
}

func TestRunGoKeepsHelperDiagnostics(t *testing.T) {
	for _, code := range []string{
		"package main\nfunc helper(\n",
		"package main\nfunc helper() { missingHelperSymbol() }\n",
	} {
		project := t.TempDir()
		entry := filepath.Join(project, "main.go")
		writeGoSource(t, entry, "package main\nfunc main() {}\n")
		writeGoSource(t, filepath.Join(project, "main2.go"), "package main\nfunc main() {\n")
		writeGoSource(t, filepath.Join(project, "helper.go"), code)
		result := runGo(project, entry)
		if result.ExitCode != 1 || result.Stdout != "" || !strings.Contains(result.Stderr, "helper.go") {
			t.Fatalf("helper diagnostic was hidden: %+v", result)
		}
	}
}

func TestCompetingMainFilesReadError(t *testing.T) {
	if _, err := competingMainFiles(filepath.Join(t.TempDir(), "missing"), "main.go"); err == nil {
		t.Fatal("a directory read failure was swallowed")
	}
}

func writeGoSource(t *testing.T, path, source string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(source), 0644); err != nil {
		t.Fatal(err)
	}
}

func TestRunGoSelectsEntryWithSiblingMain(t *testing.T) {
	project := t.TempDir()
	source := filepath.Join(project, "src")
	if err := os.MkdirAll(source, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(source, "localpkg"), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, "localpkg", "pkg.go"), []byte("package localpkg\nfunc Name() string { return \"pkg\" }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, "helper.go"), []byte("package main\nfunc message() string { return \"helper\" }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	mainSrc := "package main\nimport (\"fmt\"; \"qfli-project/src/localpkg\")\nfunc main() { fmt.Println(\"%s\", message(), localpkg.Name()) }\n"
	mainEntry := filepath.Join(source, "main.go")
	main2Entry := filepath.Join(source, "main2.go")
	if err := os.WriteFile(mainEntry, []byte(fmt.Sprintf(mainSrc, "main")), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(main2Entry, []byte(fmt.Sprintf(mainSrc, "main2")), 0644); err != nil {
		t.Fatal(err)
	}

	result := runGo(project, mainEntry)
	if result.ExitCode != 0 || result.Stdout != "main helper pkg\n" {
		t.Fatalf("selecting main.go failed: %+v", result)
	}

	result = runGo(project, main2Entry)
	if result.ExitCode != 0 || result.Stdout != "main2 helper pkg\n" {
		t.Fatalf("selecting main2.go failed: %+v", result)
	}

	result = runGo(project, mainEntry)
	if result.ExitCode != 0 || result.Stdout != "main helper pkg\n" {
		t.Fatalf("re-selecting main.go failed: %+v", result)
	}
}

func TestRunGoRejectsEntryWithoutMain(t *testing.T) {
	project := t.TempDir()
	source := filepath.Join(project, "src")
	if err := os.MkdirAll(source, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, "main.go"), []byte("package main\nfunc main() { println(\"main\") }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	helper := filepath.Join(source, "helper.go")
	if err := os.WriteFile(helper, []byte("package main\nfunc message() string { return \"helper\" }\n"), 0644); err != nil {
		t.Fatal(err)
	}

	result := runGo(project, helper)
	if result.ExitCode == 0 || !strings.Contains(result.Stderr, "no main function") {
		t.Fatalf("helper entry was not rejected: %+v", result)
	}
	if strings.Contains(result.Stdout, "main") {
		t.Fatalf("helper entry executed another main: %+v", result)
	}
}

func TestRunGoRejectsNonMainPackageEntry(t *testing.T) {
	project := t.TempDir()
	source := filepath.Join(project, "src")
	if err := os.MkdirAll(source, 0755); err != nil {
		t.Fatal(err)
	}
	tool := filepath.Join(source, "tool.go")
	if err := os.WriteFile(tool, []byte("package tool\nfunc main() {}\n"), 0644); err != nil {
		t.Fatal(err)
	}
	result := runGo(project, tool)
	if result.ExitCode == 0 || !strings.Contains(result.Stderr, "no main function") {
		t.Fatalf("non-main package entry was not rejected: %+v", result)
	}
}

func TestRunGoSurfacesParseErrorBeforeNoMain(t *testing.T) {
	project := t.TempDir()
	source := filepath.Join(project, "src")
	if err := os.MkdirAll(source, 0755); err != nil {
		t.Fatal(err)
	}
	entry := filepath.Join(source, "main.go")
	if err := os.WriteFile(entry, []byte("package main\nfunc main() {\n"), 0644); err != nil {
		t.Fatal(err)
	}
	result := runGo(project, entry)
	if result.ExitCode == 0 {
		t.Fatalf("malformed source was accepted: %+v", result)
	}
	if strings.Contains(result.Stderr, "no main function") {
		t.Fatalf("parse error was masked by a no-main diagnostic: %+v", result)
	}
}

func TestRunGoKeepsCompilerDiagnostics(t *testing.T) {
	project := t.TempDir()
	source := filepath.Join(project, "src")
	if err := os.MkdirAll(source, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, "main.go"), []byte("package main\nfunc main() { missingSymbol() }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, "main2.go"), []byte("package main\nfunc main() { println(\"main2\") }\n"), 0644); err != nil {
		t.Fatal(err)
	}

	result := runGo(project, filepath.Join(source, "main.go"))
	if result.ExitCode == 0 || !strings.Contains(result.Stderr, "missingSymbol") {
		t.Fatalf("compiler diagnostic was lost: %+v", result)
	}
}

func TestRunGoMultiFile(t *testing.T) {
	project := t.TempDir()
	source := filepath.Join(project, "src")
	if err := os.Mkdir(source, 0755); err != nil {
		t.Fatal(err)
	}
	entry := filepath.Join(source, "main.go")
	if err := os.WriteFile(entry, []byte("package main\nimport \"fmt\"\nfunc main() { fmt.Println(message()) }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, "helper.go"), []byte("package main\nfunc message() string { return \"ready\" }\n"), 0644); err != nil {
		t.Fatal(err)
	}

	result := runGo(project, entry)
	if result.ExitCode != 0 || result.Stdout != "ready\n" {
		t.Fatalf("unexpected result: %+v", result)
	}

	if err := os.WriteFile(entry, []byte("package main\nfunc main() { unknown() }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	result = runGo(project, entry)
	if result.ExitCode == 0 || !strings.Contains(result.Stderr, "unknown") {
		t.Fatalf("invalid program did not fail: %+v", result)
	}
}

func TestRunGoRejectsOutsideEntry(t *testing.T) {
	result := runGo(t.TempDir(), filepath.Join(t.TempDir(), "main.go"))
	if result.ExitCode != 127 {
		t.Fatalf("outside entry was accepted: %+v", result)
	}
}

func TestRunGoCanBeCancelled(t *testing.T) {
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	if err := os.WriteFile(entry, []byte("package main\nfunc main() { for {} }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	result := runGoWithContext(ctx, project, entry)
	if result.ExitCode == 0 || !strings.Contains(result.Stderr, "canceled") {
		t.Fatalf("cancelled program did not stop: %+v", result)
	}
}

func TestRunGoHandlesProgramPanic(t *testing.T) {
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	if err := os.WriteFile(entry, []byte("package main\nfunc main() { panic(\"boom\") }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	result := runGo(project, entry)
	if result.ExitCode == 0 || !strings.Contains(result.Stderr, "boom") {
		t.Fatalf("program panic was not reported: %+v", result)
	}
}

func TestRunGoHandlesOsExit(t *testing.T) {
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	if err := os.WriteFile(entry, []byte("package main\nimport \"os\"\nfunc main() { os.Exit(2) }\n"), 0644); err != nil {
		t.Fatal(err)
	}
	result := runGo(project, entry)
	if result.ExitCode == 0 || !strings.Contains(result.Stderr, "os.Exit(2)") {
		t.Fatalf("os.Exit was not reported: %+v", result)
	}
}

func TestRunGoHandlesGoroutinePanic(t *testing.T) {
	for _, test := range []struct {
		name, source, errorText string
	}{
		{"interpreted function", "package main\nfunc fail() { panic(\"worker boom\") }; func main() { go fail(); select {} }\n", "worker boom"},
		{"stdlib function", "package main\nimport \"log\"\nfunc main() { go log.Panic(\"worker boom\"); select {} }\n", "worker boom"},
		{"os.Exit", "package main\nimport \"os\"\nfunc main() { go os.Exit(2); select {} }\n", "os.Exit(2)"},
	} {
		t.Run(test.name, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, "main.go")
			if err := os.WriteFile(entry, []byte(test.source), 0644); err != nil {
				t.Fatal(err)
			}
			result := runGo(project, entry)
			if result.ExitCode == 0 || !strings.Contains(result.Stderr, test.errorText) {
				t.Fatalf("goroutine panic was not reported: %+v", result)
			}
		})
	}
}

func TestRunGoCancelsRunningProgram(t *testing.T) {
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	source := "package main\nimport (\"fmt\"; \"time\")\nfunc main() { fmt.Println(\"started\"); for { fmt.Println(\"tick\"); time.Sleep(time.Millisecond) } }\n"
	if err := os.WriteFile(entry, []byte(source), 0644); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	result := runGoWithContext(ctx, project, entry)
	if result.ExitCode == 0 || !strings.Contains(result.Stderr, "deadline exceeded") || !strings.HasPrefix(result.Stdout, "started\n") {
		t.Fatalf("running program did not cancel correctly: %+v", result)
	}
}

func TestRunGoConcurrentOutput(t *testing.T) {
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	source := "package main\nimport (\"fmt\"; \"sync\")\nfunc main() { var wg sync.WaitGroup; for i := 0; i < 8; i++ { wg.Add(1); go func() { defer wg.Done(); for j := 0; j < 100; j++ { fmt.Println(\"line\") } }() }; wg.Wait() }\n"
	if err := os.WriteFile(entry, []byte(source), 0644); err != nil {
		t.Fatal(err)
	}
	result := runGo(project, entry)
	if result.ExitCode != 0 || strings.Count(result.Stdout, "line\n") != 800 {
		t.Fatalf("concurrent output was lost: %+v", result)
	}
}
