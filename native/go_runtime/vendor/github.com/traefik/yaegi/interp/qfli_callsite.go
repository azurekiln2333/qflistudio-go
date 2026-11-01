package interp

import (
	"hash/maphash"
	"reflect"
	"runtime"
	"sort"
	"sync"
	"weak"
)

// SourceFrame identifies an interpreted function and a call made by it. FunctionID
// is stable within one Interpreter, including anonymous functions with equal names.
type SourceFrame struct {
	FunctionID int64
	Filename   string
	Line       int
	Column     int
}

// SourceMethodReceiver is the narrow native boundary for source-aware methods.
// Arguments have reflect.MakeFunc form (a variadic final argument is a slice).
// The supplied stack is a fresh snapshot, innermost caller first.
type SourceMethodReceiver interface {
	SourceMethodEnabled(string) bool
	CallWithSource(string, []SourceFrame, []reflect.Value) ([]reflect.Value, bool)
}

type sourceCallFrame struct {
	function *node
	position *node
	parent   *sourceCallFrame
}

type callContext struct {
	frame    *frame
	node     *node
	source   *sourceCallFrame
	external bool
}

type sourceFunction func([]reflect.Value, *callContext) []reflect.Value

// The returned wrapper owns its binding lease. The registry holds only a hash
// and a weak pointer, so recording provenance never keeps an otherwise dead
// closure, its captured frame or a native receiver alive for the whole epoch.
type sourceFunctionBinding struct {
	function reflect.Value
	original reflect.Value
	invoke   sourceFunction
}

type sourceFunctionRegistry struct {
	mutex         sync.RWMutex
	seed          maphash.Seed
	bindings      map[uint64][]weak.Pointer[sourceFunctionBinding]
	registrations uint64
}

func (registry *sourceFunctionRegistry) prune() {
	for hash, bucket := range registry.bindings {
		live := bucket[:0]
		for _, entry := range bucket {
			if entry.Value() != nil {
				live = append(live, entry)
			}
		}
		if len(live) == 0 {
			delete(registry.bindings, hash)
		} else {
			registry.bindings[hash] = live
		}
	}
}

func newCallContext(f *frame, n *node) *callContext {
	context := &callContext{frame: f, node: n}
	if f != nil && f.source != nil {
		context.source = &sourceCallFrame{function: f.source.function, position: n, parent: f.source.parent}
	}
	return context
}

func setSourceCaller(f *frame, function *node, caller *callContext) {
	if caller != nil {
		f.source = &sourceCallFrame{function: function, parent: caller.source}
	}
}

func (context *callContext) frames() []SourceFrame {
	var frames []SourceFrame
	if context == nil {
		return frames
	}
	for call := context.source; call != nil; call = call.parent {
		if call.function == nil || call.position == nil {
			continue
		}
		position := call.position.interp.fset.Position(call.position.pos)
		frames = append(frames, SourceFrame{call.function.index, position.Filename, position.Line, position.Column})
	}
	return frames
}

// Normalize function Values before registration and lookup. In particular,
// reflect's bound-method Value must be materialized once, before it is stored in
// an interpreted variable. Copies then retain the same closure identity rather
// than the shared code pointer returned by Value.Pointer.
func (interp *Interpreter) registerSourceFunction(function reflect.Value, invoke sourceFunction) reflect.Value {
	binding := &sourceFunctionBinding{original: reflect.ValueOf(function.Interface()), invoke: invoke}
	wrapped := reflect.MakeFunc(function.Type(), func(in []reflect.Value) []reflect.Value {
		// Preserve the original wrapper's native-bound caller when a compiled
		// library invokes it. This forwarding call is not a native dispatch
		// marker: an asynchronous callback still owns a separate debug routine.
		var out []reflect.Value
		if binding.original.Type().IsVariadic() {
			out = binding.original.CallSlice(in)
		} else {
			out = binding.original.Call(in)
		}
		// Mark mutable result aliases before compiled code can retain or write
		// them, including results from an asynchronously retained callback.
		interp.observeNativeValues(out)
		return out
	})
	binding.function = reflect.ValueOf(wrapped.Interface())
	registry := &interp.sourceFunctions
	registry.mutex.Lock()
	if registry.bindings == nil {
		registry.seed = maphash.MakeSeed()
		registry.bindings = make(map[uint64][]weak.Pointer[sourceFunctionBinding])
	}
	registry.registrations++
	if registry.registrations%256 == 0 {
		registry.prune()
	}
	hash := maphash.Comparable(registry.seed, binding.function)
	registry.bindings[hash] = append(registry.bindings[hash], weak.Make(binding))
	registry.mutex.Unlock()
	return binding.function
}

func (interp *Interpreter) sourceFunction(function reflect.Value) sourceFunction {
	if function.Kind() != reflect.Func || function.IsNil() {
		return nil
	}
	function = reflect.ValueOf(function.Interface())
	registry := &interp.sourceFunctions
	registry.mutex.RLock()
	var invoke sourceFunction
	if registry.bindings != nil {
		for _, entry := range registry.bindings[maphash.Comparable(registry.seed, function)] {
			if binding := entry.Value(); binding != nil && binding.function == function {
				invoke = binding.invoke
				break
			}
		}
	}
	registry.mutex.RUnlock()
	// The lookup's argument owns the lease until weak.Value has promoted it.
	runtime.KeepAlive(function)
	return invoke
}

func (interp *Interpreter) sourceMethod(receiver, method reflect.Value, name string) reflect.Value {
	if !receiver.IsValid() || !receiver.CanInterface() {
		return method
	}
	receiver = valueInterfaceValue(receiver)
	// A bound native method may retain its receiver independently of explicit
	// arguments. Mark the receiver without following its mutable storage.
	interp.observeNativeValues([]reflect.Value{receiver})
	aware, ok := receiver.Interface().(SourceMethodReceiver)
	if !ok || !aware.SourceMethodEnabled(name) {
		return method
	}
	method = reflect.ValueOf(method.Interface())
	return interp.registerSourceFunction(method, func(in []reflect.Value, caller *callContext) []reflect.Value {
		interp.observeNativeArguments(method, in)
		if out, handled := aware.CallWithSource(name, caller.frames(), in); handled {
			return out
		}
		return interp.callNativeWithSource(method, in, caller, method.Type().IsVariadic())
	})
}

// nativeMethodExpression keeps the explicit receiver argument of T.Method while
// binding source-aware native receivers at invocation time. Interface method
// expressions have no Method.Func and must dispatch to the concrete receiver.
func (interp *Interpreter) nativeMethodExpression(receiver reflect.Type, method reflect.Method, index []int, pointer bool) reflect.Value {
	typ := nativeSelectorType(receiver, method, true)
	index = append([]int(nil), index...)
	invoke := func(in []reflect.Value, caller *callContext) []reflect.Value {
		value := valueInterfaceValue(in[0])
		for _, field := range index {
			if value.Kind() == reflect.Ptr {
				value = value.Elem()
			}
			value = valueInterfaceValue(value.Field(field))
		}
		if pointer && value.Kind() != reflect.Ptr {
			value = value.Addr()
		}
		bound := interp.sourceMethod(value, value.MethodByName(method.Name), method.Name)
		return interp.callWithSource(bound, in[1:], caller, typ.IsVariadic())
	}
	wrapped := reflect.MakeFunc(typ, func(in []reflect.Value) []reflect.Value { return invoke(in, nil) })
	return interp.registerSourceFunction(wrapped, invoke)
}

func packedSourceArguments(function reflect.Value, in []reflect.Value, slice bool) []reflect.Value {
	typ := function.Type()
	if slice || !typ.IsVariadic() {
		return in
	}
	last := typ.NumIn() - 1
	packed := make([]reflect.Value, last+1)
	copy(packed, in[:last])
	variadic := reflect.MakeSlice(typ.In(last), len(in)-last, len(in)-last)
	for index, value := range in[last:] {
		variadic.Index(index).Set(value)
	}
	packed[last] = variadic
	return packed
}

func (interp *Interpreter) callWithSource(function reflect.Value, in []reflect.Value, caller *callContext, slice bool) []reflect.Value {
	if invoke := interp.sourceFunction(function); invoke != nil {
		return invoke(packedSourceArguments(function, in, slice), caller)
	}
	// A method expression supplies its native receiver explicitly rather than
	// creating a bound method value. Match the actual reflected method, never
	// an unrelated package function which happens to have the same name.
	if len(in) > 0 && in[0].CanInterface() {
		receiver := valueInterfaceValue(in[0])
		if aware, ok := receiver.Interface().(SourceMethodReceiver); ok {
			for index := 0; index < receiver.NumMethod(); index++ {
				method := receiver.Type().Method(index)
				if method.Func.Type() == function.Type() && method.Func.Pointer() == function.Pointer() {
					args := packedSourceArguments(function, in, slice)
					interp.observeNativeArguments(function, args)
					if out, handled := aware.CallWithSource(method.Name, caller.frames(), args[1:]); handled {
						return out
					}
					break
				}
			}
		}
	}
	return interp.callNativeWithSource(function, in, caller, slice)
}

func (interp *Interpreter) callNativeWithSource(function reflect.Value, in []reflect.Value, caller *callContext, slice bool) []reflect.Value {
	interp.observeNativeArguments(function, in)
	// Bind provenance to this invocation's callback values. A callback may enter
	// on another native goroutine long after the native function has returned.
	// No mutable current-call slot is shared between simultaneous invocations.
	args := append([]reflect.Value(nil), in...)
	for index, value := range args {
		if invoke := interp.sourceFunction(value); invoke != nil {
			// Only a native API with an explicit synchronous/non-retaining
			// contract can prove that this argument's caller is still the
			// caller when the callback enters. A retained argument can be
			// invoked by a different dispatch even while this call is active.
			callbackCaller := caller
			synchronousSource := caller != nil && caller.frame != nil && !caller.external
			if caller != nil && caller.node != nil && caller.node.anc != nil && caller.node.anc.kind == goStmt {
				synchronousSource = false
			}
			if !synchronousSource || !synchronousNativeCallback(function, index) {
				callbackCaller = nil
			}
			callback := reflect.MakeFunc(value.Type(), func(arguments []reflect.Value) []reflect.Value {
				return invoke(arguments, nativeCallbackContext(callbackCaller))
			})
			args[index] = interp.registerSourceFunction(callback, invoke)
		}
	}
	return reflectNativeCall(function, args, slice)
}

// synchronousNativeCallback recognizes only exact native functions and callback
// argument positions whose contracts do not retain or concurrently dispatch the
// argument. A generic native stack marker, or this call merely remaining active,
// cannot prove which interpreted execution called a retained callback. Unknown
// APIs therefore receive opaque callback owners, including synchronous entries.
func synchronousNativeCallback(function reflect.Value, argument int) bool {
	if argument != 1 {
		return false
	}
	for _, known := range []reflect.Value{
		reflect.ValueOf(sort.Slice),
		reflect.ValueOf(sort.SliceStable),
		reflect.ValueOf(sort.Search),
	} {
		if function.Type() == known.Type() && function.Pointer() == known.Pointer() {
			return true
		}
	}
	return false
}

//go:noinline
func reflectNativeCall(function reflect.Value, in []reflect.Value, slice bool) []reflect.Value {
	if slice {
		return function.CallSlice(in)
	}
	return function.Call(in)
}

func (interp *Interpreter) deferredSourceCall(function reflect.Value, in []reflect.Value, caller *callContext, slice bool) []reflect.Value {
	function = reflect.ValueOf(function.Interface())
	arguments := make([]reflect.Value, len(in))
	for index, value := range in {
		arguments[index] = reflect.New(value.Type()).Elem()
		arguments[index].Set(value)
	}
	return []reflect.Value{reflect.ValueOf(func() { interp.callWithSource(function, arguments, caller, slice) })}
}
