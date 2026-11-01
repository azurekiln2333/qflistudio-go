package interp

import "reflect"

// nativeValueMayAlias examines interface contents and aggregate types, never a
// pointer target, map entry, channel element or aggregate field value. Function
// wrappers are separate: their interpreted entry is guarded and their results
// pass through observeNativeValues before returning to compiled callers.
func nativeValueMayAlias(value reflect.Value) bool {
	for value.IsValid() {
		if value.Type() == valueInterfaceType {
			value = value.Interface().(valueInterface).value
			continue
		}
		if value.Kind() != reflect.Interface {
			break
		}
		if value.IsNil() {
			return false
		}
		value = value.Elem()
	}
	if !value.IsValid() {
		return false
	}
	return nativeTypeMayAlias(value.Type())
}

func nativeTypeMayAlias(typ reflect.Type) bool {
	switch typ.Kind() {
	case reflect.Ptr, reflect.Map, reflect.Slice, reflect.Chan, reflect.UnsafePointer, reflect.Interface:
		return true
	case reflect.Array:
		return nativeTypeMayAlias(typ.Elem())
	case reflect.Struct:
		for index := 0; index < typ.NumField(); index++ {
			if nativeTypeMayAlias(typ.Field(index).Type) {
				return true
			}
		}
	}
	return false
}

// observeNativeValues latches possible autonomous native writes for this debug
// session. A returned native call or callback does not establish that a library
// released a mutable alias. Type inspection deliberately over-approximates this
// condition rather than following an unsafe heap graph or executing user code.
func (interp *Interpreter) observeNativeValues(values []reflect.Value) {
	if dbg := interp.debugger; dbg != nil {
		for _, value := range values {
			if nativeValueMayAlias(value) {
				dbg.gLock.Lock()
				dbg.nativeValuesEscaped = true
				dbg.gLock.Unlock()
				return
			}
		}
	}
}

func (interp *Interpreter) observeNativeArguments(function reflect.Value, values []reflect.Value) {
	if interp.debugger == nil {
		return
	}
	for index, value := range values {
		// The exact sort implementations use the slice only for this call.
		// A bare go call is additionally covered by the owned-worker count.
		// Callback functions have their own guarded entry/result boundary.
		if index == 0 && synchronousNativeCallback(function, 1) {
			continue
		}
		interp.observeNativeValues([]reflect.Value{value})
	}
}
