package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

// Run the official filepath implementation in a separate process with its own
// cwd. Neither the test harness nor an interpreter changes the host process cwd.
func TestProjectEvalSymlinksReferenceProcess(t *testing.T) {
	input := os.Getenv("QFLI_SYMLINK_REFERENCE_PATHS")
	if input == "" {
		return
	}
	var paths []string
	if err := json.Unmarshal([]byte(input), &paths); err != nil {
		t.Fatal(err)
	}
	var output strings.Builder
	for _, name := range paths {
		result, err := filepath.EvalSymlinks(name)
		fmt.Fprintf(&output, "%s %t %t\n", result, err != nil, os.IsNotExist(err))
	}
	fmt.Print(output.String())
	os.Exit(0)
}

func checkProjectSymlinks(t *testing.T, project, directory string, names []string) {
	t.Helper()
	before, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	executable, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	input, err := json.Marshal(names)
	if err != nil {
		t.Fatal(err)
	}
	reference := exec.Command(executable, "-test.run=^TestProjectEvalSymlinksReferenceProcess$")
	reference.Dir = directory
	reference.Env = append(os.Environ(), "QFLI_SYMLINK_REFERENCE_PATHS="+string(input))
	wanted, err := reference.CombinedOutput()
	if err != nil {
		t.Fatalf("official filepath reference failed: %s, %v", wanted, err)
	}
	var literals []string
	for _, name := range names {
		literals = append(literals, strconv.Quote(name))
	}
	entry := filepath.Join(directory, "main.go")
	writeGoSource(t, entry, `package main
import ("fmt"; "os"; "path/filepath")
func main() {
 for _, name := range []string{`+strings.Join(literals, ",")+`} {
  result, err := filepath.EvalSymlinks(name)
  fmt.Println(result, err != nil, os.IsNotExist(err))
 }
}`)
	result := runGo(project, entry)
	if result.ExitCode != 0 || result.Stderr != "" || result.Stdout != string(wanted) {
		t.Fatalf("interpreted EvalSymlinks differs from official Go:\nwant %q\nresult %+v", wanted, result)
	}
	after, err := os.Getwd()
	if err != nil || before != after {
		t.Fatalf("host cwd changed: %q -> %q, %v", before, after, err)
	}
}

func TestProjectEnvironmentEvalSymlinksRelativePaths(t *testing.T) {
	project := t.TempDir()
	directory := filepath.Join(project, "src")
	if err := os.MkdirAll(filepath.Join(directory, "data"), 0755); err != nil {
		t.Fatal(err)
	}
	writeGoSource(t, filepath.Join(directory, "data", "file.txt"), "fixture")
	checkProjectSymlinks(t, project, directory, []string{
		"data/file.txt", "./data/../data/file.txt", "", ".", "data/..", "../..", "../src/data/file.txt", "missing",
		filepath.Join(directory, "data", "file.txt"),
	})
}

func TestProjectEnvironmentEvalSymlinksLinkTargets(t *testing.T) {
	project := t.TempDir()
	directory := filepath.Join(project, "src")
	if err := os.MkdirAll(filepath.Join(directory, "data", "deep"), 0755); err != nil {
		t.Fatal(err)
	}
	writeGoSource(t, filepath.Join(directory, "data", "deep", "file.txt"), "fixture")
	writeGoSource(t, filepath.Join(directory, "data", "parent.txt"), "parent")
	outside := t.TempDir()
	writeGoSource(t, filepath.Join(outside, "external.txt"), "outside application project")
	for _, link := range []struct{ target, name string }{
		{filepath.Join("data", "deep"), "relative"},
		{filepath.Join(directory, "data", "deep"), "absolute"},
		{outside, "outside"},
		{"relative", "chain"},
		{"loop", "loop"},
	} {
		if err := os.Symlink(link.target, filepath.Join(directory, link.name)); err != nil {
			t.Skipf("host does not permit symlinks: %v", err)
		}
	}
	checkProjectSymlinks(t, project, directory, []string{
		"relative/file.txt", "relative/../parent.txt", "absolute/file.txt", "absolute/../parent.txt",
		"outside/external.txt", "chain/file.txt", "loop", "relative/missing", "data/parent.txt/child",
	})
}
