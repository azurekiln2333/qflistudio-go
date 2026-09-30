package main

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

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
