package interp

import (
	"context"
	"reflect"
	"runtime"
	"sync"
)

// executionEpoch owns one uninterrupted evaluation, including source dependency
// initialization, an optional debug entry pause, and all native callbacks. The
// registration gate is closed before Wait, so a callback cannot Add after a
// zero-count Wait or enter interpreted code after this epoch has ended.
type executionEpoch struct {
	interp    *Interpreter
	panics    chan Panic
	mu        sync.Mutex
	closing   bool
	failure   error
	workers   sync.WaitGroup
	stopOnce  sync.Once
	closeOnce sync.Once
	err       error
}

func (interp *Interpreter) newExecution() *executionEpoch {
	execution := &executionEpoch{interp: interp, panics: make(chan Panic, 1)}
	interp.mutex.Lock()
	interp.done = make(chan struct{})
	interp.panics = execution.panics
	interp.activeExecution = execution
	interp.cancelChan = !interp.opt.fastChan
	interp.frame.setrunid(interp.runid())
	interp.frame.mutex.Lock()
	interp.frame.done = reflect.SelectCase{Dir: reflect.SelectRecv, Chan: reflect.ValueOf(interp.done)}
	interp.frame.mutex.Unlock()
	interp.mutex.Unlock()
	return execution
}

func (execution *executionEpoch) enter() bool {
	execution.mu.Lock()
	defer execution.mu.Unlock()
	if execution.closing {
		return false
	}
	execution.workers.Add(1)
	return true
}

func (execution *executionEpoch) stop() {
	execution.mu.Lock()
	execution.closing = true
	execution.mu.Unlock()
	execution.stopOnce.Do(execution.interp.stop)
}

func (execution *executionEpoch) close() error {
	execution.closeOnce.Do(func() {
		execution.stop()
		execution.workers.Wait()
		execution.interp.mutex.Lock()
		if execution.interp.activeExecution == execution {
			execution.interp.activeExecution = nil
		}
		execution.interp.mutex.Unlock()
		execution.mu.Lock()
		execution.err = execution.failure
		execution.mu.Unlock()
	})
	return execution.err
}

func (interp *Interpreter) executeWithContext(ctx context.Context, execute func() (reflect.Value, error)) (value reflect.Value, err error) {
	if err = ctx.Err(); err != nil {
		return reflect.Value{}, err
	}
	execution := interp.newExecution()
	defer func() {
		if failure := execution.close(); err == nil {
			err = failure
		}
	}()
	return execution.evaluate(ctx, execute)
}

func (execution *executionEpoch) evaluate(ctx context.Context, execute func() (reflect.Value, error)) (reflect.Value, error) {
	type result struct {
		value reflect.Value
		err   error
	}
	finished := make(chan result, 1)
	go func() {
		var response result
		defer func() {
			if failure := recover(); failure != nil {
				response.err = recoveredPanic(failure)
			}
			finished <- response
		}()
		response.value, response.err = execute()
	}()
	select {
	case <-ctx.Done():
		execution.recordFailure(ctx.Err())
		execution.stop()
		<-finished
		return reflect.Value{}, ctx.Err()
	case failure := <-execution.panics:
		execution.stop()
		<-finished
		return reflect.Value{}, failure
	case response := <-finished:
		return response.value, response.err
	}
}

// ExecutionError reports a failure of the currently owned evaluation. Native
// adapters use it before reporting an interrupted source callback as passed.
// It carries no source attribution or shared current-call metadata.
func (interp *Interpreter) ExecutionError() error {
	execution := interp.callbackExecution()
	if execution == nil {
		return nil
	}
	execution.mu.Lock()
	defer execution.mu.Unlock()
	return execution.failure
}

func (execution *executionEpoch) recordFailure(failure error) {
	execution.mu.Lock()
	if execution.failure == nil {
		execution.failure = failure
	}
	execution.mu.Unlock()
}

func (execution *executionEpoch) reportPanic(failure Panic) {
	execution.recordFailure(failure)
	select {
	case execution.panics <- failure:
	default:
	}
}

// nativeCallbackContext accepts provenance only after the dispatch's exact
// synchronous/non-retaining native contract has been checked. The generic native
// stack marker classifies panic propagation; it cannot establish a retained
// argument's caller identity. Unknown APIs pass nil and get an opaque owner.
func nativeCallbackContext(caller *callContext) *callContext {
	if caller == nil {
		return nil
	}
	callback := *caller
	callback.external = !onNativeDispatchStack()
	return &callback
}

func onNativeDispatchStack() bool {
	marker := reflect.ValueOf(reflectNativeCall).Pointer()
	for size := 64; ; size *= 2 {
		pcs := make([]uintptr, size)
		n := runtime.Callers(2, pcs)
		for _, pc := range pcs[:n] {
			if fn := runtime.FuncForPC(pc - 1); fn != nil && fn.Entry() == marker {
				return true
			}
		}
		if n < len(pcs) {
			return false
		}
	}
}

func (interp *Interpreter) callbackExecution() *executionEpoch {
	interp.mutex.RLock()
	defer interp.mutex.RUnlock()
	return interp.activeExecution
}

// prepareDebugCallback keeps execution ownership separate from panic recovery.
// An opaque native entry has no argument-bound caller (for example sync.Pool.New),
// so it owns a fresh logical callback routine even on a synchronous native stack.
// Its lexical ancestry still supplies captured values, never a displayed caller.
func (interp *Interpreter) prepareDebugCallback(local *frame, function *node, caller *callContext) (bool, func()) {
	var external bool
	if caller != nil {
		external = caller.external || caller.node != nil && caller.node.anc != nil && caller.node.anc.kind == goStmt
	} else {
		external = !onNativeDispatchStack()
		// Prevent runCfg from rebuilding a source stack from the lexical capture.
		local.source = &sourceCallFrame{function: function}
	}
	dbg := interp.debugger
	if dbg == nil {
		return external, func() {}
	}
	g := dbg.main
	if caller != nil {
		for current := caller.frame; current != nil; current = current.anc {
			if current.debug != nil && current.debug.g != nil {
				g = current.debug.g
				break
			}
		}
	}
	ownsRoutine := caller == nil || external
	if caller == nil {
		g = dbg.enterRoutine("nativeCallback")
	} else if ownsRoutine {
		g = dbg.enterGoRoutine()
	}
	local.debug = &frameDebugData{g: g, kind: frameCall, scope: function.scope, nativeBoundary: caller == nil}
	if caller != nil && !external {
		// .anc belongs to closure storage. Use only proven synchronous call
		// provenance when displaying a caller, including nested native reentry.
		local.debug.caller = caller.frame
	}
	if function.kind == funcDecl {
		local.debug.name = function.child[1].ident
	}
	if !ownsRoutine {
		return external, func() {}
	}
	dbg.events(&DebugEvent{dbg, DebugEnterGoRoutine, local})
	return external, func() {
		dbg.exitGoRoutine(g)
		dbg.events(&DebugEvent{dbg, DebugExitGoRoutine, local})
	}
}

func (execution *executionEpoch) recoverCallback() {
	if failure := recover(); failure != nil {
		execution.reportPanic(recoveredPanic(failure))
	}
}
