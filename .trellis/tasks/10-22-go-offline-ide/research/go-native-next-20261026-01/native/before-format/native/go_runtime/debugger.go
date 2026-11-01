package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"sync"
	"unicode/utf8"

	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

const debugMaxEvents = 128
const debugMaxOutput = 64 * 1024

type debugRequest struct {
	ProjectPath string           `json:"projectPath"`
	EntryFile   string           `json:"entryFile"`
	Breakpoints map[string][]int `json:"breakpoints"`
}
type debugCommandRequest struct {
	Command   string `json:"command"`
	GoRoutine int    `json:"goroutineId"`
}
type debugVariable struct {
	Name  string `json:"name"`
	Type  string `json:"type"`
	Value string `json:"value"`
}
type debugFrame struct {
	Name                    string          `json:"name"`
	File                    string          `json:"file"`
	Line                    int             `json:"line"`
	Column                  int             `json:"column"`
	Variables               []debugVariable `json:"variables"`
	LocalsUnavailableReason string          `json:"localsUnavailableReason,omitempty"`
	LocalsTruncated         bool            `json:"localsTruncated,omitempty"`
	OpaqueNativeBoundary    bool            `json:"opaqueNativeBoundary,omitempty"`
}
type debugThread struct {
	ID     int    `json:"id"`
	Paused bool   `json:"paused"`
	Kind   string `json:"kind"`
}
type debugEvent struct {
	Sequence             uint64       `json:"sequence"`
	Reason               string       `json:"reason"`
	GoRoutine            int          `json:"goroutineId"`
	Frames               []debugFrame `json:"frames,omitempty"`
	Message              string       `json:"message,omitempty"`
	FramesTruncated      bool         `json:"framesTruncated,omitempty"`
	Kind                 string       `json:"kind,omitempty"`
	OpaqueNativeBoundary bool         `json:"opaqueNativeBoundary,omitempty"`
}
type debugBreakpoint struct {
	File       string `json:"file"`
	Line       int    `json:"line"`
	ActualLine int    `json:"actualLine"`
	Valid      bool   `json:"valid"`
}
type debugResponse struct {
	OK               bool              `json:"ok"`
	Error            string            `json:"error,omitempty"`
	SessionID        uint64            `json:"sessionId"`
	State            string            `json:"state"`
	Sequence         uint64            `json:"sequence"`
	DroppedThrough   uint64            `json:"droppedThrough"`
	Events           []debugEvent      `json:"events"`
	Breakpoints      []debugBreakpoint `json:"breakpoints"`
	Stdout           string            `json:"stdout"`
	Stderr           string            `json:"stderr"`
	OutputTruncated  bool              `json:"outputTruncated"`
	StdoutTruncated  bool              `json:"stdoutTruncated"`
	StderrTruncated  bool              `json:"stderrTruncated"`
	Threads          []debugThread     `json:"threads"`
	ThreadsTruncated bool              `json:"threadsTruncated,omitempty"`
}

type debugOutput struct {
	sync.Mutex
	data      []byte
	truncated bool
}

func (out *debugOutput) Write(data []byte) (int, error) {
	out.Lock()
	defer out.Unlock()
	out.data = append(out.data, data...)
	if len(out.data) > debugMaxOutput {
		out.data = append([]byte(nil), out.data[len(out.data)-debugMaxOutput:]...)
		for len(out.data) > 0 && !utf8.RuneStart(out.data[0]) {
			out.data = out.data[1:]
		}
		out.truncated = true
	}
	return len(data), nil
}
func (out *debugOutput) snapshot() (string, bool) {
	out.Lock()
	defer out.Unlock()
	return string(out.data), out.truncated
}

type debugSession struct {
	sync.Mutex
	id            uint64
	request       debugRequest
	ctx           context.Context
	cancel        context.CancelFunc
	dbg           *interp.Debugger
	state         string
	sequence      uint64
	dropped       uint64
	events        []debugEvent
	breakpoints   []debugBreakpoint
	paused        map[int]bool
	stopRequested bool
	stdout        debugOutput
	stderr        debugOutput
	done          chan struct{}
}

var debugRegistry = struct {
	sync.Mutex
	sessions map[uint64]*debugSession
	closed   map[uint64]bool
}{sessions: make(map[uint64]*debugSession), closed: make(map[uint64]bool)}

func debugFailure(id uint64, err error) debugResponse {
	return debugResponse{SessionID: id, OK: false, State: "unavailable", Error: err.Error(), Events: []debugEvent{}, Breakpoints: []debugBreakpoint{}}
}

func startGoDebug(id uint64, request debugRequest) debugResponse {
	if id == 0 {
		return debugFailure(id, errors.New("debug session ID must be positive"))
	}
	debugRegistry.Lock()
	if debugRegistry.closed[id] {
		delete(debugRegistry.closed, id)
		debugRegistry.Unlock()
		return debugFailure(id, errors.New("debug session cancelled before registration"))
	}
	if _, exists := debugRegistry.sessions[id]; exists {
		debugRegistry.Unlock()
		return debugFailure(id, errors.New("debug session ID already owned"))
	}
	if len(debugRegistry.sessions) >= 16 {
		debugRegistry.Unlock()
		return debugFailure(id, errors.New("too many debug sessions; close an existing session"))
	}
	ctx, cancel := context.WithCancel(context.Background())
	session := &debugSession{id: id, request: request, ctx: ctx, cancel: cancel, state: "starting", paused: make(map[int]bool), events: []debugEvent{}, breakpoints: []debugBreakpoint{}, done: make(chan struct{})}
	debugRegistry.sessions[id] = session
	debugRegistry.Unlock()
	go session.run()
	return session.snapshot(0)
}

func getGoDebug(id uint64) *debugSession {
	debugRegistry.Lock()
	defer debugRegistry.Unlock()
	return debugRegistry.sessions[id]
}
func pollGoDebug(id, after uint64) debugResponse {
	session := getGoDebug(id)
	if session == nil {
		return debugFailure(id, errors.New("debug session does not exist"))
	}
	return session.snapshot(after)
}
func closeGoDebug(id uint64) debugResponse {
	debugRegistry.Lock()
	session := debugRegistry.sessions[id]
	if session == nil && len(debugRegistry.closed) < 128 {
		debugRegistry.closed[id] = true
	}
	debugRegistry.Unlock()
	if session == nil {
		return debugResponse{OK: true, SessionID: id, State: "closed", Events: []debugEvent{}, Breakpoints: []debugBreakpoint{}}
	}
	session.stop()
	<-session.done
	debugRegistry.Lock()
	if debugRegistry.sessions[id] == session {
		delete(debugRegistry.sessions, id)
	}
	debugRegistry.Unlock()
	response := session.snapshot(0)
	response.State = "closed"
	return response
}

func commandGoDebug(id uint64, request debugCommandRequest) debugResponse {
	session := getGoDebug(id)
	if session == nil {
		return debugFailure(id, errors.New("debug session does not exist"))
	}
	if request.Command == "stop" {
		session.stop()
		return session.snapshot(0)
	}
	session.Lock()
	dbg := session.dbg
	if dbg == nil || session.state == "failed" || session.state == "terminated" || session.stopRequested {
		session.Unlock()
		return debugFailure(id, errors.New("debug session is not ready"))
	}
	gid := request.GoRoutine
	if gid == 0 {
		for candidate := range session.paused {
			if gid == 0 || candidate < gid {
				gid = candidate
			}
		}
	}
	if request.Command == "pause" {
		session.Unlock()
		interrupted := false
		for _, routine := range dbg.GoRoutines() {
			interrupted = dbg.Interrupt(routine.ID(), interp.DebugPause) || interrupted
		}
		if !interrupted {
			return debugFailure(id, errors.New("no live Go routine to pause"))
		}
		return session.snapshot(0)
	}
	if !session.paused[gid] {
		session.Unlock()
		return debugFailure(id, errors.New("select a stopped Go routine"))
	}
	var err error
	switch request.Command {
	case "continue":
		err = dbg.Continue(gid)
	case "stepInto":
		err = dbg.Step(gid, interp.DebugStepInto)
	case "stepOver":
		err = dbg.Step(gid, interp.DebugStepOver)
	case "stepOut":
		err = dbg.Step(gid, interp.DebugStepOut)
	default:
		session.Unlock()
		return debugFailure(id, errors.New("unsupported debug command"))
	}
	if err == nil {
		delete(session.paused, gid)
		if len(session.paused) == 0 {
			session.state = "running"
		}
	}
	session.Unlock()
	if err != nil {
		return debugFailure(id, err)
	}
	return session.snapshot(0)
}

func (session *debugSession) stop() {
	session.Lock()
	session.stopRequested = true
	if session.state != "failed" && session.state != "terminated" {
		session.state = "stopping"
	}
	dbg := session.dbg
	session.Unlock()
	session.cancel()
	if dbg != nil {
		dbg.Terminate()
	}
}
func (session *debugSession) append(event debugEvent) {
	if len(event.Message) > 2048 {
		event.Message = event.Message[:2048]
		for !utf8.ValidString(event.Message) {
			event.Message = event.Message[:len(event.Message)-1]
		}
		event.Message += "…"
	}
	session.sequence++
	event.Sequence = session.sequence
	session.events = append(session.events, event)
	if len(session.events) > debugMaxEvents {
		session.dropped = session.events[0].Sequence
		session.events = append([]debugEvent(nil), session.events[1:]...)
	}
}
func (session *debugSession) snapshot(after uint64) debugResponse {
	session.Lock()
	response := debugResponse{OK: true, SessionID: session.id, State: session.state, Sequence: session.sequence, DroppedThrough: session.dropped, Events: []debugEvent{}, Breakpoints: append([]debugBreakpoint{}, session.breakpoints...)}
	for _, event := range session.events {
		if event.Sequence > after {
			response.Events = append(response.Events, event)
		}
	}
	if session.dbg != nil && session.state != "terminated" && session.state != "failed" {
		for _, routine := range session.dbg.GoRoutines() {
			if len(response.Threads) >= 128 {
				response.ThreadsTruncated = true
				break
			}
			response.Threads = append(response.Threads, debugThread{ID: routine.ID(), Paused: session.paused[routine.ID()], Kind: routine.Kind()})
		}
	}
	session.Unlock()
	var stdoutTruncated, stderrTruncated bool
	response.Stdout, stdoutTruncated = session.stdout.snapshot()
	response.Stderr, stderrTruncated = session.stderr.snapshot()
	response.OutputTruncated = stdoutTruncated || stderrTruncated
	response.StdoutTruncated, response.StderrTruncated = stdoutTruncated, stderrTruncated
	return response
}
func (session *debugSession) fail(err error) {
	session.Lock()
	if session.stopRequested {
		session.state = "terminated"
	} else {
		session.state = "failed"
	}
	session.append(debugEvent{Reason: session.state, Message: err.Error()})
	session.Unlock()
}

func (session *debugSession) run() {
	defer close(session.done)
	defer session.cancel()
	defer func() {
		if recovered := recover(); recovered != nil {
			session.fail(fmt.Errorf("debugger panic: %v", recovered))
		}
	}()
	count := 0
	for _, lines := range session.request.Breakpoints {
		count += len(lines)
	}
	if count > 256 {
		session.fail(errors.New("at most 256 breakpoints are supported"))
		return
	}
	project, entry, packagePath, excluded, err := prepareDebugProject(session.request)
	if err != nil {
		session.fail(err)
		return
	}
	// Validate all launch inputs before imports can run dependency initializers.
	for file, lines := range session.request.Breakpoints {
		if _, err := containedDebugFile(project, file); err != nil {
			session.fail(err)
			return
		}
		for _, line := range lines {
			if line < 1 || line > 1000000 {
				session.fail(errors.New("breakpoint line out of range"))
				return
			}
		}
	}
	interpreter := interp.New(interp.Options{GoPath: ".", SourcecodeFilesystem: projectSourceFS{root: os.DirFS(project), entryDir: packagePath, excluded: excluded}, Stdout: &session.stdout, Stderr: &session.stderr, Args: []string{entry}})
	if err = interpreter.Use(stdlib.Symbols); err != nil {
		session.fail(err)
		return
	}
	if err = useProjectEnvironment(interpreter, project, filepath.Dir(entry)); err != nil {
		session.fail(err)
		return
	}
	dbg, err := interpreter.DebugPath(session.ctx, path.Join("qfli-project", packagePath), session.handleEvent, &interp.DebugOptions{GoRoutineStartAt1: true})
	if err != nil {
		session.fail(err)
		return
	}
	defer func() { dbg.Terminate(); dbg.Wait() }()
	abort := func(err error) { dbg.Terminate(); dbg.Wait(); session.fail(err) }
	files := make([]string, 0, len(session.request.Breakpoints))
	for file := range session.request.Breakpoints {
		files = append(files, file)
	}
	sort.Strings(files)
	var breakpoints []debugBreakpoint
	for _, file := range files {
		absolute, err := containedDebugFile(project, file)
		if err != nil {
			abort(err)
			return
		}
		relative, _ := filepath.Rel(project, absolute)
		var requests []interp.BreakpointRequest
		for _, line := range session.request.Breakpoints[file] {
			if line < 1 || line > 1000000 || len(requests) >= 256 {
				abort(errors.New("breakpoint line/count out of range"))
				return
			}
			requests = append(requests, interp.LineBreakpoint(line))
		}
		results := dbg.SetBreakpoints(interp.PathBreakpointTarget(path.Join(virtualProject, filepath.ToSlash(relative))), requests...)
		for index, result := range results {
			breakpoints = append(breakpoints, debugBreakpoint{File: filepath.ToSlash(relative), Line: session.request.Breakpoints[file][index], ActualLine: result.Position.Line, Valid: result.Valid})
		}
	}
	session.Lock()
	session.dbg = dbg
	session.breakpoints = breakpoints
	stop := session.stopRequested
	session.Unlock()
	if stop {
		dbg.Terminate()
	} else if err = dbg.Step(1, interp.DebugEntry); err != nil {
		abort(err)
		return
	}
	_, err = dbg.Wait()
	session.Lock()
	if err != nil && !session.stopRequested {
		session.state = "failed"
		session.append(debugEvent{Reason: "failed", Message: err.Error()})
	} else {
		session.state = "terminated"
		session.append(debugEvent{Reason: "terminated"})
	}
	session.paused = make(map[int]bool)
	session.Unlock()
}

func prepareDebugProject(request debugRequest) (project, entry, packagePath string, excluded map[string]bool, err error) {
	project, err = filepath.Abs(request.ProjectPath)
	if err != nil {
		return
	}
	project, err = filepath.EvalSymlinks(project)
	if err != nil {
		return
	}
	entry, err = containedDebugFile(project, request.EntryFile)
	if err != nil {
		return
	}
	facts, parseErr := parseFileFacts(entry)
	if parseErr != nil {
		err = parseErr
		return
	}
	if !facts.isRunnableEntry() {
		err = errors.New("selected Go file has no main function")
		return
	}
	directory := filepath.Dir(entry)
	packagePath, err = filepath.Rel(project, directory)
	packagePath = filepath.ToSlash(packagePath)
	if err != nil {
		return
	}
	competing, readErr := competingMainFiles(directory, filepath.Base(entry))
	if readErr != nil {
		err = readErr
		return
	}
	excluded = make(map[string]bool)
	for _, file := range competing {
		excluded[file] = true
	}
	return
}
func containedDebugFile(project, file string) (string, error) {
	if !filepath.IsAbs(file) {
		file = filepath.Join(project, file)
	}
	absolute, err := filepath.Abs(file)
	if err != nil {
		return "", err
	}
	absolute, err = filepath.EvalSymlinks(absolute)
	if err != nil {
		return "", err
	}
	relative, err := filepath.Rel(project, absolute)
	if err != nil || relative == ".." || strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		return "", errors.New("debug file is outside the project")
	}
	if !strings.HasSuffix(absolute, ".go") {
		return "", errors.New("debug file must be Go source")
	}
	return absolute, nil
}

func (session *debugSession) handleEvent(event *interp.DebugEvent) {
	if event.Reason() == interp.DebugExitGoRoutine {
		session.Lock()
		delete(session.paused, event.GoRoutine())
		if !session.stopRequested && session.state == "paused" && len(session.paused) == 0 {
			session.state = "running"
		}
		session.Unlock()
		return
	}
	reason := ""
	switch event.Reason() {
	case interp.DebugEntry:
		reason = "entry"
	case interp.DebugBreak:
		reason = "breakpoint"
	case interp.DebugPause:
		reason = "pause"
	case interp.DebugStepInto:
		reason = "stepInto"
	case interp.DebugStepOver:
		reason = "stepOver"
	case interp.DebugStepOut:
		reason = "stepOut"
	default:
		return
	}
	var frames []debugFrame
	if !event.WithStoppedValues(func() {
		frames = snapshotDebugFrames(event, session.request.ProjectPath, true)
	}) {
		frames = snapshotDebugFrames(event, session.request.ProjectPath, false)
	}
	session.Lock()
	defer session.Unlock()
	if session.stopRequested {
		return
	}
	session.state = "paused"
	session.paused[event.GoRoutine()] = true
	session.append(debugEvent{Reason: reason, GoRoutine: event.GoRoutine(), Kind: event.GoRoutineKind(), OpaqueNativeBoundary: event.OpaqueNativeBoundary(), Frames: frames, FramesTruncated: event.FrameDepth() > 32})
}
func snapshotDebugFrames(event *interp.DebugEvent, project string, readValues bool) (frames []debugFrame) {
	if event.OpaqueNativeBoundary() {
		readValues = false
	}
	defer func() {
		if recover() != nil {
			frames = append(frames, debugFrame{Name: "<frame unavailable>"})
		}
	}()
	depth := event.FrameDepth()
	if depth > 32 {
		depth = 32
	}
	for _, frame := range event.Frames(0, depth) {
		position := frame.Position()
		file := position.Filename
		if strings.HasPrefix(file, virtualProject+"/") {
			file = strings.TrimPrefix(file, virtualProject+"/")
		} else if filepath.IsAbs(file) {
			if relative, err := filepath.Rel(project, file); err == nil {
				file = filepath.ToSlash(relative)
			}
		}
		value := debugFrame{Name: frame.Name(), File: file, Line: position.Line, Column: position.Column, Variables: []debugVariable{}, OpaqueNativeBoundary: frame.OpaqueNativeBoundary()}
		if !readValues {
			value.LocalsUnavailableReason = "Other Go routines may modify shared values; locals were not read"
			if event.NativeValuesEscaped() {
				value.LocalsUnavailableReason = "Native code may retain mutable values; locals are unavailable for this session"
			}
			if event.OpaqueNativeBoundary() {
				value.LocalsUnavailableReason = "Opaque native callback may capture values outside this stack; locals were not read"
			}
			frames = append(frames, value)
			continue
		}
		for _, scope := range frame.Scopes() {
			for _, variable := range scope.Variables() {
				if len(value.Variables) >= 100 {
					value.LocalsTruncated = true
					break
				}
				if variable.Value.IsValid() {
					text := "<存在其他 Go routine，未读取共享值>"
					if readValues {
						text = debugReflectValue(variable.Value)
					}
					value.Variables = append(value.Variables, debugVariable{Name: variable.Name, Type: variable.Value.Type().String(), Value: text})
				}
			}
		}
		sort.Slice(value.Variables, func(i, j int) bool { return value.Variables[i].Name < value.Variables[j].Name })
		frames = append(frames, value)
	}
	return
}
func debugReflectValue(value reflect.Value) string {
	var text string
	switch value.Kind() {
	case reflect.String:
		text = strconv.Quote(value.String())
	case reflect.Bool:
		text = strconv.FormatBool(value.Bool())
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		text = strconv.FormatInt(value.Int(), 10)
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
		text = strconv.FormatUint(value.Uint(), 10)
	case reflect.Float32, reflect.Float64:
		text = strconv.FormatFloat(value.Float(), 'g', -1, value.Type().Bits())
	default:
		text = "<" + value.Type().String() + ">"
	}
	if len(text) > 512 {
		text = text[:512]
		for !utf8.ValidString(text) {
			text = text[:len(text)-1]
		}
		text += "…"
	}
	return text
}
