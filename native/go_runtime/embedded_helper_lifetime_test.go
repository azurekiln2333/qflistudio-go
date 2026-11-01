package main

import (
	"context"
	"fmt"
	"reflect"
	"runtime"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

// Larger than Go's tiny allocation class, so finalizer reachability reflects
// this token rather than an unrelated live object sharing its allocation.
type helperLifetimeToken struct{ padding [64]byte }

func (token *helperLifetimeToken) Touch() { runtime.KeepAlive(token) }

func TestEmbeddedHelperClosureLifetimeAndNativeRetention(t *testing.T) {
	var created, collected atomic.Int32
	var held func()
	var output outputBuffer
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	suite := &embeddedTestSuite{ctx: ctx, stdout: &output}
	subject := &embeddedT{suite: suite, ctx: ctx, name: "retained"}
	interpreter := interp.New(interp.Options{Stdout: &output, Stderr: &output})
	for _, exports := range []interp.Exports{stdlib.Symbols, suite.exports(), {
		"fixture/fixture": {
			"T": reflect.ValueOf(subject),
			"New": reflect.ValueOf(func() *helperLifetimeToken {
				created.Add(1)
				token := new(helperLifetimeToken)
				runtime.SetFinalizer(token, func(*helperLifetimeToken) { collected.Add(1) })
				return token
			}),
			"Hold": reflect.ValueOf(func(callback func()) { held = callback }),
		},
	}} {
		if err := interpreter.Use(exports); err != nil {
			t.Fatal(err)
		}
	}
	source := `package main
import ("fixture"; "testing")
func discard() {
 for i:=0; i<512; i++ {
  token := fixture.New()
  callback := func(){ token.Touch() }
  callback()
 }
}
func retain(t *testing.T) {
 t.Helper()
 fixture.Hold(func(){ t.Helper(); t.Error("retained evidence") }) // retained callback
}
func main() { discard(); retain(fixture.T) } // registration caller
`
	err := interpreter.InvokeWithContext(ctx, func() error {
		if _, err := interpreter.Eval(source); err != nil {
			return err
		}
		if held == nil {
			return fmt.Errorf("native library did not retain the interpreted callback")
		}
		for pass := 0; pass < 2; pass++ {
			deadline := time.Now().Add(time.Second)
			for collected.Load() < created.Load()-2 && time.Now().Before(deadline) {
				runtime.GC()
				runtime.Gosched()
				time.Sleep(time.Millisecond)
			}
			if collected.Load() < created.Load()-2 {
				return fmt.Errorf("dead closures retain captured native objects: created=%d collected=%d", created.Load(), collected.Load())
			}
			if pass == 0 {
				// Generate another wave after GC so dead lookup buckets are
				// pruned while the native-owned callback must remain usable.
				if _, err := interpreter.Eval("discard()"); err != nil {
					return err
				}
			}
		}
		held()
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	// The original native call returned before held enters. The closure keeps
	// its live source binding, but its lexical registration stack is not an
	// actual caller. Even a marked helper can only fall back to this boundary.
	wanted := fmt.Sprintf("_.go:%d: retained evidence", helperSourceLine(t, source, "// retained callback"))
	invented := fmt.Sprintf("_.go:%d: retained evidence", helperSourceLine(t, source, "// registration caller"))
	if !subject.Failed() || !strings.Contains(output.String(), wanted) || strings.Contains(output.String(), invented) {
		t.Fatalf("native-retained closure lost its source lease after GC: want %q, output %q", wanted, output.String())
	}
	runtime.KeepAlive(interpreter)
	runtime.KeepAlive(held)
}
