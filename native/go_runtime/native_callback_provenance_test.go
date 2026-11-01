package main

import (
	"context"
	"io"
	"net/rpc"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

type nativeProvenanceDebugger struct {
	debugger      *interp.Debugger
	stops         chan debugEvent
	stdout        outputBuffer
	entered       atomic.Int32
	exited        atomic.Int32
	valuesAllowed atomic.Bool
	stoppedEvent  atomic.Pointer[interp.DebugEvent] // eligibility probes only while this owner stays stopped
}

func newNativeProvenanceDebugger(t *testing.T, source string, exports interp.Exports, beforeClose func(), markers ...string) *nativeProvenanceDebugger {
	t.Helper()
	project := t.TempDir()
	writeGoSource(t, filepath.Join(project, "main.go"), source)
	fixture := &nativeProvenanceDebugger{stops: make(chan debugEvent, 32)}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	t.Cleanup(cancel)
	interpreter := interp.New(interp.Options{GoPath: ".", SourcecodeFilesystem: projectSourceFS{root: os.DirFS(project), entryDir: "."}, Stdout: &fixture.stdout})
	if err := interpreter.Use(stdlib.Symbols); err != nil {
		t.Fatal(err)
	}
	if exports != nil {
		if err := interpreter.Use(exports); err != nil {
			t.Fatal(err)
		}
	}
	dbg, err := interpreter.DebugPath(ctx, "qfli-project", func(event *interp.DebugEvent) {
		if event.GoRoutineKind() == "nativeCallback" {
			switch event.Reason() {
			case interp.DebugEnterGoRoutine:
				fixture.entered.Add(1)
			case interp.DebugExitGoRoutine:
				fixture.exited.Add(1)
			}
		}
		reason := ""
		switch event.Reason() {
		case interp.DebugBreak:
			reason = "breakpoint"
		case interp.DebugStepInto:
			reason = "stepInto"
		case interp.DebugStepOver:
			reason = "stepOver"
		case interp.DebugStepOut:
			reason = "stepOut"
		default:
			return
		}
		// Copy while the event owns the stopped frame, before its execution can
		// resume. The stop channel contains only detached snapshots; stoppedEvent
		// is used for eligibility probes only before this owner is resumed.
		var frames []debugFrame
		allowed := event.WithStoppedValues(func() { frames = snapshotDebugFrames(event, project, true) })
		if !allowed {
			frames = snapshotDebugFrames(event, project, false)
		}
		fixture.valuesAllowed.Store(allowed)
		fixture.stoppedEvent.Store(event)
		snapshot := debugEvent{Reason: reason, GoRoutine: event.GoRoutine(), Kind: event.GoRoutineKind(), OpaqueNativeBoundary: event.OpaqueNativeBoundary(), Frames: frames}
		select {
		case fixture.stops <- snapshot:
		case <-ctx.Done():
		}
	}, &interp.DebugOptions{GoRoutineStartAt1: true})
	if err != nil {
		t.Fatal(err)
	}
	fixture.debugger = dbg
	t.Cleanup(func() {
		if beforeClose != nil {
			beforeClose()
		}
		dbg.Terminate()
		dbg.Wait()
	})
	requests := make([]interp.BreakpointRequest, len(markers))
	for index, marker := range markers {
		requests[index] = interp.LineBreakpoint(debugSourceLine(t, source, marker))
	}
	for index, result := range dbg.SetBreakpoints(interp.AllBreakpointTarget(), requests...) {
		if !result.Valid {
			t.Fatalf("breakpoint %q is invalid", markers[index])
		}
	}
	return fixture
}

func (fixture *nativeProvenanceDebugger) next(t *testing.T, reason string) debugEvent {
	t.Helper()
	select {
	case event := <-fixture.stops:
		if event.Reason != reason {
			t.Fatalf("expected %s, got %+v", reason, event)
		}
		return event
	case <-time.After(3 * time.Second):
		t.Fatalf("no %s event; live=%v", reason, fixture.debugger.GoRoutines())
		return debugEvent{}
	}
}

func (fixture *nativeProvenanceDebugger) waitRoutines(t *testing.T, accept func([]*interp.DebugGoRoutine) bool) {
	t.Helper()
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if accept(fixture.debugger.GoRoutines()) {
			return
		}
		time.Sleep(time.Millisecond)
	}
	t.Fatalf("execution owners did not reach the required state: %v", fixture.debugger.GoRoutines())
}

func requireOnlyCallbackSource(t *testing.T, recorder *opaqueSourceStackRecorder, source string, count int) {
	t.Helper()
	for index := 0; index < count; index++ {
		select {
		case frames := <-recorder.frames:
			if len(frames) != 1 || frames[0].Line != debugSourceLine(t, source, "callback pause") {
				t.Fatalf("retained callback claimed its registration-time caller: %+v", frames)
			}
		default:
			t.Fatal("retained callback did not execute the source-aware recorder")
		}
	}
}

func TestDebugRetainedNativeArgumentAfterRegistrarExit(t *testing.T) {
	for _, panics := range []bool{false, true} {
		name, action, expected := "returns", "callbackbridge.RecordDone()", "ok"
		expectedCompleted := int32(1)
		if panics {
			name, action, expected = "synchronous-recover", `panic("retained sync panic")`, "retained sync panic"
			expectedCompleted = 0
		}
		t.Run(name, func(t *testing.T) {
			source := `package main
import ("fmt"; "callbackbridge")
func install(done chan struct{}) {
 callbackbridge.Keep([]int{2, 1}, func(i, j int) bool {
  callbackbridge.Recorder().Mark() // callback pause
  ` + action + ` // callback step
  return i < j
 })
 close(done) // creator pause
}
func main() {
 defer func() { if value := recover(); value != nil { fmt.Print(value) } }()
 done := make(chan struct{})
 go install(done)
 <-done
 callbackbridge.Invoke() // main pause
 fmt.Print("ok")
}
`
			var retained func(int, int) bool
			var lock sync.Mutex
			var completed atomic.Int32
			recorder := &opaqueSourceStackRecorder{frames: make(chan []interp.SourceFrame, 1)}
			fixture := newNativeProvenanceDebugger(t, source, interp.Exports{"callbackbridge/callbackbridge": {
				// This has exactly sort.Slice's signature, but its retention
				// behavior is different. Type/name matching cannot grant trust.
				"Keep": reflect.ValueOf(func(_ interface{}, callback func(int, int) bool) {
					lock.Lock()
					retained = callback
					lock.Unlock()
				}),
				"Invoke": reflect.ValueOf(func() {
					lock.Lock()
					callback := retained
					lock.Unlock()
					callback(0, 1)
				}),
				"Recorder":   reflect.ValueOf(func() *opaqueSourceStackRecorder { return recorder }),
				"RecordDone": reflect.ValueOf(func() { completed.Add(1) }),
			}}, nil, "creator pause", "main pause", "callback pause")
			if err := fixture.debugger.Continue(1); err != nil {
				t.Fatal(err)
			}
			creator := fixture.next(t, "breakpoint")
			if creator.Kind != "goroutine" || creator.GoRoutine == 1 {
				t.Fatalf("registrar did not run on its own interpreted owner: %+v", creator)
			}
			if err := fixture.debugger.Continue(creator.GoRoutine); err != nil {
				t.Fatal(err)
			}
			main := fixture.next(t, "breakpoint")
			if main.GoRoutine != 1 {
				t.Fatalf("main did not reach its invocation barrier: %+v", main)
			}
			fixture.waitRoutines(t, func(routines []*interp.DebugGoRoutine) bool { return len(routines) == 1 && routines[0].ID() == 1 })
			if err := fixture.debugger.Continue(1); err != nil {
				t.Fatal(err)
			}
			callback := fixture.next(t, "breakpoint")
			requireOpaqueDebugEvent(t, callback)
			if callback.GoRoutine == 1 || callback.GoRoutine == creator.GoRoutine || len(callback.Frames) != 1 {
				t.Fatalf("retained argument reused a different or exited execution: %+v", callback)
			}
			if err := fixture.debugger.Step(callback.GoRoutine, interp.DebugStepOver); err != nil {
				t.Fatal(err)
			}
			stepped := fixture.next(t, "stepOver")
			requireOpaqueDebugEvent(t, stepped)
			if stepped.GoRoutine != callback.GoRoutine || stepped.Frames[0].Line == callback.Frames[0].Line {
				t.Fatalf("retained callback cannot step using its actual live owner: %+v", stepped)
			}
			if err := fixture.debugger.Continue(callback.GoRoutine); err != nil {
				t.Fatal(err)
			}
			if _, err := fixture.debugger.Wait(); err != nil || fixture.stdout.String() != expected {
				t.Fatalf("retained callback lost synchronous return/recover semantics: output=%q error=%v", fixture.stdout.String(), err)
			}
			if fixture.entered.Load() != 1 || fixture.exited.Load() != 1 || len(fixture.debugger.GoRoutines()) != 0 || completed.Load() != expectedCompleted {
				t.Fatalf("retained callback ownership/body did not drain: entered=%d exited=%d completed=%d", fixture.entered.Load(), fixture.exited.Load(), completed.Load())
			}
			requireOnlyCallbackSource(t, recorder, source, 1)
		})
	}
}

func TestDebugRetainedNativeArgumentWhileRegistrarStillBlocked(t *testing.T) {
	source := `package main
import "callbackbridge"
func install(done chan struct{}) {
 callbackbridge.KeepAndWait([]int{2, 1}, func(i, j int) bool {
  callbackbridge.Recorder().Mark() // callback pause
  callbackbridge.RecordDone() // callback step
  return i < j
 })
 close(done)
}
func invoke(done chan struct{}) { callbackbridge.Invoke(); done <- struct{}{} }
func main() {
 installed := make(chan struct{})
 go install(installed)
 callbackbridge.WaitRegistered()
 done := make(chan struct{})
 go invoke(done)
 go invoke(done)
 <-done
 <-done
 callbackbridge.Release()
 <-installed
}
`
	registered, release := make(chan struct{}), make(chan struct{})
	var releaseOnce sync.Once
	unblock := func() { releaseOnce.Do(func() { close(release) }) }
	var retained func(int, int) bool
	var lock sync.Mutex
	var held atomic.Bool
	var completed atomic.Int32
	recorder := &opaqueSourceStackRecorder{frames: make(chan []interp.SourceFrame, 2)}
	fixture := newNativeProvenanceDebugger(t, source, interp.Exports{"callbackbridge/callbackbridge": {
		"KeepAndWait": reflect.ValueOf(func(_ interface{}, callback func(int, int) bool) {
			lock.Lock()
			retained = callback
			lock.Unlock()
			held.Store(true)
			close(registered)
			<-release
			held.Store(false)
		}),
		"WaitRegistered": reflect.ValueOf(func() { <-registered }),
		"Invoke": reflect.ValueOf(func() {
			lock.Lock()
			callback := retained
			lock.Unlock()
			callback(0, 1)
		}),
		"Release":    reflect.ValueOf(unblock),
		"Recorder":   reflect.ValueOf(func() *opaqueSourceStackRecorder { return recorder }),
		"RecordDone": reflect.ValueOf(func() { completed.Add(1) }),
	}}, unblock, "callback pause")
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	first, second := fixture.next(t, "breakpoint"), fixture.next(t, "breakpoint")
	requireOpaqueDebugEvent(t, first)
	requireOpaqueDebugEvent(t, second)
	if !held.Load() || first.GoRoutine == second.GoRoutine || len(first.Frames) != 1 || len(second.Frames) != 1 {
		t.Fatalf("overlapping dispatches reused the active registrar or caller stack: first=%+v second=%+v held=%v", first, second, held.Load())
	}
	if err := fixture.debugger.Step(first.GoRoutine, interp.DebugStepOver); err != nil {
		t.Fatal(err)
	}
	stepped := fixture.next(t, "stepOver")
	requireOpaqueDebugEvent(t, stepped)
	if stepped.GoRoutine != first.GoRoutine || stepped.Frames[0].Line == first.Frames[0].Line {
		t.Fatalf("one retained callback could not step independently: %+v", stepped)
	}
	if err := fixture.debugger.Continue(second.GoRoutine); err != nil {
		t.Fatal(err)
	}
	fixture.waitRoutines(t, func(routines []*interp.DebugGoRoutine) bool {
		firstLive, secondLive := false, false
		for _, routine := range routines {
			firstLive = firstLive || routine.ID() == first.GoRoutine
			secondLive = secondLive || routine.ID() == second.GoRoutine
		}
		return firstLive && !secondLive
	})
	if !held.Load() || completed.Load() != 1 {
		t.Fatal("resuming a callback released the registrar or the other stopped callback")
	}
	if err := fixture.debugger.Continue(first.GoRoutine); err != nil {
		t.Fatal(err)
	}
	if _, err := fixture.debugger.Wait(); err != nil {
		t.Fatal(err)
	}
	if held.Load() || completed.Load() != 2 || fixture.entered.Load() != 2 || fixture.exited.Load() != 2 || len(fixture.debugger.GoRoutines()) != 0 {
		t.Fatalf("overlapping retained callbacks did not leave exactly once: held=%v completed=%d entered=%d exited=%d", held.Load(), completed.Load(), fixture.entered.Load(), fixture.exited.Load())
	}
	requireOnlyCallbackSource(t, recorder, source, 2)
}

func TestDebugRetainedNativeArgumentExternalPanicFailsEpoch(t *testing.T) {
	const source = `package main
import "callbackbridge"
func main() {
 callbackbridge.Keep(func() { panic("retained external panic") })
 callbackbridge.Start()
 select {}
}
`
	var retained func()
	fixture := newNativeProvenanceDebugger(t, source, interp.Exports{"callbackbridge/callbackbridge": {
		"Keep":  reflect.ValueOf(func(callback func()) { retained = callback }),
		"Start": reflect.ValueOf(func() { callback := retained; go callback() }),
	}}, nil)
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err := fixture.debugger.Wait(); err == nil || !strings.Contains(err.Error(), "retained external panic") {
		t.Fatalf("external retained callback panic escaped its owning epoch: %v", err)
	}
	if fixture.entered.Load() != 1 || fixture.exited.Load() != 1 || len(fixture.debugger.GoRoutines()) != 0 {
		t.Fatalf("external retained callback owner did not drain: entered=%d exited=%d", fixture.entered.Load(), fixture.exited.Load())
	}
}

func TestDebugTrustedNativeCallbackContractsKeepActualCaller(t *testing.T) {
	for _, item := range []struct{ name, body, output string }{
		{"stable", `values := []int{2, 1}
 sort.SliceStable(values, func(i, j int) bool {
  return values[i] < values[j] // trusted pause
 })
 fmt.Print(values)`, "[1 2]"},
		{"search", `index := sort.Search(1, func(i int) bool {
  return true // trusted pause
 })
 fmt.Print(index)`, "0"},
	} {
		t.Run(item.name, func(t *testing.T) {
			source := "package main\nimport (\"fmt\"; \"sort\")\nfunc main() {\n " + item.body + "\n}\n"
			fixture := newNativeProvenanceDebugger(t, source, nil, nil, "trusted pause")
			if err := fixture.debugger.Continue(1); err != nil {
				t.Fatal(err)
			}
			paused := fixture.next(t, "breakpoint")
			if paused.GoRoutine != 1 || paused.Kind != "goroutine" || paused.OpaqueNativeBoundary || len(fixture.debugger.GoRoutines()) != 1 {
				t.Fatalf("trusted native callback lost its actual dispatch owner: %+v", paused)
			}
			if err := fixture.debugger.Continue(1); err != nil {
				t.Fatal(err)
			}
			if _, err := fixture.debugger.Wait(); err != nil || fixture.stdout.String() != item.output || fixture.entered.Load() != 0 {
				t.Fatalf("trusted native callback failed: output=%q error=%v entered=%d", fixture.stdout.String(), err, fixture.entered.Load())
			}
		})
	}
}

func TestDebugNativeGoCallbackDoesNotClaimLaunchingOwner(t *testing.T) {
	const source = `package main
import ("sort"; "callbackbridge")
func main() {
 values := []int{2, 1}
 done := make(chan struct{})
 go sort.Slice(values, func(i, j int) bool {
  result := values[i] < values[j] // native go pause
  close(done)
  return result
 })
 <-done
 callbackbridge.Noop() // main drain pause
}
`
	fixture := newNativeProvenanceDebugger(t, source, interp.Exports{"callbackbridge/callbackbridge": {
		"Noop": reflect.ValueOf(func() {}),
	}}, nil, "native go pause", "main drain pause")
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	paused := fixture.next(t, "breakpoint")
	requireOpaqueDebugEvent(t, paused)
	if paused.GoRoutine == 1 || len(paused.Frames) != 1 {
		t.Fatalf("compiled go dispatch claimed its launching source owner: %+v", paused)
	}
	if err := fixture.debugger.Continue(paused.GoRoutine); err != nil {
		t.Fatal(err)
	}
	main := fixture.next(t, "breakpoint")
	if main.GoRoutine != 1 {
		t.Fatalf("compiled worker did not reach the main drain barrier: %+v", main)
	}
	fixture.waitRoutines(t, func(routines []*interp.DebugGoRoutine) bool {
		return len(routines) == 1 && routines[0].ID() == 1 && fixture.stoppedEvent.Load().WithStoppedValues(func() {})
	})
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err := fixture.debugger.Wait(); err != nil || fixture.entered.Load() != 1 || fixture.exited.Load() != 1 {
		t.Fatalf("compiled go callback did not drain: error=%v entered=%d exited=%d", err, fixture.entered.Load(), fixture.exited.Load())
	}
}

func TestDebugStoppedScalarSnapshotExcludesNewCallbackEntry(t *testing.T) {
	const source = `package main
import ("fmt"; "callbackbridge")
func main() {
 value := 42
 callbackbridge.Keep(func() { value = 99; callbackbridge.Mark() })
 callbackbridge.Noop() // main snapshot pause
 fmt.Print(value)
}
`
	project := t.TempDir()
	writeGoSource(t, filepath.Join(project, "main.go"), source)
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	callbacks := make(chan func(), 1)
	snapshotHeld, readNow, releaseSnapshot := make(chan struct{}), make(chan struct{}), make(chan struct{})
	readResult := make(chan []debugFrame, 1)
	allowedResult := make(chan bool, 1)
	var readOnce, releaseOnce sync.Once
	startRead := func() { readOnce.Do(func() { close(readNow) }) }
	finishRead := func() { releaseOnce.Do(func() { close(releaseSnapshot) }) }
	var called atomic.Int32
	var stdout outputBuffer
	interpreter := interp.New(interp.Options{GoPath: ".", SourcecodeFilesystem: projectSourceFS{root: os.DirFS(project), entryDir: "."}, Stdout: &stdout})
	for _, exports := range []interp.Exports{stdlib.Symbols, {"callbackbridge/callbackbridge": {
		"Keep": reflect.ValueOf(func(callback func()) { callbacks <- callback }),
		"Noop": reflect.ValueOf(func() {}),
		"Mark": reflect.ValueOf(func() { called.Add(1) }),
	}}} {
		if err := interpreter.Use(exports); err != nil {
			t.Fatal(err)
		}
	}
	dbg, err := interpreter.DebugPath(ctx, "qfli-project", func(event *interp.DebugEvent) {
		if event.Reason() != interp.DebugBreak {
			return
		}
		allowed := event.WithStoppedValues(func() {
			close(snapshotHeld)
			<-readNow
			readResult <- snapshotDebugFrames(event, project, true)
			<-releaseSnapshot
		})
		allowedResult <- allowed
	}, &interp.DebugOptions{GoRoutineStartAt1: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { startRead(); finishRead(); dbg.Terminate(); dbg.Wait() })
	results := dbg.SetBreakpoints(interp.AllBreakpointTarget(), interp.LineBreakpoint(debugSourceLine(t, source, "main snapshot pause")))
	if len(results) != 1 || !results[0].Valid {
		t.Fatal("main snapshot breakpoint is invalid")
	}
	if err := dbg.Continue(1); err != nil {
		t.Fatal(err)
	}
	select {
	case <-snapshotHeld:
	case <-ctx.Done():
		t.Fatal("single stopped owner did not acquire the value snapshot guard")
	}
	callback := <-callbacks
	returned := make(chan struct{})
	go func() { defer close(returned); callback() }()
	// The fixture's reader holds the guard. Observe the actual contender in
	// enterRoutine, rather than assuming that a launched goroutine was scheduled.
	// Stack inspection is test synchronization only, never caller provenance.
	deadline := time.Now().Add(3 * time.Second)
	blocked := false
	for time.Now().Before(deadline) {
		stack := make([]byte, 256*1024)
		stack = stack[:runtime.Stack(stack, true)]
		if strings.Contains(string(stack), "(*Debugger).enterRoutine(") {
			blocked = true
			break
		}
		time.Sleep(time.Millisecond)
	}
	if !blocked || called.Load() != 0 {
		t.Fatal("callback entry did not wait behind the stopped-value snapshot")
	}
	startRead()
	var frames []debugFrame
	select {
	case frames = <-readResult:
	case <-ctx.Done():
		t.Fatal("guarded scalar snapshot did not complete")
	}
	found := false
	for _, frame := range frames {
		for _, variable := range frame.Variables {
			found = found || variable.Name == "value" && variable.Value == "42"
		}
	}
	if !found || called.Load() != 0 {
		t.Fatalf("scalar snapshot raced an entering callback: %+v called=%d", frames, called.Load())
	}
	finishRead()
	select {
	case allowed := <-allowedResult:
		if !allowed {
			t.Fatal("ordinary stopped scalar values were unnecessarily suppressed")
		}
	case <-ctx.Done():
		t.Fatal("snapshot guard did not release")
	}
	select {
	case <-returned:
	case <-ctx.Done():
		t.Fatal("callback did not enter after snapshot release")
	}
	if called.Load() != 1 {
		t.Fatal("released callback did not run exactly once")
	}
	if err := dbg.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err := dbg.Wait(); err != nil || stdout.String() != "99" {
		t.Fatalf("snapshot exclusion changed execution: output=%q error=%v", stdout.String(), err)
	}
}

func TestDebugCompiledWorkerMakesStoppedLocalsUnavailable(t *testing.T) {
	const source = `package main
import ("fmt"; "callbackbridge")
func main() {
 value := 42
 go callbackbridge.Hold()
 callbackbridge.WaitEntered()
 callbackbridge.Noop() // main pause
 callbackbridge.Release()
 callbackbridge.WaitFinished()
 fmt.Print(value)
}
`
	entered, release, finished := make(chan struct{}), make(chan struct{}), make(chan struct{})
	var releaseOnce sync.Once
	unblock := func() { releaseOnce.Do(func() { close(release) }) }
	fixture := newNativeProvenanceDebugger(t, source, interp.Exports{"callbackbridge/callbackbridge": {
		"Hold":         reflect.ValueOf(func() { close(entered); <-release; close(finished) }),
		"WaitEntered":  reflect.ValueOf(func() { <-entered }),
		"WaitFinished": reflect.ValueOf(func() { <-finished }),
		"Release":      reflect.ValueOf(unblock),
		"Noop":         reflect.ValueOf(func() {}),
	}}, unblock, "main pause")
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	paused := fixture.next(t, "breakpoint")
	if fixture.valuesAllowed.Load() || len(fixture.debugger.GoRoutines()) != 1 || len(paused.Frames) == 0 {
		t.Fatalf("compiled worker was omitted from scalar snapshot eligibility: %+v", paused)
	}
	for _, frame := range paused.Frames {
		if len(frame.Variables) != 0 || frame.LocalsUnavailableReason == "" {
			t.Fatalf("compiled worker allowed an unsafe scalar read: %+v", frame)
		}
	}
	unblock()
	fixture.waitRoutines(t, func(routines []*interp.DebugGoRoutine) bool {
		return len(routines) == 1 && fixture.stoppedEvent.Load().WithStoppedValues(func() {})
	})
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err := fixture.debugger.Wait(); err != nil || fixture.stdout.String() != "42" {
		t.Fatalf("compiled worker did not drain: output=%q error=%v", fixture.stdout.String(), err)
	}
}

type nativeReplyCodec struct {
	requests  chan uint64
	entered   chan struct{}
	release   chan struct{}
	finished  chan struct{}
	closed    chan struct{}
	closeOnce sync.Once
}

func (codec *nativeReplyCodec) WriteRequest(request *rpc.Request, _ interface{}) error {
	codec.requests <- request.Seq
	return nil
}

func (codec *nativeReplyCodec) ReadResponseHeader(response *rpc.Response) error {
	select {
	case response.Seq = <-codec.requests:
		return nil
	case <-codec.closed:
		return io.EOF
	}
}

func (codec *nativeReplyCodec) ReadResponseBody(reply interface{}) error {
	close(codec.entered)
	select {
	case <-codec.release:
		if reply != nil {
			*reply.(*int) = 99
		}
		close(codec.finished)
		return nil
	case <-codec.closed:
		return io.EOF
	}
}

func (codec *nativeReplyCodec) Close() error {
	codec.closeOnce.Do(func() { close(codec.closed) })
	return nil
}

func requireNativeEscapeSnapshot(t *testing.T, fixture *nativeProvenanceDebugger, paused debugEvent) {
	t.Helper()
	if paused.GoRoutine != 1 || len(fixture.debugger.GoRoutines()) != 1 || fixture.valuesAllowed.Load() || len(paused.Frames) == 0 {
		t.Fatalf("native escape did not suppress sole-owner scalar reads: %+v", paused)
	}
	for _, frame := range paused.Frames {
		if len(frame.Variables) != 0 || frame.LocalsUnavailableReason != "Native code may retain mutable values; locals are unavailable for this session" {
			t.Fatalf("native escape has no explicit unavailable boundary: %+v", frame)
		}
	}
	event := fixture.stoppedEvent.Load()
	if !event.NativeValuesEscaped() || event.WithStoppedValues(func() { t.Error("escaped native alias allowed a scalar read") }) {
		t.Fatal("native escape eligibility was not sticky")
	}
}

func TestDebugRPCAsyncReplyMakesStoppedLocalsUnavailable(t *testing.T) {
	const source = `package main
import ("fmt"; "net/rpc"; "callbackbridge")
func main() {
 var client *rpc.Client = callbackbridge.Client()
 reply := 42
 pending := client.Go("Service.Value", 0, &reply, nil)
 callbackbridge.Noop() // native escape pause
 <-pending.Done
 fmt.Print(reply)
}
`
	codec := &nativeReplyCodec{requests: make(chan uint64, 1), entered: make(chan struct{}), release: make(chan struct{}), finished: make(chan struct{}), closed: make(chan struct{})}
	client := rpc.NewClientWithCodec(codec)
	var releaseOnce sync.Once
	unblock := func() { releaseOnce.Do(func() { close(codec.release) }) }
	fixture := newNativeProvenanceDebugger(t, source, interp.Exports{"callbackbridge/callbackbridge": {
		"Client": reflect.ValueOf(func() *rpc.Client { return client }),
		"Noop":   reflect.ValueOf(func() {}),
	}}, func() { unblock(); client.Close() }, "native escape pause")
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	paused := fixture.next(t, "breakpoint")
	select {
	case <-codec.entered:
	case <-time.After(3 * time.Second):
		t.Fatal("real RPC input goroutine did not hold the reply pointer")
	}
	requireNativeEscapeSnapshot(t, fixture, paused)
	unblock()
	select {
	case <-codec.finished:
	case <-time.After(3 * time.Second):
		t.Fatal("real RPC input goroutine did not mutate its retained reply")
	}
	// Completion does not prove that an arbitrary native API released an alias.
	requireNativeEscapeSnapshot(t, fixture, paused)
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err := fixture.debugger.Wait(); err != nil || fixture.stdout.String() != "99" {
		t.Fatalf("RPC async reply semantics changed: output=%q error=%v", fixture.stdout.String(), err)
	}
}

func TestDebugNativeCallbackResultEscapeMakesStoppedLocalsUnavailable(t *testing.T) {
	const source = `package main
import ("fmt"; "callbackbridge")
func main() {
 value := 42
 callbackbridge.HoldResult(func() interface{} { return &value })
 callbackbridge.Noop() // native escape pause
 callbackbridge.WaitFinished()
 fmt.Print(value)
}
`
	release, finished := make(chan struct{}), make(chan struct{})
	var releaseOnce sync.Once
	unblock := func() { releaseOnce.Do(func() { close(release) }) }
	fixture := newNativeProvenanceDebugger(t, source, interp.Exports{"callbackbridge/callbackbridge": {
		"HoldResult": reflect.ValueOf(func(callback func() interface{}) {
			value := callback().(*int)
			go func() { <-release; *value = 99; close(finished) }()
		}),
		"Noop":         reflect.ValueOf(func() {}),
		"WaitFinished": reflect.ValueOf(func() { <-finished }),
	}}, unblock, "native escape pause")
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	paused := fixture.next(t, "breakpoint")
	requireNativeEscapeSnapshot(t, fixture, paused)
	unblock()
	select {
	case <-finished:
	case <-time.After(3 * time.Second):
		t.Fatal("native code did not mutate the retained callback result")
	}
	requireNativeEscapeSnapshot(t, fixture, paused)
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err := fixture.debugger.Wait(); err != nil || fixture.stdout.String() != "99" || fixture.entered.Load() != 1 || fixture.exited.Load() != 1 {
		t.Fatalf("callback result escape changed execution: output=%q error=%v entered=%d exited=%d", fixture.stdout.String(), err, fixture.entered.Load(), fixture.exited.Load())
	}
}

func TestDebugPureScalarNativeCallsKeepStoppedLocalsAvailable(t *testing.T) {
	const source = `package main
import ("fmt"; "callbackbridge")
func main() {
 value := callbackbridge.Apply(func(value int) int { return value + 1 }, 41)
 fmt.Print("ready", value)
 callbackbridge.Noop() // scalar pause
 fmt.Print(value)
}
`
	fixture := newNativeProvenanceDebugger(t, source, interp.Exports{"callbackbridge/callbackbridge": {
		"Apply": reflect.ValueOf(func(callback func(int) int, value int) int { return callback(value) }),
		"Noop":  reflect.ValueOf(func() {}),
	}}, nil, "scalar pause")
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	paused := fixture.next(t, "breakpoint")
	if !fixture.valuesAllowed.Load() || fixture.stoppedEvent.Load().NativeValuesEscaped() {
		t.Fatalf("pure scalar arguments/results disabled ordinary locals: %+v", paused)
	}
	found := false
	for _, frame := range paused.Frames {
		for _, variable := range frame.Variables {
			found = found || variable.Name == "value" && variable.Value == "42"
		}
	}
	if !found {
		t.Fatalf("ordinary scalar local is unavailable: %+v", paused.Frames)
	}
	if err := fixture.debugger.Continue(1); err != nil {
		t.Fatal(err)
	}
	if _, err := fixture.debugger.Wait(); err != nil || fixture.stdout.String() != "ready4242" {
		t.Fatalf("pure scalar execution changed: output=%q error=%v", fixture.stdout.String(), err)
	}
}
