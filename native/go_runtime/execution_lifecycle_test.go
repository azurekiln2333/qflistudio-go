package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

func TestRunGoNativeCallbackPanicsStayInInvocation(t *testing.T) {
	const childFlag = "QFLI_GO_CALLBACK_PANIC_CHILD"
	if os.Getenv(childFlag) != "1" {
		executable, err := os.Executable()
		if err != nil {
			t.Fatal(err)
		}
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()
		command := exec.CommandContext(ctx, executable, "-test.run=^TestRunGoNativeCallbackPanicsStayInInvocation$", "-test.timeout=12s")
		command.Env = append(os.Environ(), childFlag+"=1")
		output, err := command.CombinedOutput()
		if err != nil || !strings.Contains(string(output), "CALLBACK-PANIC-CONTAINED") {
			t.Fatalf("native callback panic escaped or did not report failure: %v\n%s", err, output)
		}
		return
	}
	for _, item := range []struct{ name, entry, source string }{
		{"program-literal", "main.go", "package main\nimport \"time\"\nfunc main(){time.AfterFunc(0,func(){panic(\"native timer boom\")});select{}}\n"},
		{"program-named", "main.go", "package main\nimport \"time\"\nfunc fail(){panic(\"native timer boom\")}\nfunc main(){time.AfterFunc(0,fail);select{}}\n"},
		{"initializer", "main.go", "package main\nimport \"time\"\nfunc init(){time.AfterFunc(0,func(){panic(\"native timer boom\")});select{}}\nfunc main(){}\n"},
		{"embedded-test", "timer_test.go", "package timercheck\nimport(\"testing\";\"time\")\nfunc TestTimer(t *testing.T){time.AfterFunc(0,func(){panic(\"native timer boom\")});select{}}\n"},
		{"embedded-cleanup", "timer_test.go", "package timercheck\nimport(\"testing\";\"time\")\nfunc TestTimer(t *testing.T){t.Cleanup(func(){time.AfterFunc(0,func(){panic(\"native timer boom\")});select{}})}\n"},
		{"benchmark", "timer_test.go", "package timercheck\nimport(\"testing\";\"time\")\nfunc BenchmarkTimer(b *testing.B){time.AfterFunc(0,func(){panic(\"native timer boom\")});select{}}\n"},
	} {
		t.Run(item.name, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, item.entry)
			writeGoSource(t, entry, item.source)
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			result := runGoWithContext(ctx, project, entry)
			if result.ExitCode != 1 || !strings.Contains(result.Stderr, "native timer boom") {
				t.Fatalf("callback panic did not become an invocation failure: %+v", result)
			}
			if item.name == "benchmark" {
				if result.TestExecution == nil || result.TestExecution.BenchmarksRun != 1 || strings.Contains(result.Stdout, "PASS") {
					t.Fatalf("interrupted benchmark was falsely counted as passed: %+v", result)
				}
			} else if strings.HasSuffix(item.entry, "_test.go") {
				if result.TestExecution == nil || result.TestExecution.TestsFailed != 1 || result.TestExecution.TestsPassed != 0 || strings.Contains(result.Stdout, "--- PASS: TestTimer") {
					t.Fatalf("interrupted test was falsely counted as passed: %+v", result)
				}
			}
		})
	}
	fmt.Println("CALLBACK-PANIC-CONTAINED")
}

func TestRunGoWaitsForEnteredNativeCallbacks(t *testing.T) {
	for _, ending := range []string{"main-return", "cancel"} {
		t.Run(ending, func(t *testing.T) {
			project := t.TempDir()
			entry := filepath.Join(project, "main.go")
			returning := filepath.Join(project, "main-returning")
			entered, release := make(chan struct{}), make(chan struct{})
			var once sync.Once
			unblock := func() { once.Do(func() { close(release) }) }
			defer unblock()
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path == "/callback" {
					close(entered)
					<-release
				} else {
					<-entered
				}
				w.Write([]byte("ready"))
			}))
			defer server.Close()
			defer unblock()
			finish := "select{}"
			if ending == "main-return" {
				finish = "response,_:=http.Get(" + strconv.Quote(server.URL+"/ready") + ");if response!=nil{response.Body.Close()};os.WriteFile(" + strconv.Quote(returning) + ",[]byte(\"returning\"),0600)"
			}
			writeGoSource(t, entry, "package main\nimport(\"net/http\";\"time\";\"os\")\nvar _=os.Stat\nfunc main(){time.AfterFunc(0,func(){response,_:=http.Get("+strconv.Quote(server.URL+"/callback")+");if response!=nil{response.Body.Close()}});"+finish+"}\n")
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			finished := make(chan runResult, 1)
			go func() { finished <- runGoWithContext(ctx, project, entry) }()
			select {
			case <-entered:
			case <-ctx.Done():
				t.Fatal("native callback did not enter its held HTTP call")
			}
			if ending == "cancel" {
				cancel()
			} else {
				for {
					if _, err := os.Stat(returning); err == nil {
						break
					}
					select {
					case result := <-finished:
						t.Fatalf("invocation ended before the main-return marker: %+v", result)
					case <-ctx.Done():
						t.Fatal("main did not reach its return")
					case <-time.After(time.Millisecond):
					}
				}
			}
			select {
			case result := <-finished:
				t.Fatalf("invocation returned while its native callback was blocked: %+v", result)
			case <-time.After(30 * time.Millisecond):
			}
			unblock()
			select {
			case result := <-finished:
				if ending == "main-return" && result.ExitCode != 0 {
					t.Fatalf("normal main completion failed: %+v", result)
				}
				if ending == "cancel" && (result.ExitCode != 1 || !strings.Contains(result.Stderr, "context canceled")) {
					t.Fatalf("cancellation lost its actual result: %+v", result)
				}
			case <-time.After(3 * time.Second):
				t.Fatal("invocation did not finish after its native callback left")
			}
		})
	}
}

func TestRunGoClosedEpochRejectsRetainedNativeCallbacks(t *testing.T) {
	for _, mode := range []string{"EvalPathWithContext", "InvokeWithContext"} {
		t.Run(mode, func(t *testing.T) {
			project := t.TempDir()
			writeGoSource(t, filepath.Join(project, "main.go"), "package main\nimport \"callbackbridge\"\nfunc main(){callbackbridge.Keep(func(){callbackbridge.Mark()})}\n")
			callbacks := make(chan func(), 1)
			var calls atomic.Int32
			interpreter := interp.New(interp.Options{GoPath: ".", SourcecodeFilesystem: projectSourceFS{root: os.DirFS(project), entryDir: "."}})
			if err := interpreter.Use(stdlib.Symbols); err != nil {
				t.Fatal(err)
			}
			if err := interpreter.Use(interp.Exports{"callbackbridge/callbackbridge": {
				"Keep": reflect.ValueOf(func(callback func()) { callbacks <- callback }),
				"Mark": reflect.ValueOf(func() { calls.Add(1) }),
			}}); err != nil {
				t.Fatal(err)
			}
			var err error
			if mode == "EvalPathWithContext" {
				_, err = interpreter.EvalPathWithContext(context.Background(), "qfli-project")
			} else {
				err = interpreter.InvokeWithContext(context.Background(), func() error {
					_, failure := interpreter.EvalPath("qfli-project")
					return failure
				})
			}
			if err != nil {
				t.Fatal(err)
			}
			var callback func()
			select {
			case callback = <-callbacks:
			default:
				t.Fatal("native library did not retain the source callback")
			}
			runtime.GC()
			var late sync.WaitGroup
			for index := 0; index < 32; index++ {
				late.Add(1)
				go func() { defer late.Done(); callback() }()
			}
			late.Wait()
			if calls.Load() != 0 {
				t.Fatalf("closed invocation executed a retained callback %d times", calls.Load())
			}
		})
	}
}

func TestRunGoMainReturnStopsInterpretedWorkers(t *testing.T) {
	project := t.TempDir()
	entry := filepath.Join(project, "main.go")
	writeGoSource(t, entry, "package main\nimport \"fmt\"\nfunc main(){go func(){for{}}();fmt.Println(\"main returned\")}\n")
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	result := runGoWithContext(ctx, project, entry)
	if result.ExitCode != 0 || result.Stdout != "main returned\n" {
		t.Fatalf("main completion did not cancel its interpreted worker: %+v", result)
	}
}
