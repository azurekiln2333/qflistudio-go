package interp

import (
	"context"
	"reflect"
)

// RunNativeCallback marks a synchronous host adapter which owns its own panic
// and Goexit recovery. Source functions reentered by callback retain that
// recovery boundary; callbacks launched on another native goroutine still join
// their creation epoch's asynchronous panic boundary.
func RunNativeCallback(callback func()) {
	reflectNativeCall(reflect.ValueOf(callback), nil, false)
}

// EvalTestWithContext is EvalTest with the same cancellation and worker-panic
// boundary as EvalPathWithContext. Package initializers execute here; they must
// be cancellable before any test symbol is invoked.
func (interp *Interpreter) EvalTestWithContext(ctx context.Context, path string) error {
	return interp.InvokeWithContext(ctx, func() error { return interp.EvalTest(path) })
}

// InvokeWithContext safely calls already compiled interpreted functions.
// Calls on one Interpreter must be sequential. Shutdown cancels interpreted
// workers and waits for entered native callbacks and blocking IO to return.
func (interp *Interpreter) InvokeWithContext(ctx context.Context, invoke func() error) error {
	_, err := interp.executeWithContext(ctx, func() (reflect.Value, error) {
		return reflect.Value{}, invoke()
	})
	return err
}
