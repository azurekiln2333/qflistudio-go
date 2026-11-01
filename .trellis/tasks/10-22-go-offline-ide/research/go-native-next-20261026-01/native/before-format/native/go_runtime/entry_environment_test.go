package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestSelectedEntryWorkingDirectoryAcrossExecutionModes(t *testing.T) {
	before, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for _, mode := range []string{"program", "test", "debug"} {
		t.Run(mode, func(t *testing.T) {
			project := t.TempDir()
			selected := filepath.Join(project, "src")
			if err := os.Mkdir(selected, 0700); err != nil {
				t.Fatal(err)
			}
			writeGoSource(t, filepath.Join(project, "fixture.txt"), "wrong-root")
			writeGoSource(t, filepath.Join(selected, "fixture.txt"), "selected")
			filename := "main.go"
			imports := `"fmt";"os";"path/filepath"`
			invoke := `func main(){check()}`
			if mode == "test" {
				filename = "entry_test.go"
				imports += `;"testing"`
				invoke = `func TestEntry(t *testing.T){check()}`
			}
			entry := filepath.Join(selected, filename)
			writeGoSource(t, entry, `package main
import (`+imports+`)
func check(){
 data,err:=os.ReadFile("fixture.txt");if err!=nil{panic(err)}
 if string(data)!="selected"{panic("wrong initial working directory: "+string(data))}
 cwd,err:=os.Getwd();if err!=nil{panic(err)}
 if filepath.Base(cwd)!="src"{panic("Getwd did not select entry directory")}
 expectedTemp:=filepath.Join(filepath.Dir(cwd),".qfli","tmp")
 if os.TempDir()!=expectedTemp{panic("temporary base moved away from project root")}
 file,err:=os.CreateTemp("","entry-");if err!=nil{panic(err)}
 name:=file.Name();file.Close();defer os.Remove(name)
 if filepath.Dir(name)!=expectedTemp{panic("temporary file is outside project temp base")}
 if err:=os.WriteFile("generated.txt",[]byte("selected"),0600);err!=nil{panic(err)}
 fmt.Println("entry-environment-ok")
}
`+invoke)
			if mode == "debug" {
				const id = 170
				response := startGoDebug(id, debugRequest{ProjectPath: project, EntryFile: entry})
				t.Cleanup(func() { closeGoDebug(id) })
				if !response.OK {
					t.Fatal(response.Error)
				}
				waitDebugPause(t, id, 0, "entry")
				debugControl(t, id, "continue")
				finished := waitDebug(t, id, 0, func(response debugResponse) bool {
					return response.State == "terminated" || response.State == "failed"
				})
				if finished.State != "terminated" || finished.Stdout != "entry-environment-ok\n" {
					t.Fatalf("debug environment: %+v", finished)
				}
			} else {
				result := runGo(project, entry)
				if result.ExitCode != 0 || !strings.Contains(result.Stdout, "entry-environment-ok\n") {
					t.Fatalf("%s environment: %+v", mode, result)
				}
				if mode == "test" && (result.TestExecution == nil || result.TestExecution.TestsRun != 1 || result.TestExecution.TestsPassed != 1) {
					t.Fatalf("selected test did not execute: %+v", result)
				}
			}
			if data, err := os.ReadFile(filepath.Join(selected, "generated.txt")); err != nil || string(data) != "selected" {
				t.Fatalf("entry-relative write: %q, %v", data, err)
			}
			if _, err := os.Stat(filepath.Join(project, "generated.txt")); !os.IsNotExist(err) {
				t.Fatalf("entry-relative write escaped to project root: %v", err)
			}
		})
	}
	if after, err := os.Getwd(); err != nil || after != before {
		t.Fatalf("host working directory changed: %q -> %q (%v)", before, after, err)
	}
}
