package main

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func embeddedFixture(t *testing.T, source string) (string, string) {
	t.Helper()
	project := t.TempDir()
	entry := filepath.Join(project, "snippet_test.go")
	writeGoSource(t, entry, source)
	return project, entry
}

func TestEmbeddedTestingOriginalCurriculum(t *testing.T) {
	for _, item := range []struct {
		id, file                string
		tests, benchmarks, fuzz int
	}{
		{"T080", "pool_test.go", 2, 2, 0},
		{"T104", "timeout_test.go", 2, 0, 0},
		{"T105", "calc_test.go", 1, 0, 0},
		{"T106", "assert_test.go", 1, 0, 0},
		{"T107", "fixture_test.go", 2, 0, 0},
		{"T108", "bench_test.go", 1, 2, 0},
		{"T110", "fuzz_test.go", 2, 0, 4},
		{"T119", "freq_test.go", 2, 0, 0},
	} {
		t.Run(item.id, func(t *testing.T) {
			source, err := os.ReadFile(filepath.Join("..", "..", "tool", "go_curriculum", "samples", item.id, item.file))
			if err != nil {
				t.Fatal(err)
			}
			project, entry := embeddedFixture(t, string(source))
			support, err := filepath.Glob(filepath.Join("..", "..", "tool", "go_curriculum", "samples", item.id, "*.go"))
			if err != nil {
				t.Fatal(err)
			}
			for _, file := range support {
				if filepath.Base(file) == item.file {
					continue
				}
				data, err := os.ReadFile(file)
				if err != nil {
					t.Fatal(err)
				}
				writeGoSource(t, filepath.Join(project, filepath.Base(file)), string(data))
			}
			ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
			defer cancel()
			result := runGoWithContext(ctx, project, entry)
			if result.ExitCode != 0 || result.Stderr != "" || result.TestExecution == nil {
				t.Fatalf("original curriculum did not actually execute: %+v", result)
			}
			proof := result.TestExecution
			if proof.Engine != "qfli-embedded-testing-v1" || proof.TestsRun != item.tests || proof.TestsPassed != item.tests || proof.TestsFailed != 0 || proof.BenchmarksRun != item.benchmarks || proof.FuzzSeedsRun != item.fuzz {
				t.Fatalf("wrong execution proof: %+v; output %s", proof, result.Stdout)
			}
			if !strings.HasSuffix(result.Stdout, "PASS\n") || !strings.Contains(result.Stdout, "--- PASS: Test") {
				t.Fatalf("missing actual test transcript: %s", result.Stdout)
			}
			if item.benchmarks > 0 && !strings.Contains(result.Stdout, "ns/op") {
				t.Fatalf("missing real benchmark measurements: %s", result.Stdout)
			}
		})
	}
}

func TestEmbeddedTestingFailuresFatalCleanupAndSubtests(t *testing.T) {
	project, entry := embeddedFixture(t, `package checks
import ("os"; "testing")
var order string
var temporary string
func TestAFatal(t *testing.T) {
 temporary = t.TempDir()
 defer func(){ order += "defer;" }()
 t.Cleanup(func(){ order += "last;"; t.Fatal("cleanup fatal") })
 t.Cleanup(func(){ order += "first;" })
 t.Fatal("expected fatal assertion")
 order += "unreachable;"
}
func TestBSubtests(t *testing.T) {
 if t.Run("failure", func(t *testing.T){ t.Error("subtest assertion") }) { t.Fatal("failed child reported success") }
 t.Run("success", func(t *testing.T){})
}
func TestZCleanup(t *testing.T) {
 if order != "defer;first;last;" { t.Fatalf("cleanup order = %q", order) }
 if _, err := os.Stat(temporary); !os.IsNotExist(err) { t.Fatalf("TempDir remains: %v", err) }
}
`)
	result := runGo(project, entry)
	if result.ExitCode != 1 || result.TestExecution == nil || result.TestExecution.TestsRun != 3 || result.TestExecution.TestsFailed != 2 || result.TestExecution.TestsPassed != 1 {
		t.Fatalf("failure/Fatal/cleanup semantics incorrect: %+v", result)
	}
	for _, text := range []string{"expected fatal assertion", "cleanup fatal", "--- FAIL: TestBSubtests/failure", "--- PASS: TestZCleanup"} {
		if !strings.Contains(result.Stdout, text) {
			t.Fatalf("missing %q in %s", text, result.Stdout)
		}
	}
}

func TestEmbeddedTestingPanicsAndNoExecutionCannotPass(t *testing.T) {
	for _, item := range []struct{ name, source, diagnostic string }{
		{"panic", `func TestPanic(t *testing.T){ panic("test panic") }`, "test panic"},
		{"skip", `func TestSkip(t *testing.T){ t.Skip("not applicable") }`, "no non-skipped"},
		{"empty", `func helper(){}`, "no non-skipped"},
		{"parallel", `func TestParallel(t *testing.T){ t.Parallel() }`, "unsupported"},
		{"fuzz-empty", `func FuzzEmpty(f *testing.F){ f.Fuzz(func(t *testing.T, x string){}) }`, "requires f.Add"},
		{"fuzz-bad", `func FuzzBad(f *testing.F){ f.Add("x"); f.Fuzz(func(t *testing.T, x string){t.Fatal("seed fails")}) }`, "seed fails"},
		{"fuzz-skip", `func FuzzSkip(f *testing.F){ f.Add("x"); f.Fuzz(func(t *testing.T, x string){t.Skip("skip seed")}) }`, "no non-skipped"},
		{"benchmark-panic", `func BenchmarkPanic(b *testing.B){panic("benchmark panic")}`, "benchmark panic"},
		{"benchmark-cleanup-panic", `func BenchmarkCleanupPanic(b *testing.B){b.Cleanup(func(){panic("benchmark cleanup panic")})}`, "benchmark cleanup panic"},
		{"parallel-benchmark-panic", `func BenchmarkParallelPanic(b *testing.B){b.RunParallel(func(pb *testing.PB){panic("parallel benchmark panic")})}`, "parallel benchmark panic"},
	} {
		t.Run(item.name, func(t *testing.T) {
			source := "package checks\nimport \"testing\"\n" + item.source
			if item.name == "empty" {
				source = "package checks\n" + item.source
			}
			project, entry := embeddedFixture(t, source)
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			result := runGoWithContext(ctx, project, entry)
			if result.ExitCode != 1 || !strings.Contains(result.Stdout+result.Stderr, item.diagnostic) {
				t.Fatalf("invalid test execution reported success or lost error: %+v", result)
			}
		})
	}
}

func TestEmbeddedTestingSkippedBenchmarks(t *testing.T) {
	for _, item := range []struct {
		name, source string
		passed       int
		exitCode     int
	}{
		{"only-skip", `func BenchmarkSkipped(b *testing.B) { b.Skip("not applicable") }`, 0, 1},
		{"test-and-skip", `func BenchmarkSkipped(b *testing.B) { b.Skip("not applicable") }
func TestHealthy(t *testing.T) {}`, 1, 0},
		{"fail-then-skip", `func BenchmarkSkipped(b *testing.B) { b.Error("failed before skip"); b.Skip("not applicable") }
func TestHealthy(t *testing.T) {}`, 0, 1},
	} {
		t.Run(item.name, func(t *testing.T) {
			project, entry := embeddedFixture(t, "package checks\nimport \"testing\"\n"+item.source)
			result := runGo(project, entry)
			if result.ExitCode != item.exitCode || result.TestExecution == nil || result.TestExecution.BenchmarksRun != 1 || result.TestExecution.TestsPassed != item.passed {
				t.Fatalf("benchmark skip state incorrect: %+v", result)
			}
			if item.name == "fail-then-skip" {
				if !strings.Contains(result.Stdout, "failed before skip") || strings.Contains(result.Stdout, "--- SKIP: BenchmarkSkipped") {
					t.Fatalf("failed benchmark was reported as skipped: %+v", result)
				}
				return
			}
			if !strings.Contains(result.Stdout, "--- SKIP: BenchmarkSkipped") || strings.Contains(result.Stdout+result.Stderr, "did not complete any benchmark iterations") {
				t.Fatalf("skipped benchmark was reported as a failed measurement: %+v", result)
			}
			if item.name == "only-skip" && !strings.Contains(result.Stderr, "no non-skipped") {
				t.Fatalf("skipped-only suite pretended to execute successfully: %+v", result)
			}
		})
	}
}

func TestEmbeddedTestingCancelsInitializersAndTests(t *testing.T) {
	for _, source := range []string{
		"package checks\nimport \"testing\"\nfunc init(){ for {} }; func TestNever(t *testing.T){t.Fatal(\"must not run\")}\n",
		"package checks\nimport \"testing\"\nfunc TestLoop(t *testing.T){for {}; t.Fatal(\"must not finish\")}\n",
		"package checks\nimport \"testing\"\nfunc TestWorkerPanic(t *testing.T){go func(){panic(\"worker panic\")}(); for {}}\n",
	} {
		project, entry := embeddedFixture(t, source)
		ctx, cancel := context.WithTimeout(context.Background(), 75*time.Millisecond)
		started := time.Now()
		result := runGoWithContext(ctx, project, entry)
		cancel()
		if result.ExitCode != 1 || time.Since(started) > 2*time.Second {
			t.Fatalf("test/initializer cancellation or worker panic escaped: %+v", result)
		}
		if !strings.Contains(result.Stderr+result.Stdout, "deadline") && !strings.Contains(result.Stderr+result.Stdout, "worker panic") {
			t.Fatalf("cancellation diagnostic missing: %+v", result)
		}
		if strings.Contains(source, "TestWorkerPanic") && (result.TestExecution == nil || result.TestExecution.TestsFailed != 1 || result.TestExecution.TestsPassed != 0) {
			t.Fatalf("worker panic was falsely counted as a passed test: %+v", result)
		}
	}
}

func TestEmbeddedTestingEvidenceJSONAndPreCancellation(t *testing.T) {
	project, entry := embeddedFixture(t, "package checks\nimport \"testing\"\nfunc TestReal(t *testing.T){}\n")
	result := runGo(project, entry)
	encoded, err := json.Marshal(result)
	if err != nil || !strings.Contains(string(encoded), `"testExecution":{"engine":"qfli-embedded-testing-v1","testsRun":1,"testsPassed":1`) {
		t.Fatalf("execution proof missing: %s, %v", encoded, err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	result = runGoWithContext(ctx, project, entry)
	if result.ExitCode != 1 || result.TestExecution.TestsRun != 0 || !strings.Contains(result.Stderr, "canceled") {
		t.Fatalf("pre-cancelled tests executed: %+v", result)
	}
}
