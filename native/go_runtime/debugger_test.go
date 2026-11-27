package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
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

func debugFixture(t *testing.T, id uint64, files map[string]string, entry string, breakpoints map[string][]int) debugResponse {
	t.Helper()
	root := t.TempDir()
	for name, source := range files {
		file := filepath.Join(root, name)
		if err := os.MkdirAll(filepath.Dir(file), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(file, []byte(source), 0600); err != nil {
			t.Fatal(err)
		}
	}
	response := startGoDebug(id, debugRequest{ProjectPath: root, EntryFile: filepath.Join(root, entry), Breakpoints: breakpoints})
	t.Cleanup(func() {
		session := getGoDebug(id)
		closeGoDebug(id)
		if session != nil {
			select {
			case <-session.done:
			case <-time.After(3 * time.Second):
				t.Error("debug session did not terminate")
			}
		}
	})
	if !response.OK {
		t.Fatal(response.Error)
	}
	return response
}
func waitDebug(t *testing.T, id, after uint64, accept func(debugResponse) bool) debugResponse {
	t.Helper()
	deadline := time.Now().Add(6 * time.Second)
	for time.Now().Before(deadline) {
		response := pollGoDebug(id, after)
		if !response.OK {
			t.Fatalf("debug poll: %s", response.Error)
		}
		if accept(response) {
			return response
		}
		time.Sleep(time.Millisecond)
	}
	t.Fatalf("debug timeout: %+v", pollGoDebug(id, after))
	return debugResponse{}
}
func waitDebugPause(t *testing.T, id, after uint64, reason string) debugResponse {
	t.Helper()
	return waitDebug(t, id, after, func(response debugResponse) bool {
		if response.State == "failed" {
			t.Fatalf("debug failed: %+v", response)
		}
		for _, event := range response.Events {
			if event.Reason == reason {
				return true
			}
		}
		return false
	})
}
func debugControl(t *testing.T, id uint64, command string) {
	t.Helper()
	if response := commandGoDebug(id, debugCommandRequest{Command: command}); !response.OK {
		t.Fatal(response.Error)
	}
}
func lastDebugEvent(response debugResponse) debugEvent {
	return response.Events[len(response.Events)-1]
}

func TestDebugBreakpointFramesStepAndContinue(t *testing.T) {
	marker := filepath.Join(t.TempDir(), "after-breakpoint")
	source := "package main\nimport (\"fmt\";\"os\")\nfunc twice(v int) int { return v*2 }\nfunc main() {\n value := 21\n result := twice(value)\n os.WriteFile(" + strconv.Quote(marker) + ", []byte(\"done\"), 0600)\n fmt.Println(result)\n}\n"
	debugFixture(t, 101, map[string]string{"main.go": source}, "main.go", map[string][]int{"main.go": {7}})
	entry := waitDebugPause(t, 101, 0, "entry")
	if _, err := os.Stat(marker); !os.IsNotExist(err) {
		t.Fatal("program executed before entry resume")
	}
	debugControl(t, 101, "continue")
	paused := waitDebugPause(t, 101, entry.Sequence, "breakpoint")
	if _, err := os.Stat(marker); !os.IsNotExist(err) {
		t.Fatal("breakpoint did not stop before side effect")
	}
	if len(paused.Breakpoints) != 1 || !paused.Breakpoints[0].Valid {
		t.Fatalf("breakpoint not verified: %+v", paused.Breakpoints)
	}
	event := lastDebugEvent(paused)
	if len(event.Frames) == 0 || event.Frames[0].Line != 7 || event.Frames[0].Name != "main" {
		t.Fatalf("wrong frame: %+v", event.Frames)
	}
	values := map[string]string{}
	for _, variable := range event.Frames[0].Variables {
		values[variable.Name] = variable.Value
	}
	if values["value"] != "21" || values["result"] != "42" {
		t.Fatalf("wrong local variables: %+v", values)
	}
	debugControl(t, 101, "stepOver")
	stepped := waitDebugPause(t, 101, paused.Sequence, "stepOver")
	if lastDebugEvent(stepped).Frames[0].Line == 7 {
		t.Fatal("step did not change execution line")
	}
	if _, err := os.Stat(marker); err != nil {
		t.Fatal("stepped statement did not execute", err)
	}
	debugControl(t, 101, "continue")
	finished := waitDebug(t, 101, 0, func(response debugResponse) bool { return response.State == "terminated" || response.State == "failed" })
	if finished.State != "terminated" || strings.TrimSpace(finished.Stdout) != "42" {
		t.Fatalf("wrong debug result: %+v", finished)
	}
}

func TestDebugMultiFileScopesAndSelectedEntry(t *testing.T) {
	debugFixture(t, 102, map[string]string{
		"main.go":   "package main\nfunc main(){panic(\"wrong entry\")}\n",
		"main2.go":  "package main\nimport f \"fmt\"\nfunc main(){f.Println(helper())}\n",
		"helper.go": "package main\nimport f \"strings\"\nfunc helper() string {\n return f.ToUpper(\"scopes\")\n}\n",
	}, "main2.go", map[string][]int{"helper.go": {4}})
	entry := waitDebugPause(t, 102, 0, "entry")
	debugControl(t, 102, "continue")
	paused := waitDebugPause(t, 102, entry.Sequence, "breakpoint")
	frames := lastDebugEvent(paused).Frames
	if len(frames) < 2 || frames[0].File != "helper.go" || frames[0].Name != "helper" || frames[1].Name != "main" {
		t.Fatalf("wrong stack: %+v", frames)
	}
	debugControl(t, 102, "stepOut")
	stepped := waitDebugPause(t, 102, paused.Sequence, "stepOut")
	if lastDebugEvent(stepped).Frames[0].Name != "main" {
		t.Fatalf("step out failed: %+v", stepped)
	}
	debugControl(t, 102, "continue")
	finished := waitDebug(t, 102, 0, func(response debugResponse) bool { return response.State == "terminated" || response.State == "failed" })
	if finished.State != "terminated" || strings.TrimSpace(finished.Stdout) != "SCOPES" {
		t.Fatalf("wrong output: %+v", finished)
	}
}

func TestDebugEntryInitializerDoesNotRunBeforeResume(t *testing.T) {
	marker := filepath.Join(t.TempDir(), "initialized")
	source := "package main\nimport \"os\"\nfunc init(){\n os.WriteFile(" + strconv.Quote(marker) + ", []byte(\"init\"), 0600)\n}\nfunc main(){}\n"
	debugFixture(t, 103, map[string]string{"main.go": source}, "main.go", map[string][]int{"main.go": {4}})
	entry := waitDebugPause(t, 103, 0, "entry")
	if _, err := os.Stat(marker); !os.IsNotExist(err) {
		t.Fatal("init executed during compile")
	}
	debugControl(t, 103, "continue")
	waitDebugPause(t, 103, entry.Sequence, "breakpoint")
	if _, err := os.Stat(marker); !os.IsNotExist(err) {
		t.Fatal("init breakpoint failed")
	}
}

func TestDebugPauseStopAndIDOwnership(t *testing.T) {
	debugFixture(t, 104, map[string]string{"main.go": "package main\nfunc main(){\n count := 0\n for { count++ }\n}\n"}, "main.go", nil)
	entry := waitDebugPause(t, 104, 0, "entry")
	if response := startGoDebug(104, debugRequest{}); response.OK {
		t.Fatal("duplicate session replaced owner")
	}
	debugControl(t, 104, "continue")
	waitDebug(t, 104, entry.Sequence, func(response debugResponse) bool { return response.State == "running" })
	debugControl(t, 104, "pause")
	paused := waitDebugPause(t, 104, entry.Sequence, "pause")
	debugControl(t, 104, "stepInto")
	stepped := waitDebugPause(t, 104, paused.Sequence, "stepInto")
	if len(lastDebugEvent(stepped).Frames) == 0 {
		t.Fatal("step has no frame")
	}
	debugControl(t, 104, "stop")
	waitDebug(t, 104, 0, func(response debugResponse) bool { return response.State == "terminated" })
	closeGoDebug(104)
	if response := pollGoDebug(104, 0); response.OK {
		t.Fatal("closed session still registered")
	}
	closeGoDebug(105)
	if response := startGoDebug(105, debugRequest{}); response.OK {
		t.Fatal("pre-cancelled session started")
	}
}

func TestDebugErrorsAndPanicDoNotEscape(t *testing.T) {
	for index, source := range []string{"package main\nfunc main( {", "package main\nfunc main(){panic(\"debug panic\")}\n", "package main\nfunc main(){go func(){panic(\"worker panic\")}(); select{}}\n", "package main\nimport \"time\"\nfunc main(){time.AfterFunc(0,func(){panic(\"timer panic\")});select{}}\n"} {
		id := uint64(110 + index)
		debugFixture(t, id, map[string]string{"main.go": source}, "main.go", nil)
		response := waitDebug(t, id, 0, func(response debugResponse) bool { return response.State == "paused" || response.State == "failed" })
		if response.State == "paused" {
			debugControl(t, id, "continue")
		}
		failed := waitDebug(t, id, 0, func(response debugResponse) bool { return response.State == "failed" })
		if lastDebugEvent(failed).Message == "" {
			t.Fatal("failure has no diagnostic")
		}
	}
}

func TestDebugBuffersAndInvalidCommands(t *testing.T) {
	var output debugOutput
	output.Write([]byte(strings.Repeat("中", debugMaxOutput)))
	text, truncated := output.snapshot()
	if len(text) > debugMaxOutput || !truncated || !strings.HasPrefix(text, "中") {
		t.Fatal("debug output not bounded")
	}
	session := &debugSession{id: 999, state: "running", events: []debugEvent{}, breakpoints: []debugBreakpoint{}}
	for index := 0; index < 300; index++ {
		session.append(debugEvent{Reason: "test"})
	}
	snapshot := session.snapshot(250)
	if len(session.events) != debugMaxEvents || snapshot.DroppedThrough != 172 || len(snapshot.Events) != 50 {
		t.Fatalf("event log not bounded: %+v", snapshot)
	}
	if response := commandGoDebug(999, debugCommandRequest{Command: "eval"}); response.OK {
		t.Fatal("unknown session accepted")
	}
}

func TestDebugConcurrentPollCommandsAndClose(t *testing.T) {
	debugFixture(t, 120, map[string]string{"main.go": "package main\nfunc main(){\n for {}\n}\n"}, "main.go", nil)
	waitDebugPause(t, 120, 0, "entry")
	var callers sync.WaitGroup
	for index := 0; index < 12; index++ {
		callers.Add(1)
		go func(index int) {
			defer callers.Done()
			for attempt := 0; attempt < 12; attempt++ {
				switch index % 3 {
				case 0:
					pollGoDebug(120, 0)
				case 1:
					commandGoDebug(120, debugCommandRequest{Command: "continue"})
				case 2:
					commandGoDebug(120, debugCommandRequest{Command: "pause"})
				}
			}
		}(index)
	}
	callers.Wait()
	debugControl(t, 120, "stop")
	waitDebug(t, 120, 0, func(response debugResponse) bool { return response.State == "terminated" })
	closeGoDebug(120)
	if response := pollGoDebug(120, 0); response.OK {
		t.Fatal("closed concurrent session retained")
	}
}

func TestDebugStopAndCloseWaitForBlockedNativeWorkers(t *testing.T) {
	for index, kind := range []string{"main", "go", "timer-literal", "timer-named"} {
		t.Run(kind, func(t *testing.T) {
			entered, release := make(chan struct{}), make(chan struct{})
			var once sync.Once
			unblock := func() { once.Do(func() { close(release) }) }
			defer unblock()
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				close(entered)
				<-release
				w.Write([]byte("finished"))
			}))
			defer server.Close()
			defer unblock()
			call := "http.Get(" + strconv.Quote(server.URL) + ")"
			imports, helper := "\"net/http\"", ""
			switch kind {
			case "go":
				call = "go func(){" + call + "}(); select{}"
			case "timer-literal":
				imports += ";\"time\""
				call = "time.AfterFunc(0,func(){" + call + "});select{}"
			case "timer-named":
				imports += ";\"time\""
				helper = "func fetch(){" + call + "}\n"
				call = "time.AfterFunc(0,fetch);select{}"
			}
			id := uint64(130 + index)
			debugFixture(t, id, map[string]string{"main.go": "package main\nimport (" + imports + ")\n" + helper + "func main(){" + call + "}\n"}, "main.go", nil)
			waitDebugPause(t, id, 0, "entry")
			debugControl(t, id, "continue")
			select {
			case <-entered:
			case <-time.After(3 * time.Second):
				t.Fatal("native HTTP call did not start")
			}
			if kind != "main" {
				if response := pollGoDebug(id, 0); len(response.Threads) != 2 {
					t.Fatalf("concurrent native worker missing from live threads: %+v", response)
				}
			}
			debugControl(t, id, "stop")
			closed := make(chan debugResponse, 1)
			go func() { closed <- closeGoDebug(id) }()
			select {
			case response := <-closed:
				stack := make([]byte, 32768)
				stack = stack[:runtime.Stack(stack, true)]
				t.Fatalf("close returned while native worker was blocked: %+v\n%s", response, stack)
			case <-time.After(30 * time.Millisecond):
			}
			if response := pollGoDebug(id, 0); !response.OK || response.State != "stopping" {
				t.Fatalf("worker ownership lost before actual exit: %+v", response)
			}
			unblock()
			select {
			case response := <-closed:
				if !response.OK || response.State != "closed" {
					t.Fatalf("close failed: %+v", response)
				}
			case <-time.After(3 * time.Second):
				t.Fatal("close did not complete after worker exit")
			}
			if pollGoDebug(id, 0).OK {
				t.Fatal("closed session registration was retained")
			}
		})
	}
}

func TestDebugLocalDependencyInitializerCallbackSameEpoch(t *testing.T) {
	const id = 140
	debugFixture(t, id, map[string]string{
		"go.mod":               "module qfli-project\n\ngo 1.21\n",
		"src/localpkg/pool.go": "package localpkg\nimport \"sync\"\nvar Pool=sync.Pool{New:func() any{return \"ready\"}}\n",
		"src/main.go":          "package main\nimport(\"fmt\";\"qfli-project/src/localpkg\")\nfunc main(){fmt.Println(localpkg.Pool.Get())}\n",
	}, "src/main.go", nil)
	paused := waitDebugPause(t, id, 0, "entry")
	if paused.Stdout != "" {
		t.Fatalf("entry executed during dependency preparation: %+v", paused)
	}
	session := getGoDebug(id)
	ordinary := runGo(session.request.ProjectPath, filepath.Join(session.request.ProjectPath, "src/main.go"))
	if ordinary.ExitCode != 0 || ordinary.Stdout != "ready\n" {
		t.Fatalf("ordinary local dependency run failed: %+v", ordinary)
	}
	debugControl(t, id, "continue")
	finished := waitDebug(t, id, 0, func(response debugResponse) bool { return response.State == "terminated" || response.State == "failed" })
	if finished.State != "terminated" || finished.Stdout != ordinary.Stdout {
		t.Fatalf("initializer-created callback did not survive the entry pause: %+v", finished)
	}
}

func TestDebugNativeCallbackKeepsSynchronousThread(t *testing.T) {
	for index, kind := range []string{"direct", "deferred"} {
		t.Run(kind, func(t *testing.T) {
			id := uint64(141 + index)
			before, prefix, after := "", "", " fmt.Println(values)\n"
			line := 6
			if kind == "deferred" {
				before, prefix, after = " defer fmt.Println(values)\n", "defer ", ""
				line++
			}
			source := "package main\nimport(\"fmt\";\"sort\")\nfunc main(){\n values:=[]int{2,1}\n" + before + " " + prefix + "sort.Slice(values,func(i,j int)bool{\n  return values[i]<values[j]\n })\n" + after + "}\n"
			debugFixture(t, id, map[string]string{"main.go": source}, "main.go", map[string][]int{"main.go": {line}})
			entry := waitDebugPause(t, id, 0, "entry")
			debugControl(t, id, "continue")
			paused := waitDebugPause(t, id, entry.Sequence, "breakpoint")
			event := lastDebugEvent(paused)
			if len(paused.Threads) != 1 || event.GoRoutine != 1 || paused.Threads[0].Kind != "goroutine" || event.Kind != "goroutine" || event.OpaqueNativeBoundary {
				t.Fatalf("synchronous sort callback was counted as another thread: %+v", paused)
			}
			debugControl(t, id, "continue")
			finished := waitDebug(t, id, 0, func(response debugResponse) bool { return response.State == "terminated" || response.State == "failed" })
			if finished.State != "terminated" || finished.Stdout != "[1 2]\n" {
				t.Fatalf("synchronous callback failed: %+v", finished)
			}
		})
	}
}

func TestDebugClosedEpochRejectsLateNativeCallbacks(t *testing.T) {
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
	dbg, err := interpreter.DebugPath(context.Background(), "qfli-project", func(*interp.DebugEvent) {}, &interp.DebugOptions{GoRoutineStartAt1: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { dbg.Terminate(); dbg.Wait() })
	if err = dbg.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err = dbg.Wait(); err != nil {
		t.Fatal(err)
	}
	var callback func()
	select {
	case callback = <-callbacks:
	default:
		t.Fatal("native library did not retain the interpreted callback")
	}
	var late sync.WaitGroup
	for index := 0; index < 32; index++ {
		late.Add(1)
		go func() { defer late.Done(); callback() }()
	}
	late.Wait()
	if calls.Load() != 0 || len(dbg.GoRoutines()) != 0 {
		t.Fatalf("closed epoch executed late callback: calls=%d threads=%v", calls.Load(), dbg.GoRoutines())
	}
}

func debugSourceLine(t *testing.T, source, marker string) int {
	t.Helper()
	for index, line := range strings.Split(source, "\n") {
		if strings.Contains(line, marker) {
			return index + 1
		}
	}
	t.Fatalf("debug fixture marker %q is missing", marker)
	return 0
}

func debugRoutineControl(t *testing.T, id uint64, routine int, command string) debugResponse {
	t.Helper()
	response := commandGoDebug(id, debugCommandRequest{Command: command, GoRoutine: routine})
	if !response.OK {
		t.Fatalf("%s routine %d: %s", command, routine, response.Error)
	}
	return response
}

func requireOpaqueDebugEvent(t *testing.T, event debugEvent) {
	t.Helper()
	if event.Kind != "nativeCallback" || !event.OpaqueNativeBoundary || len(event.Frames) == 0 {
		t.Fatalf("opaque callback identity/boundary missing: %+v", event)
	}
	if !event.Frames[len(event.Frames)-1].OpaqueNativeBoundary {
		t.Fatalf("opaque stack has no final source boundary: %+v", event.Frames)
	}
	for _, frame := range event.Frames {
		if len(frame.Variables) != 0 || frame.LocalsUnavailableReason != "Opaque native callback may capture values outside this stack; locals were not read" {
			t.Fatalf("opaque callback inspected uncertain locals: %+v", frame)
		}
	}
}

func TestDebugOpaqueCallbackOutlivesItsCreatingWorker(t *testing.T) {
	const id = 150
	source := `package main
import ("fmt"; "sync")
var pool sync.Pool
func worker(done chan struct{}) {
 pool.New = func() interface{} {
  value := 7 // callback pause
  return value
 }
 close(done) // creator pause
}
func main() {
 done := make(chan struct{})
 go worker(done)
 <-done
 fmt.Println("ready") // main pause
 fmt.Println(pool.Get())
}
`
	debugFixture(t, id, map[string]string{"main.go": source}, "main.go", map[string][]int{"main.go": {
		debugSourceLine(t, source, "creator pause"), debugSourceLine(t, source, "main pause"), debugSourceLine(t, source, "callback pause"),
	}})
	entry := waitDebugPause(t, id, 0, "entry")
	debugControl(t, id, "continue")
	creator := waitDebugPause(t, id, entry.Sequence, "breakpoint")
	creatorEvent := lastDebugEvent(creator)
	if creatorEvent.GoRoutine == 1 || creatorEvent.Kind != "goroutine" {
		t.Fatalf("creator did not run as an interpreted worker: %+v", creatorEvent)
	}
	debugRoutineControl(t, id, creatorEvent.GoRoutine, "continue")
	mainPause := waitDebugPause(t, id, creator.Sequence, "breakpoint")
	if lastDebugEvent(mainPause).GoRoutine != 1 {
		t.Fatalf("main barrier was not reached: %+v", mainPause)
	}
	// close(done) precedes the worker's final unwind. Wait for actual removal
	// while main remains paused, so this cannot accidentally use a live creator.
	waitDebug(t, id, mainPause.Sequence, func(response debugResponse) bool {
		return len(response.Threads) == 1 && response.Threads[0].ID == 1 && response.Threads[0].Paused
	})
	debugRoutineControl(t, id, 1, "continue")
	callback := waitDebugPause(t, id, mainPause.Sequence, "breakpoint")
	event := lastDebugEvent(callback)
	requireOpaqueDebugEvent(t, event)
	if event.GoRoutine == 1 || event.GoRoutine == creatorEvent.GoRoutine || len(event.Frames) != 1 {
		t.Fatalf("callback reused an exited creator or invented its caller: %+v", callback)
	}
	live := false
	for _, routine := range callback.Threads {
		if routine.ID == event.GoRoutine {
			live = routine.Paused && routine.Kind == "nativeCallback"
		}
	}
	if !live {
		t.Fatalf("callback pause has no live command owner: %+v", callback)
	}
	debugRoutineControl(t, id, event.GoRoutine, "stepOver")
	stepped := waitDebugPause(t, id, callback.Sequence, "stepOver")
	step := lastDebugEvent(stepped)
	requireOpaqueDebugEvent(t, step)
	if step.GoRoutine != event.GoRoutine || step.Frames[0].Line == event.Frames[0].Line {
		t.Fatalf("callback could not step independently: %+v", stepped)
	}
	debugRoutineControl(t, id, event.GoRoutine, "continue")
	finished := waitDebug(t, id, 0, func(response debugResponse) bool { return response.State == "terminated" || response.State == "failed" })
	if finished.State != "terminated" || finished.Stdout != "ready\n7\n" || len(finished.Threads) != 0 {
		t.Fatalf("callback did not complete after its creator exited: %+v", finished)
	}
	found := false
	for _, retained := range finished.Events {
		if retained.Sequence == event.Sequence {
			requireOpaqueDebugEvent(t, retained)
			found = true
		}
	}
	if !found {
		t.Fatal("callback metadata disappeared when its owner exited")
	}
}

func TestDebugOpaqueCallbackCreatedByMainCalledByWorker(t *testing.T) {
	const id = 151
	source := `package main
import ("fmt"; "sync")
var pool sync.Pool
func worker(done chan interface{}) {
 var value interface{} // worker pause
 value = pool.Get()
 done <- value
}
func main() {
 pool.New = func() interface{} {
  value := 9 // callback pause
  return value
 }
 done := make(chan interface{})
 go worker(done)
 fmt.Println(<-done)
}
`
	// A send-line breakpoint stops after its RHS; pause before pool.Get instead.
	workerLine := debugSourceLine(t, source, "worker pause")
	callbackLine := debugSourceLine(t, source, "callback pause")
	debugFixture(t, id, map[string]string{"main.go": source}, "main.go", map[string][]int{"main.go": {workerLine, callbackLine}})
	entry := waitDebugPause(t, id, 0, "entry")
	if len(entry.Breakpoints) != 2 {
		t.Fatalf("expected two worker/callback breakpoints, got %+v", entry.Breakpoints)
	}
	for index, line := range []int{workerLine, callbackLine} {
		breakpoint := entry.Breakpoints[index]
		if !breakpoint.Valid || breakpoint.File != "main.go" || breakpoint.Line != line || breakpoint.ActualLine != line {
			t.Fatalf("breakpoint = %+v, want main.go:%d", breakpoint, line)
		}
	}
	debugControl(t, id, "continue")
	worker := waitDebugPause(t, id, entry.Sequence, "breakpoint")
	workerEvent := lastDebugEvent(worker)
	workerID := workerEvent.GoRoutine
	if workerEvent.Reason != "breakpoint" || workerID <= 1 || workerEvent.Kind != "goroutine" || workerEvent.OpaqueNativeBoundary || len(workerEvent.Frames) != 1 {
		t.Fatalf("first stop is not the interpreted worker: %+v", worker)
	}
	workerFrame := workerEvent.Frames[0]
	if workerFrame.Name != "worker" || workerFrame.File != "main.go" || workerFrame.Line != workerLine || workerFrame.OpaqueNativeBoundary {
		t.Fatalf("worker did not stop before pool.Get: %+v", workerEvent)
	}
	debugRoutineControl(t, id, workerID, "continue")
	callback := waitDebugPause(t, id, worker.Sequence, "breakpoint")
	event := lastDebugEvent(callback)
	requireOpaqueDebugEvent(t, event)
	if event.GoRoutine == 1 || event.GoRoutine == workerID || len(event.Frames) != 1 {
		t.Fatalf("opaque callback claimed its lexical or native caller: %+v", callback)
	}
	debugRoutineControl(t, id, event.GoRoutine, "continue")
	finished := waitDebug(t, id, 0, func(response debugResponse) bool { return response.State == "terminated" || response.State == "failed" })
	if finished.State != "terminated" || finished.Stdout != "9\n" {
		t.Fatalf("main-created callback failed on a worker: %+v", finished)
	}
}

func TestDebugConcurrentOpaqueCallbacksHaveIndependentControls(t *testing.T) {
	const id = 152
	source := `package main
import ("fmt"; "sync")
var pool sync.Pool
func nested() int {
 value := 7 // nested pause
 return value
}
func worker(done chan int) { done <- pool.Get().(int) }
func main() {
 pool.New = func() interface{} {
  value := nested()
  return value
 }
 done := make(chan int)
 go worker(done)
 go worker(done)
 left := <-done
 right := <-done
 fmt.Println(left + right)
}
`
	debugFixture(t, id, map[string]string{"main.go": source}, "main.go", map[string][]int{"main.go": {debugSourceLine(t, source, "nested pause")}})
	entry := waitDebugPause(t, id, 0, "entry")
	debugControl(t, id, "continue")
	owners := make(map[int]debugEvent)
	paused := waitDebug(t, id, entry.Sequence, func(response debugResponse) bool {
		if response.State == "failed" {
			t.Fatalf("concurrent callbacks failed: %+v", response)
		}
		for _, event := range response.Events {
			if event.Reason == "breakpoint" && event.Kind == "nativeCallback" {
				owners[event.GoRoutine] = event
			}
		}
		return len(owners) == 2
	})
	ids := make([]int, 0, 2)
	for routine, event := range owners {
		requireOpaqueDebugEvent(t, event)
		if len(event.Frames) != 2 || event.Frames[0].Name != "nested" || event.Frames[0].OpaqueNativeBoundary {
			t.Fatalf("nested stack crossed an opaque boundary: %+v", event.Frames)
		}
		ids = append(ids, routine)
	}
	for _, routine := range paused.Threads {
		if _, exists := owners[routine.ID]; exists && (!routine.Paused || routine.Kind != "nativeCallback") {
			t.Fatalf("callback owners share a running/paused state: %+v", paused.Threads)
		}
	}
	liveCallbacks := 0
	for _, routine := range paused.Threads {
		if routine.Kind == "nativeCallback" && routine.Paused {
			liveCallbacks++
		}
	}
	if liveCallbacks != 2 {
		t.Fatalf("concurrent pauses do not have two live command owners: %+v", paused.Threads)
	}
	first, second := ids[0], ids[1]
	debugRoutineControl(t, id, first, "stepOut")
	out := waitDebugPause(t, id, paused.Sequence, "stepOut")
	event := lastDebugEvent(out)
	requireOpaqueDebugEvent(t, event)
	if event.GoRoutine != first || len(event.Frames) != 1 || !event.Frames[0].OpaqueNativeBoundary {
		t.Fatalf("stepOut did not return to the callback boundary: %+v", out)
	}
	debugRoutineControl(t, id, first, "stepOut")
	waitDebug(t, id, out.Sequence, func(response debugResponse) bool {
		firstLive, secondPaused := false, false
		for _, routine := range response.Threads {
			firstLive = firstLive || routine.ID == first
			secondPaused = secondPaused || routine.ID == second && routine.Paused
		}
		return !firstLive && secondPaused
	})
	if response := commandGoDebug(id, debugCommandRequest{Command: "continue", GoRoutine: first}); response.OK {
		t.Fatal("exited callback retained a stopped command entry")
	}
	debugRoutineControl(t, id, second, "stepInto")
	stepped := waitDebugPause(t, id, out.Sequence, "stepInto")
	if lastDebugEvent(stepped).GoRoutine != second {
		t.Fatalf("stepping one callback resumed another: %+v", stepped)
	}
	debugRoutineControl(t, id, second, "continue")
	finished := waitDebug(t, id, 0, func(response debugResponse) bool { return response.State == "terminated" || response.State == "failed" })
	if finished.State != "terminated" || finished.Stdout != "14\n" || len(finished.Threads) != 0 {
		t.Fatalf("concurrent callback ownership did not drain: %+v", finished)
	}
	session := getGoDebug(id)
	session.Lock()
	remaining := len(session.paused)
	session.Unlock()
	if remaining != 0 {
		t.Fatal("completed opaque callbacks retained paused entries")
	}
}

func TestDebugSynchronousOpaqueCallbackPanicRecoversInCaller(t *testing.T) {
	const id = 153
	source := `package main
import ("fmt"; "sync")
func main() {
 defer func() { fmt.Print(recover()) }()
 pool := sync.Pool{New: func() interface{} {
  panic("recovered opaque") // callback panic
 }}
 pool.Get()
}
`
	debugFixture(t, id, map[string]string{"main.go": source}, "main.go", map[string][]int{"main.go": {debugSourceLine(t, source, "callback panic")}})
	entry := waitDebugPause(t, id, 0, "entry")
	debugControl(t, id, "continue")
	paused := waitDebugPause(t, id, entry.Sequence, "breakpoint")
	event := lastDebugEvent(paused)
	requireOpaqueDebugEvent(t, event)
	debugRoutineControl(t, id, event.GoRoutine, "continue")
	finished := waitDebug(t, id, 0, func(response debugResponse) bool { return response.State == "terminated" || response.State == "failed" })
	if finished.State != "terminated" || finished.Stdout != "recovered opaque" || finished.Stderr != "" || len(finished.Threads) != 0 {
		t.Fatalf("logical callback ownership swallowed a synchronously recoverable panic: %+v", finished)
	}
}

func TestDebugStopAndCloseWaitForHeldOpaqueCallback(t *testing.T) {
	const id = 154
	entered, release := make(chan struct{}), make(chan struct{})
	var once sync.Once
	unblock := func() { once.Do(func() { close(release) }) }
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		close(entered)
		<-release
		w.Write([]byte("released"))
	}))
	defer server.Close()
	defer unblock()
	source := "package main\nimport(\"net/http\";\"sync\")\nfunc main(){pool:=sync.Pool{New:func()interface{}{response,_:=http.Get(" + strconv.Quote(server.URL) + ");if response!=nil{response.Body.Close()};return 1}};pool.Get()}\n"
	debugFixture(t, id, map[string]string{"main.go": source}, "main.go", nil)
	waitDebugPause(t, id, 0, "entry")
	debugControl(t, id, "continue")
	select {
	case <-entered:
	case <-time.After(3 * time.Second):
		t.Fatal("opaque callback did not enter its held native call")
	}
	response := pollGoDebug(id, 0)
	callbacks := 0
	for _, routine := range response.Threads {
		if routine.Kind == "nativeCallback" {
			callbacks++
		}
	}
	if callbacks != 1 {
		t.Fatalf("held opaque callback has no live logical owner: %+v", response)
	}
	debugControl(t, id, "stop")
	closed := make(chan debugResponse, 1)
	go func() { closed <- closeGoDebug(id) }()
	select {
	case response := <-closed:
		t.Fatalf("close released an entered opaque callback: %+v", response)
	case <-time.After(30 * time.Millisecond):
	}
	if response := pollGoDebug(id, 0); !response.OK || response.State != "stopping" {
		t.Fatalf("stop lost ownership before callback exit: %+v", response)
	}
	unblock()
	select {
	case response := <-closed:
		if !response.OK || response.State != "closed" || len(response.Threads) != 0 {
			t.Fatalf("close did not drain opaque callback ownership: %+v", response)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("close did not finish after the callback was released")
	}
	if pollGoDebug(id, 0).OK {
		t.Fatal("closed opaque callback session remains registered")
	}
}

func TestDebugClosedEpochRejectsRetainedOpaqueCallbacks(t *testing.T) {
	project := t.TempDir()
	writeGoSource(t, filepath.Join(project, "main.go"), "package main\nimport(\"sync\";\"callbackbridge\")\nfunc main(){pool:=sync.Pool{New:func()interface{}{callbackbridge.Mark();return 7}};callbackbridge.KeepPool(&pool)}\n")
	callbacks := make(chan func() interface{}, 1)
	var calls, entries atomic.Int32
	interpreter := interp.New(interp.Options{GoPath: ".", SourcecodeFilesystem: projectSourceFS{root: os.DirFS(project), entryDir: "."}})
	if err := interpreter.Use(stdlib.Symbols); err != nil {
		t.Fatal(err)
	}
	if err := interpreter.Use(interp.Exports{"callbackbridge/callbackbridge": {
		"KeepPool": reflect.ValueOf(func(pool *sync.Pool) { callbacks <- pool.New }),
		"Mark":     reflect.ValueOf(func() { calls.Add(1) }),
	}}); err != nil {
		t.Fatal(err)
	}
	dbg, err := interpreter.DebugPath(context.Background(), "qfli-project", func(event *interp.DebugEvent) {
		if event.Reason() == interp.DebugEnterGoRoutine && event.GoRoutineKind() == "nativeCallback" {
			entries.Add(1)
		}
	}, &interp.DebugOptions{GoRoutineStartAt1: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { dbg.Terminate(); dbg.Wait() })
	if err = dbg.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err = dbg.Wait(); err != nil {
		t.Fatal(err)
	}
	var callback func() interface{}
	select {
	case callback = <-callbacks:
	default:
		t.Fatal("native object did not retain its opaque callback")
	}
	var late sync.WaitGroup
	for index := 0; index < 32; index++ {
		late.Add(1)
		go func() { defer late.Done(); callback() }()
	}
	late.Wait()
	if calls.Load() != 0 || entries.Load() != 0 || len(dbg.GoRoutines()) != 0 {
		t.Fatalf("closed epoch admitted an opaque callback: calls=%d entries=%d live=%v", calls.Load(), entries.Load(), dbg.GoRoutines())
	}
}

func TestDebugNestedNativeReentryKeepsOpaqueOwnerAndActualCaller(t *testing.T) {
	const id = 155
	source := `package main
import ("fmt"; "sort"; "sync")
var values = []int{2, 1}
func main() {
 less := func(i, j int) bool {
  return values[i] < values[j] // comparison pause
 }
 pool := sync.Pool{New: func() interface{} {
  sort.Slice(values, less)
  return values[0]
 }}
 fmt.Println(pool.Get())
}
`
	debugFixture(t, id, map[string]string{"main.go": source}, "main.go", map[string][]int{"main.go": {debugSourceLine(t, source, "comparison pause")}})
	entry := waitDebugPause(t, id, 0, "entry")
	debugControl(t, id, "continue")
	paused := waitDebugPause(t, id, entry.Sequence, "breakpoint")
	event := lastDebugEvent(paused)
	requireOpaqueDebugEvent(t, event)
	if len(paused.Threads) != 2 || len(event.Frames) != 2 || event.Frames[0].OpaqueNativeBoundary || event.Frames[1].Name == "main" {
		t.Fatalf("known nested callback followed lexical capture instead of its actual caller: %+v", paused)
	}
	debugRoutineControl(t, id, event.GoRoutine, "stepOut")
	stepped := waitDebugPause(t, id, paused.Sequence, "stepOut")
	step := lastDebugEvent(stepped)
	requireOpaqueDebugEvent(t, step)
	if step.GoRoutine != event.GoRoutine || len(step.Frames) != 1 {
		t.Fatalf("nested native reentry changed owner or crossed the boundary: %+v", stepped)
	}
	debugRoutineControl(t, id, event.GoRoutine, "continue")
	finished := waitDebug(t, id, 0, func(response debugResponse) bool { return response.State == "terminated" || response.State == "failed" })
	if finished.State != "terminated" || finished.Stdout != "1\n" {
		t.Fatalf("nested native reentry did not complete: %+v", finished)
	}
}

func TestDebugAsynchronousOpaqueCallbackPanicStaysInEpoch(t *testing.T) {
	project := t.TempDir()
	writeGoSource(t, filepath.Join(project, "main.go"), "package main\nimport(\"sync\";\"callbackbridge\")\nfunc main(){pool:=sync.Pool{New:func()interface{}{panic(\"opaque external boom\")}};callbackbridge.StartPool(&pool);select{}}\n")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	interpreter := interp.New(interp.Options{GoPath: ".", SourcecodeFilesystem: projectSourceFS{root: os.DirFS(project), entryDir: "."}})
	if err := interpreter.Use(stdlib.Symbols); err != nil {
		t.Fatal(err)
	}
	if err := interpreter.Use(interp.Exports{"callbackbridge/callbackbridge": {
		"StartPool": reflect.ValueOf(func(pool *sync.Pool) { go pool.New() }),
	}}); err != nil {
		t.Fatal(err)
	}
	var entered, exited atomic.Int32
	dbg, err := interpreter.DebugPath(ctx, "qfli-project", func(event *interp.DebugEvent) {
		if event.GoRoutineKind() != "nativeCallback" {
			return
		}
		switch event.Reason() {
		case interp.DebugEnterGoRoutine:
			entered.Add(1)
		case interp.DebugExitGoRoutine:
			exited.Add(1)
		}
	}, &interp.DebugOptions{GoRoutineStartAt1: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { dbg.Terminate(); dbg.Wait() })
	if err = dbg.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err = dbg.Wait(); err == nil || !strings.Contains(err.Error(), "opaque external boom") {
		t.Fatalf("external opaque panic did not fail its epoch: %v", err)
	}
	if entered.Load() != 1 || exited.Load() != 1 || len(dbg.GoRoutines()) != 0 {
		t.Fatalf("external opaque callback owner did not leave exactly once: entered=%d exited=%d live=%v", entered.Load(), exited.Load(), dbg.GoRoutines())
	}
}

type opaqueSourceStackRecorder struct {
	frames chan []interp.SourceFrame
}

func (*opaqueSourceStackRecorder) Mark() { panic("source-aware method binding was bypassed") }
func (*opaqueSourceStackRecorder) SourceMethodEnabled(name string) bool {
	return name == "Mark"
}
func (recorder *opaqueSourceStackRecorder) CallWithSource(name string, frames []interp.SourceFrame, _ []reflect.Value) ([]reflect.Value, bool) {
	if name != "Mark" {
		return nil, false
	}
	recorder.frames <- append([]interp.SourceFrame(nil), frames...)
	return nil, true
}

func TestDebugOpaqueCallbackSourceStackEndsBeforeLexicalCreator(t *testing.T) {
	source := `package main
import ("sync"; "callbackbridge")
var pool sync.Pool
func inner() {
 callbackbridge.Recorder().Mark() // inner call
}
func install() {
 pool.New = func() interface{} {
  inner() // callback call
  return 7
 }
}
func main() {
 done := make(chan struct{})
 go func() { install(); close(done) }()
 <-done
 pool.Get()
}
`
	project := t.TempDir()
	writeGoSource(t, filepath.Join(project, "main.go"), source)
	recorder := &opaqueSourceStackRecorder{frames: make(chan []interp.SourceFrame, 1)}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	interpreter := interp.New(interp.Options{GoPath: ".", SourcecodeFilesystem: projectSourceFS{root: os.DirFS(project), entryDir: "."}})
	if err := interpreter.Use(stdlib.Symbols); err != nil {
		t.Fatal(err)
	}
	if err := interpreter.Use(interp.Exports{"callbackbridge/callbackbridge": {
		"Recorder": reflect.ValueOf(func() *opaqueSourceStackRecorder { return recorder }),
	}}); err != nil {
		t.Fatal(err)
	}
	dbg, err := interpreter.DebugPath(ctx, "qfli-project", func(*interp.DebugEvent) {}, &interp.DebugOptions{GoRoutineStartAt1: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { dbg.Terminate(); dbg.Wait() })
	if err = dbg.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err = dbg.Wait(); err != nil {
		t.Fatal(err)
	}
	select {
	case frames := <-recorder.frames:
		if len(frames) != 2 || frames[0].Line != debugSourceLine(t, source, "inner call") || frames[1].Line != debugSourceLine(t, source, "callback call") {
			t.Fatalf("opaque source stack fabricated its lexical creator/caller: %+v", frames)
		}
	default:
		t.Fatal("nested opaque callback did not record its source stack")
	}
}
