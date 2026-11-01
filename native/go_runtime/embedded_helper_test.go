package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func helperSourceLine(t *testing.T, source, marker string) int {
	t.Helper()
	for index, line := range strings.Split(source, "\n") {
		if strings.Contains(line, marker) {
			return index + 1
		}
	}
	t.Fatalf("missing source marker %q", marker)
	return 0
}

func TestEmbeddedHelperSourceAttribution(t *testing.T) {
	for _, item := range []struct{ name, body, marker string }{
		{"unmarked", `func assertion(t *testing.T) {
 t.Error("source evidence") // expected
}
func TestCaller(t *testing.T) { assertion(t) }`, "// expected"},
		{"nested", `func assertion(t *testing.T) {
 t.Helper()
 t.Fatalf("source %s", "evidence")
}
func outer(t *testing.T) { t.Helper(); assertion(t) }
func TestCaller(t *testing.T) { outer(t) } // expected`, "// expected"},
		{"method-value", `func assertion(t *testing.T, report func(string, ...any)) {
 helper := t.Helper
 helper()
 report("source %s", "evidence")
}
func TestCaller(t *testing.T) {
 report := t.Errorf
 assertion(t, report) // expected
}`, "// expected"},
		{"variadic", `func assertion(t *testing.T) {
 t.Helper()
 args := []any{"source ", "evidence"}
 t.Error(args...)
}
func TestCaller(t *testing.T) { assertion(t) } // expected`, "// expected"},
		{"method-expression", `func assertion(t *testing.T) {
 (*testing.T).Helper(t)
 (*testing.T).Errorf(t, "source %s", "evidence")
}
func TestCaller(t *testing.T) { assertion(t) } // expected`, "// expected"},
		{"deferred-method-value", `func assertion(t *testing.T) {
 t.Helper()
 report := t.Errorf
 defer report("source %s", []any{"evidence"}...)
}
func TestCaller(t *testing.T) { assertion(t) } // expected`, "// expected"},
		{"deferred-anonymous", `func TestCaller(t *testing.T) {
 defer func() { t.Helper(); t.Error("source evidence") }() // expected
}`, "// expected"},
		{"anonymous", `func invoke(body func()) { body() } // expected
func TestCaller(t *testing.T) {
 invoke(func(){ t.Helper(); t.Error("source evidence") })
}`, "// expected"},
		{"subtest", `func assertion(t *testing.T) { t.Helper(); t.Error("source evidence") }
func TestCaller(t *testing.T) {
 t.Run("child", func(child *testing.T) {
  assertion(child) // expected
 })
}`, "// expected"},
		{"interface", `type reporter interface { Helper(); Errorf(string, ...any) }
func assertion(t reporter) { t.Helper(); t.Errorf("source %s", "evidence") }
func TestCaller(t *testing.T) { assertion(t) } // expected`, "// expected"},
	} {
		t.Run(item.name, func(t *testing.T) {
			source := "package caller\nimport \"testing\"\n" + item.body + "\n"
			project := t.TempDir()
			entry := filepath.Join(project, "调用位置_test.go")
			writeGoSource(t, entry, source)
			result := runGo(project, entry)
			wanted := fmt.Sprintf("调用位置_test.go:%d: source evidence", helperSourceLine(t, source, item.marker))
			if result.ExitCode != 1 || result.TestExecution == nil || result.TestExecution.TestsFailed != 1 || !strings.Contains(result.Stdout, wanted) {
				t.Fatalf("missing real failure at %q: %+v", wanted, result)
			}
		})
	}
}

func TestEmbeddedHelperRegistrationIsPerTest(t *testing.T) {
	source := `package caller
import "testing"
func assertion(t *testing.T, mark bool) {
 if mark { t.Helper() }
 t.Error("source evidence") // unmarked
}
func TestAMarked(t *testing.T) { assertion(t, true) } // marked
func TestBUnmarked(t *testing.T) { assertion(t, false) }
`
	project, entry := embeddedFixture(t, source)
	result := runGo(project, entry)
	for _, expected := range []struct{ test, marker string }{{"TestAMarked", "// marked"}, {"TestBUnmarked", "// unmarked"}} {
		wanted := fmt.Sprintf("%s: snippet_test.go:%d: source evidence", expected.test, helperSourceLine(t, source, expected.marker))
		if !strings.Contains(result.Stdout, wanted) {
			t.Fatalf("helper identity leaked between tests, missing %q: %+v", wanted, result)
		}
	}
	if result.ExitCode != 1 || result.TestExecution.TestsFailed != 2 {
		t.Fatalf("assertions did not fail: %+v", result)
	}
}

func TestEmbeddedHelperConcurrentCallers(t *testing.T) {
	source := `package caller
import ("testing"; "sync")
func marked(t *testing.T) { t.Helper(); t.Error("marked evidence") }
func ordinary(t *testing.T) { t.Error("ordinary evidence") } // ordinary
func TestConcurrent(t *testing.T) {
 var done sync.WaitGroup
 done.Add(2)
 go func(){ defer done.Done(); marked(t) }() // marked
 go func(){ defer done.Done(); ordinary(t) }()
 done.Wait()
}
`
	project, entry := embeddedFixture(t, source)
	result := runGo(project, entry)
	for _, message := range []string{"marked", "ordinary"} {
		wanted := fmt.Sprintf("snippet_test.go:%d: %s evidence", helperSourceLine(t, source, "// "+message), message)
		if !strings.Contains(result.Stdout, wanted) {
			t.Fatalf("concurrent source attribution crossed calls, missing %q: %+v", wanted, result)
		}
	}
	if result.ExitCode != 1 || result.TestExecution.TestsFailed != 1 {
		t.Fatalf("concurrent assertions did not fail: %+v", result)
	}
}

func TestEmbeddedHelperTestingFamilies(t *testing.T) {
	for _, family := range []struct{ typ, prefix string }{{"T", "Test"}, {"F", "Fuzz"}, {"B", "Benchmark"}} {
		for _, method := range []string{"Log", "Logf", "Error", "Errorf", "Fatal", "Fatalf", "Skip", "Skipf"} {
			t.Run(family.typ+"/"+method, func(t *testing.T) {
				arguments := `"family evidence"`
				if strings.HasSuffix(method, "f") {
					arguments = `"family %s", "evidence"`
				}
				source := fmt.Sprintf(`package caller
import "testing"
func assertion(t *testing.%s) { t.Helper(); t.%s(%s) }
func %sCaller(t *testing.%s) { assertion(t); t.SkipNow() } // expected
func TestHealthy(t *testing.T) {}
`, family.typ, method, arguments, family.prefix, family.typ)
				project, entry := embeddedFixture(t, source)
				result := runGo(project, entry)
				wanted := fmt.Sprintf("snippet_test.go:%d: family evidence", helperSourceLine(t, source, "// expected"))
				failed := strings.HasPrefix(method, "Error") || strings.HasPrefix(method, "Fatal")
				if !strings.Contains(result.Stdout, wanted) || result.TestExecution == nil || failed != (result.ExitCode == 1) {
					t.Fatalf("testing.%s.%s lost source or status, expected %q: %+v", family.typ, method, wanted, result)
				}
			})
		}
	}
}

func TestEmbeddedHelperOriginalT106Failure(t *testing.T) {
	data, err := os.ReadFile(filepath.Join("..", "..", "tool", "go_curriculum", "samples", "T106", "assert_test.go"))
	if err != nil {
		t.Fatal(err)
	}
	source := strings.Replace(string(data), `equalInt(t, ParseLen("go"), 2)`, `equalInt(t, ParseLen("go"), 3)`, 1)
	if source == string(data) {
		t.Fatal("T106 assertion fixture changed")
	}
	project, entry := embeddedFixture(t, source)
	result := runGo(project, entry)
	wanted := fmt.Sprintf("snippet_test.go:%d: got 2, want 3", helperSourceLine(t, source, `equalInt(t, ParseLen("go"), 3)`))
	if result.ExitCode != 1 || result.TestExecution == nil || result.TestExecution.TestsFailed != 1 || !strings.Contains(result.Stdout, wanted) {
		t.Fatalf("T106 teaching claim failed, wanted %q: %+v", wanted, result)
	}
}
