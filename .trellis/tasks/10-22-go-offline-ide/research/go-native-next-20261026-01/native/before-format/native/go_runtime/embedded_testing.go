package main

// Embedded testing deliberately does not call testing.Main, M.Run, flag.Parse,
// or os.Exit. T/F are a documented in-process subset: assertions, synchronous
// subtests, logs, cleanup, TempDir and Add-based fuzz seeds. Parallel scheduling,
// global environment/chdir changes, mutation fuzzing, coverage and race analysis
// are unsupported. Benchmarks use real testing.Benchmark and testing.PB through
// a safety wrapper, so the reported measurements come from Go's benchmark loop.
import (
	"context"
	"fmt"
	"io"
	"os"
	"path"
	"path/filepath"
	"reflect"
	"runtime"
	"sort"
	"strings"
	"sync"
	"testing"
	"time"
	"unicode"
	"unicode/utf8"

	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

type testExecution struct {
	Engine        string `json:"engine"`
	TestsRun      int    `json:"testsRun"`
	TestsPassed   int    `json:"testsPassed"`
	TestsFailed   int    `json:"testsFailed"`
	TestsSkipped  int    `json:"testsSkipped"`
	BenchmarksRun int    `json:"benchmarksRun"`
	FuzzSeedsRun  int    `json:"fuzzSeedsRun"`
}

type embeddedTestSuite struct {
	ctx            context.Context
	root           string
	stdout         io.Writer
	executionError func() error
	mutex          sync.Mutex
	evidence       testExecution
	failed         bool
}

func (suite *embeddedTestSuite) log(format string, args ...any) {
	fmt.Fprintf(suite.stdout, format, args...)
}

func (suite *embeddedTestSuite) markFailed() {
	suite.mutex.Lock()
	suite.failed = true
	suite.mutex.Unlock()
}

func (suite *embeddedTestSuite) snapshot() (testExecution, bool) {
	suite.mutex.Lock()
	defer suite.mutex.Unlock()
	return suite.evidence, suite.failed
}

type embeddedT struct {
	suite    *embeddedTestSuite
	name     string
	ctx      context.Context
	mutex    sync.Mutex
	failed   bool
	skipped  bool
	cleanups []func()
	names    map[string]int
	source   embeddedAttribution
}

func (t *embeddedT) Name() string { return t.name }

// The interpreter supplies Helper's source identity through CallWithSource.
func (t *embeddedT) Helper()                     {}
func (t *embeddedT) Context() context.Context    { return t.ctx }
func (t *embeddedT) Deadline() (time.Time, bool) { return t.ctx.Deadline() }
func (t *embeddedT) Log(args ...any)             { t.Logf("%s", fmt.Sprint(args...)) }
func (t *embeddedT) Logf(f string, args ...any) {
	t.suite.log("    %s: %s\n", t.name, fmt.Sprintf(f, args...))
}
func (t *embeddedT) Error(args ...any)            { t.Log(args...); t.Fail() }
func (t *embeddedT) Errorf(f string, args ...any) { t.Logf(f, args...); t.Fail() }
func (t *embeddedT) Fatal(args ...any)            { t.Error(args...); t.FailNow() }
func (t *embeddedT) Fatalf(f string, args ...any) { t.Errorf(f, args...); t.FailNow() }
func (t *embeddedT) Skip(args ...any)             { t.Log(args...); t.SkipNow() }
func (t *embeddedT) Skipf(f string, args ...any)  { t.Logf(f, args...); t.SkipNow() }
func (t *embeddedT) Parallel()                    { t.Fatal("testing.T.Parallel is unsupported by embedded testing") }
func (t *embeddedT) Setenv(key, value string) {
	t.Fatal("testing.T.Setenv is unsupported: process environment is shared")
}
func (t *embeddedT) Chdir(dir string) {
	t.Fatal("testing.T.Chdir is unsupported: process working directory is shared")
}
func (t *embeddedT) Attr(key, value string) { t.Logf("%s=%s", key, value) }

// Helper registrations belong to the individual T/F/B. Call stacks are passed
// as immutable invocation data, so simultaneous callers never overwrite a
// shared current location on the test object.
type embeddedAttribution struct {
	mutex   sync.Mutex
	helpers map[int64]bool
}

func embeddedSourceMethod(method string) bool {
	switch method {
	case "Helper", "Log", "Logf", "Error", "Errorf", "Fatal", "Fatalf", "Skip", "Skipf":
		return true
	}
	return false
}

func (t *embeddedT) SourceMethodEnabled(method string) bool { return embeddedSourceMethod(method) }

func (a *embeddedAttribution) call(method string, stack []interp.SourceFrame, in []reflect.Value, log func(string), fail, skip func()) bool {
	if method == "Helper" {
		if len(stack) > 0 {
			a.mutex.Lock()
			if a.helpers == nil {
				a.helpers = make(map[int64]bool)
			}
			a.helpers[stack[0].FunctionID] = true
			a.mutex.Unlock()
		}
		return true
	}
	var message string
	switch method {
	case "Log", "Error", "Fatal", "Skip":
		message = fmt.Sprint(in[0].Interface().([]any)...)
	case "Logf", "Errorf", "Fatalf", "Skipf":
		message = fmt.Sprintf(in[0].String(), in[1].Interface().([]any)...)
	default:
		return false
	}
	a.mutex.Lock()
	for index, frame := range stack {
		if !a.helpers[frame.FunctionID] || index == len(stack)-1 {
			message = fmt.Sprintf("%s:%d: %s", filepath.Base(frame.Filename), frame.Line, message)
			break
		}
	}
	a.mutex.Unlock()
	log(message)
	switch method {
	case "Error", "Errorf":
		fail()
	case "Fatal", "Fatalf":
		fail()
		runtime.Goexit()
	case "Skip", "Skipf":
		skip()
	}
	return true
}

func (t *embeddedT) CallWithSource(method string, stack []interp.SourceFrame, in []reflect.Value) ([]reflect.Value, bool) {
	return nil, t.source.call(method, stack, in, func(message string) { t.Log(message) }, t.Fail, t.SkipNow)
}

func (t *embeddedT) Fail() {
	t.mutex.Lock()
	t.failed = true
	t.mutex.Unlock()
	t.suite.markFailed()
}

func (t *embeddedT) Failed() bool {
	t.mutex.Lock()
	defer t.mutex.Unlock()
	return t.failed
}

func (t *embeddedT) Skipped() bool {
	t.mutex.Lock()
	defer t.mutex.Unlock()
	return t.skipped
}

// Goexit ends only the dedicated test goroutine. Unlike a panic sentinel, it
// cannot be swallowed by an interpreted recover and it still executes defers.
func (t *embeddedT) FailNow() { t.Fail(); runtime.Goexit() }
func (t *embeddedT) SkipNow() {
	t.mutex.Lock()
	t.skipped = true
	t.mutex.Unlock()
	runtime.Goexit()
}

func (t *embeddedT) Cleanup(cleanup func()) {
	if cleanup == nil {
		t.Fatal("testing.Cleanup requires a function")
	}
	t.mutex.Lock()
	t.cleanups = append(t.cleanups, cleanup)
	t.mutex.Unlock()
}

func (t *embeddedT) TempDir() string {
	directory, err := os.MkdirTemp(t.suite.root, ".qfli-test-")
	if err != nil {
		t.Fatalf("TempDir: %v", err)
	}
	t.Cleanup(func() {
		if err := os.RemoveAll(directory); err != nil {
			t.Errorf("TempDir cleanup: %v", err)
		}
	})
	return directory
}

func (t *embeddedT) Run(name string, body func(*embeddedT)) bool {
	name = strings.Map(func(r rune) rune {
		if unicode.IsSpace(r) {
			return '_'
		}
		return r
	}, name)
	t.mutex.Lock()
	if t.names == nil {
		t.names = make(map[string]int)
	}
	count := t.names[name]
	t.names[name]++
	t.mutex.Unlock()
	if name == "" || count > 0 {
		name = fmt.Sprintf("%s#%02d", name, count)
	}
	child := t.suite.runCase(t.name+"/"+name, func(child *embeddedT) { body(child) })
	if child.Failed() {
		t.Fail()
	}
	return !child.Failed()
}

// Isolate each body and each cleanup so Fatal/Skip/Goexit cannot terminate the
// host app or prevent the remaining LIFO cleanup functions from running.
func (t *embeddedT) invoke(body func()) {
	done := make(chan struct{})
	go func() {
		completed := false
		defer func() {
			if value := recover(); value != nil {
				t.Errorf("panic: %v", value)
			} else if !completed && !t.Failed() && !t.Skipped() {
				t.Error("test goroutine exited without completing")
			}
			if t.suite.executionError != nil {
				if failure := t.suite.executionError(); failure != nil {
					t.Errorf("execution interrupted: %v", failure)
				}
			}
			close(done)
		}()
		interp.RunNativeCallback(body)
		completed = true
	}()
	select {
	case <-done:
	case <-t.ctx.Done():
		t.Errorf("cancelled: %v", t.ctx.Err())
	}
}

func (suite *embeddedTestSuite) runCase(name string, body func(*embeddedT)) *embeddedT {
	t := &embeddedT{suite: suite, name: name, ctx: suite.ctx}
	suite.log("=== RUN   %s\n", name)
	t.invoke(func() { body(t) })
	for {
		t.mutex.Lock()
		last := len(t.cleanups) - 1
		if last < 0 {
			t.mutex.Unlock()
			break
		}
		cleanup := t.cleanups[last]
		t.cleanups = t.cleanups[:last]
		t.mutex.Unlock()
		t.invoke(cleanup)
	}
	status := "PASS"
	if t.Failed() {
		status = "FAIL"
	} else if t.Skipped() {
		status = "SKIP"
	}
	suite.log("--- %s: %s\n", status, name)
	return t
}

type embeddedF struct {
	*embeddedT
	seeds  [][]reflect.Value
	fuzzed bool
}

func (f *embeddedF) Add(args ...any) {
	if f.fuzzed {
		f.Fatal("testing.F.Add must precede Fuzz")
	}
	seed := make([]reflect.Value, len(args))
	for index, arg := range args {
		value := reflect.ValueOf(arg)
		if !value.IsValid() || !validFuzzType(value.Type()) {
			f.Fatalf("unsupported fuzz seed type %T", arg)
		}
		if bytes, ok := arg.([]byte); ok {
			value = reflect.ValueOf(append([]byte(nil), bytes...))
		}
		seed[index] = value
	}
	f.seeds = append(f.seeds, seed)
}

func validFuzzType(value reflect.Type) bool {
	if value == reflect.TypeOf([]byte(nil)) {
		return true
	}
	if value.PkgPath() != "" {
		return false
	}
	switch value.Kind() {
	case reflect.Bool, reflect.String, reflect.Int, reflect.Int8, reflect.Int16,
		reflect.Int32, reflect.Int64, reflect.Uint, reflect.Uint8, reflect.Uint16,
		reflect.Uint32, reflect.Uint64, reflect.Float32, reflect.Float64:
		return true
	}
	return false
}

func (f *embeddedF) Fuzz(target any) {
	if f.fuzzed {
		f.Fatal("testing.F.Fuzz must be called exactly once")
	}
	f.fuzzed = true
	function := reflect.ValueOf(target)
	if !function.IsValid() || function.Kind() != reflect.Func || function.IsNil() {
		f.Fatal("testing.F.Fuzz requires a function")
	}
	typeOf := function.Type()
	if typeOf.NumIn() < 2 || typeOf.NumOut() != 0 || typeOf.IsVariadic() || typeOf.In(0) != reflect.TypeOf((*embeddedT)(nil)) {
		f.Fatal("fuzz target must have signature func(*testing.T, supported seed values...)")
	}
	for index := 1; index < typeOf.NumIn(); index++ {
		if !validFuzzType(typeOf.In(index)) {
			f.Fatalf("unsupported fuzz target parameter %s", typeOf.In(index))
		}
	}
	if len(f.seeds) == 0 {
		f.Fatal("embedded fuzzing requires f.Add seed cases; mutation fuzzing is unavailable")
	}
	nonSkipped := 0
	for index, seed := range f.seeds {
		if len(seed)+1 != typeOf.NumIn() {
			f.Fatal("fuzz seed argument count does not match target")
		}
		for arg, value := range seed {
			if value.Type() != typeOf.In(arg+1) {
				f.Fatalf("fuzz seed type %s does not match %s", value.Type(), typeOf.In(arg+1))
			}
		}
		child := f.suite.runCase(fmt.Sprintf("%s/seed#%d", f.name, index), func(t *embeddedT) {
			f.suite.mutex.Lock()
			f.suite.evidence.FuzzSeedsRun++
			f.suite.mutex.Unlock()
			args := append([]reflect.Value{reflect.ValueOf(t)}, seed...)
			function.Call(args)
		})
		if child.Failed() {
			f.Fail()
		}
		if !child.Skipped() || child.Failed() {
			nonSkipped++
		}
		if f.ctx.Err() != nil {
			return
		}
	}
	if nonSkipped == 0 {
		f.Skip("all fuzz seed cases were skipped")
	}
}

// B and PB are Go's real benchmark engine. The wrapper prevents a panic in a
// RunParallel callback from escaping a Go-owned goroutine into the host process.
type embeddedB struct {
	*testing.B
	suite  *embeddedTestSuite
	name   string
	source embeddedAttribution
}

func (b *embeddedB) Name() string    { return b.name }
func (b *embeddedB) Helper()         {}
func (b *embeddedB) Log(args ...any) { b.suite.log("    %s: %s\n", b.name, fmt.Sprint(args...)) }
func (b *embeddedB) Logf(f string, args ...any) {
	b.suite.log("    %s: %s\n", b.name, fmt.Sprintf(f, args...))
}
func (b *embeddedB) Error(args ...any) { b.Log(args...); b.B.Fail(); b.suite.markFailed() }
func (b *embeddedB) Errorf(f string, args ...any) {
	b.Logf(f, args...)
	b.B.Fail()
	b.suite.markFailed()
}
func (b *embeddedB) Fatal(args ...any)            { b.Error(args...); runtime.Goexit() }
func (b *embeddedB) Fatalf(f string, args ...any) { b.Errorf(f, args...); runtime.Goexit() }
func (b *embeddedB) Fail()                        { b.B.Fail(); b.suite.markFailed() }
func (b *embeddedB) FailNow()                     { b.Fail(); runtime.Goexit() }
func (b *embeddedB) Skip(args ...any)             { b.Log(args...); b.B.SkipNow() }
func (b *embeddedB) Skipf(f string, args ...any)  { b.Logf(f, args...); b.B.SkipNow() }
func (b *embeddedB) CallWithSource(method string, stack []interp.SourceFrame, in []reflect.Value) ([]reflect.Value, bool) {
	return nil, b.source.call(method, stack, in, func(message string) { b.Log(message) }, b.Fail, b.B.SkipNow)
}
func (b *embeddedB) SourceMethodEnabled(method string) bool { return embeddedSourceMethod(method) }
func (b *embeddedB) Setenv(key, value string) {
	b.Fatal("benchmark Setenv is unsupported: process environment is shared")
}
func (b *embeddedB) Chdir(dir string) {
	b.Fatal("benchmark Chdir is unsupported: process working directory is shared")
}
func (b *embeddedB) Context() context.Context { return b.suite.ctx }

func (b *embeddedB) Cleanup(cleanup func()) {
	b.B.Cleanup(func() { b.guard(cleanup) })
}

func (b *embeddedB) guard(body func()) {
	defer func() {
		if value := recover(); value != nil {
			b.Errorf("panic: %v", value)
		}
		if b.suite.executionError != nil {
			if failure := b.suite.executionError(); failure != nil {
				b.Errorf("execution interrupted: %v", failure)
			}
		}
	}()
	if err := b.suite.ctx.Err(); err != nil {
		b.Fatalf("cancelled: %v", err)
	}
	interp.RunNativeCallback(body)
}

func (b *embeddedB) RunParallel(body func(*testing.PB)) {
	b.B.RunParallel(func(pb *testing.PB) { b.guard(func() { body(pb) }) })
}

func (b *embeddedB) Run(name string, body func(*embeddedB)) bool {
	return b.B.Run(name, func(child *testing.B) {
		wrapped := &embeddedB{B: child, suite: b.suite, name: b.name + "/" + name}
		wrapped.guard(func() { body(wrapped) })
	})
}

func (suite *embeddedTestSuite) benchmark(name string, body func(*embeddedB)) (result testing.BenchmarkResult, skipped bool) {
	var last *testing.B
	result = testing.Benchmark(func(b *testing.B) {
		last = b
		wrapped := &embeddedB{B: b, suite: suite, name: name}
		wrapped.guard(func() { body(wrapped) })
		if b.Failed() {
			suite.markFailed()
		}
	})
	// Native benchmark cleanup runs after the callback returns. Inspect its
	// final status too, including Goexit from Fatal inside a cleanup/worker.
	if last != nil && last.Failed() {
		suite.markFailed()
	}
	return result, last != nil && last.Skipped() && !last.Failed()
}

func (suite *embeddedTestSuite) exports() interp.Exports {
	symbols := map[string]reflect.Value{
		"T":       reflect.ValueOf((*embeddedT)(nil)),
		"F":       reflect.ValueOf((*embeddedF)(nil)),
		"B":       reflect.ValueOf((*embeddedB)(nil)),
		"Short":   reflect.ValueOf(func() bool { return false }),
		"Verbose": reflect.ValueOf(func() bool { return true }),
		"Testing": reflect.ValueOf(func() bool { return true }),
		"Benchmark": reflect.ValueOf(func(body func(*embeddedB)) testing.BenchmarkResult {
			result, _ := suite.benchmark("Benchmark", body)
			return result
		}),
	}
	for _, name := range []string{"Init", "Main", "MainStart", "RunTests", "RunBenchmarks", "RunExamples", "RegisterCover", "Coverage", "CoverMode"} {
		operation := name
		symbols[name] = reflect.ValueOf(func(...any) { panic("testing." + operation + " is unsupported by embedded testing") })
	}
	return interp.Exports{"testing/testing": symbols}
}

func isTestFunction(name, prefix string) bool {
	if !strings.HasPrefix(name, prefix) {
		return false
	}
	if name == prefix {
		return true
	}
	r, _ := utf8.DecodeRuneInString(name[len(prefix):])
	return !unicode.IsLower(r)
}

func runGoTestsWithContext(ctx context.Context, project, entry string) (result runResult) {
	var stdout, stderr outputBuffer
	suite := &embeddedTestSuite{
		ctx: ctx, root: project, stdout: &stdout,
		evidence: testExecution{Engine: "qfli-embedded-testing-v1"},
	}
	defer func() {
		if value := recover(); value != nil {
			fmt.Fprintf(&stderr, "embedded test panic: %v\n", value)
			result.ExitCode = 1
		}
		evidence, failed := suite.snapshot()
		result.TestExecution = &evidence
		if failed || ctx.Err() != nil {
			result.ExitCode = 1
		}
		result.Stdout = stdout.String()
		result.Stderr = stderr.String()
	}()
	packagePath, err := filepath.Rel(project, filepath.Dir(entry))
	if err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 127}
	}
	packagePath = filepath.ToSlash(packagePath)
	interpreter := interp.New(interp.Options{
		GoPath:               ".",
		SourcecodeFilesystem: projectSourceFS{root: os.DirFS(project), entryDir: packagePath},
		Stdout:               &stdout, Stderr: &stderr, Args: []string{entry},
	})
	suite.executionError = interpreter.ExecutionError
	if err := interpreter.Use(stdlib.Symbols); err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}
	if err := useProjectEnvironment(interpreter, project, filepath.Dir(entry)); err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}
	if err := interpreter.Use(suite.exports()); err != nil {
		fmt.Fprintln(&stderr, err)
		return runResult{ExitCode: 1}
	}
	importPath := path.Join("qfli-project", packagePath)
	completedBenchmarks := 0
	// Initializer-created closures retain their interpreter frame/run id. Keep
	// compilation, initialization and every test callback in this ONE context;
	// stopping between tests would invalidate Pool.New and channel operations.
	err = interpreter.InvokeWithContext(ctx, func() error {
		if err := interpreter.EvalTest(importPath); err != nil {
			return err
		}
		symbols := interpreter.Symbols(importPath)[importPath]
		if _, found := symbols["TestMain"]; found {
			return fmt.Errorf("TestMain is unsupported by embedded testing; process-level test runners cannot run inside the app")
		}
		names := make([]string, 0, len(symbols))
		for name := range symbols {
			if isTestFunction(name, "Test") || isTestFunction(name, "Benchmark") || isTestFunction(name, "Fuzz") {
				names = append(names, name)
			}
		}
		sort.Strings(names)
		for _, name := range names {
			function := symbols[name]
			if function.Kind() != reflect.Func || function.Type().NumIn() != 1 || function.Type().NumOut() != 0 {
				return fmt.Errorf("%s has an invalid embedded test function signature", name)
			}
			err := func() error {
				switch {
				case isTestFunction(name, "Benchmark"):
					if function.Type().In(0) != reflect.TypeOf((*embeddedB)(nil)) {
						return fmt.Errorf("%s must take *testing.B", name)
					}
					suite.mutex.Lock()
					suite.evidence.BenchmarksRun++
					suite.mutex.Unlock()
					measurement, skipped := suite.benchmark(name, func(b *embeddedB) {
						function.Call([]reflect.Value{reflect.ValueOf(b)})
					})
					if skipped {
						suite.log("--- SKIP: %s\n", name)
						return nil
					}
					if measurement.N <= 0 {
						suite.markFailed()
						return fmt.Errorf("%s did not complete any benchmark iterations", name)
					}
					completedBenchmarks++
					suite.log("%s\t%s\t%s\n", name, measurement.String(), measurement.MemString())
				default:
					fuzz := isTestFunction(name, "Fuzz")
					wanted := reflect.TypeOf((*embeddedT)(nil))
					if fuzz {
						wanted = reflect.TypeOf((*embeddedF)(nil))
					}
					if function.Type().In(0) != wanted {
						return fmt.Errorf("%s has an invalid testing parameter", name)
					}
					suite.mutex.Lock()
					suite.evidence.TestsRun++
					suite.mutex.Unlock()
					test := suite.runCase(name, func(t *embeddedT) {
						if fuzz {
							f := &embeddedF{embeddedT: t}
							function.Call([]reflect.Value{reflect.ValueOf(f)})
							if !f.fuzzed && !f.Skipped() {
								f.Error("fuzz function did not call Fuzz")
							}
						} else {
							function.Call([]reflect.Value{reflect.ValueOf(t)})
						}
					})
					suite.mutex.Lock()
					switch {
					case test.Failed():
						suite.evidence.TestsFailed++
					case test.Skipped():
						suite.evidence.TestsSkipped++
					default:
						suite.evidence.TestsPassed++
					}
					suite.mutex.Unlock()
				}
				return nil
			}()
			if err != nil {
				return err
			}
		}
		return nil
	})
	if err != nil {
		fmt.Fprintln(&stderr, err)
		suite.markFailed()
		return runResult{ExitCode: 1}
	}
	evidence, failed := suite.snapshot()
	if evidence.TestsPassed+evidence.TestsFailed+completedBenchmarks == 0 {
		fmt.Fprintln(&stderr, "embedded testing executed no non-skipped tests or benchmarks")
		return runResult{ExitCode: 1}
	}
	if failed {
		suite.log("FAIL\n")
		return runResult{ExitCode: 1}
	}
	suite.log("PASS\n")
	return runResult{}
}
