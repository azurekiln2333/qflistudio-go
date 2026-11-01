package main

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

func evaluateProjectEnvironment(t *testing.T, project, source string) string {
	t.Helper()
	var output outputBuffer
	interpreter := interp.New(interp.Options{Stdout: &output, Stderr: &output})
	if err := interpreter.Use(stdlib.Symbols); err != nil {
		t.Fatal(err)
	}
	if err := useProjectEnvironment(interpreter, project, project); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if _, err := interpreter.EvalWithContext(ctx, source); err != nil {
		t.Fatal(err)
	}
	return output.String()
}

func TestProjectEnvironmentRelativeFilesAndCwdIsolation(t *testing.T) {
	before, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	project := t.TempDir()
	got := evaluateProjectEnvironment(t, project, `package main
import ("fmt"; "os"; "path/filepath"; "io/fs")
func main() {
  root, _ := os.Getwd()
  if err := os.Mkdir("data", 0700); err != nil { panic(err) }
  if err := os.Chdir("data"); err != nil { panic(err) }
  if err := os.WriteFile("record.txt", []byte("project"), 0600); err != nil { panic(err) }
  current, _ := filepath.Abs("")
  matches, err := filepath.Glob("*.txt"); if err != nil { panic(err) }
  names := []string{}
  err = filepath.WalkDir(".", func(name string, entry fs.DirEntry, err error) error {
    if err != nil { return err }; names = append(names, name); return nil
  }); if err != nil { panic(err) }
  if err := os.RemoveAll(""); err != nil { panic(err) }
  data, err := os.ReadFile("record.txt"); if err != nil { panic(err) }
  _, emptyErr := os.ReadFile("")
  fmt.Println(current == filepath.Join(root, "data"), string(data), matches, names, emptyErr != nil)
}`)
	if got != "true project [record.txt] [. record.txt] true\n" {
		t.Fatalf("unexpected output: %q", got)
	}
	after, err := os.Getwd()
	if err != nil || after != before {
		t.Fatalf("host cwd changed: %q -> %q (%v)", before, after, err)
	}
	if data, err := os.ReadFile(filepath.Join(project, "data", "record.txt")); err != nil || string(data) != "project" {
		t.Fatalf("file not written under project: %q, %v", data, err)
	}
}

func TestProjectEnvironmentTemporaryFilesUseProject(t *testing.T) {
	project := t.TempDir()
	got := evaluateProjectEnvironment(t, project, `package main
import ("fmt"; "os"; "path/filepath"; "io/ioutil")
func main() {
  root, _ := os.Getwd()
  dir, err := os.MkdirTemp("", "lesson-"); if err != nil { panic(err) }
  defer os.RemoveAll(dir)
  file, err := ioutil.TempFile("", "legacy-"); if err != nil { panic(err) }
  name := file.Name(); file.Close(); defer os.Remove(name)
  fmt.Println(filepath.Dir(dir) == os.TempDir(), filepath.Dir(name) == os.TempDir(), os.TempDir() == filepath.Join(root, ".qfli", "tmp"))
}`)
	if got != "true true true\n" {
		t.Fatalf("unexpected output: %q", got)
	}
	entries, err := os.ReadDir(filepath.Join(project, ".qfli", "tmp"))
	if err != nil || len(entries) != 0 {
		t.Fatalf("temporary files were not cleaned: %v, %v", entries, err)
	}
}

func TestProjectEnvironmentConcurrentProjects(t *testing.T) {
	roots := []string{t.TempDir(), t.TempDir()}
	var workers sync.WaitGroup
	for index, root := range roots {
		index, root := index, root
		workers.Add(1)
		go func() {
			defer workers.Done()
			value := strings.Repeat("x", index+1)
			got := evaluateProjectEnvironment(t, root, `package main
import ("fmt"; "os")
func main() {
  for i:=0; i<10; i++ { if err := os.WriteFile("same.txt", []byte("`+value+`"), 0600); err != nil { panic(err) } }
  data, err := os.ReadFile("same.txt"); if err != nil { panic(err) }; fmt.Println(string(data))
}`)
			if got != value+"\n" {
				t.Errorf("project %d contaminated: %q", index, got)
			}
		}()
	}
	workers.Wait()
	for index, root := range roots {
		data, err := os.ReadFile(filepath.Join(root, "same.txt"))
		if err != nil || string(data) != strings.Repeat("x", index+1) {
			t.Fatalf("project %d file mismatch: %q, %v", index, data, err)
		}
	}
}
