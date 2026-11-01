package interp

// Interpreted named types have anonymous reflect storage types. Preserve their
// source identity at the error boundary rather than asking reflect whether an
// anonymous struct has source-declared Error/Unwrap methods.
import (
	"errors"
	"reflect"
)

type interpretedErrorValue struct {
	value valueInterface
	frame *frame
}

func (e *interpretedErrorValue) method(name string, in ...reflect.Value) []reflect.Value {
	// Optional stdlib hooks count only when their complete signature matches.
	// An unrelated method with the same name must never be invoked by errors.
	signature := e.value.node.typ.methods()[name]
	switch name {
	case "Unwrap":
		if signature != "func() error" && signature != "func() []error" {
			return nil
		}
	case "Is":
		if signature != "func(error) bool" {
			return nil
		}
	case "As":
		if signature != "func(interface{}) bool" && signature != "func(interface {}) bool" && signature != "func(any) bool" {
			return nil
		}
	}
	method, indexes := e.value.node.typ.lookupMethod(name)
	if method == nil {
		return nil
	}
	node := *method
	node.recv = &receiver{val: e.value.value, index: indexes}
	return genFunctionWrapper(&node)(e.frame).Call(in)
}

func (e *interpretedErrorValue) Error() string { return e.method("Error")[0].String() }

func errorChildren(err error) []error {
	if source, ok := err.(*interpretedErrorValue); ok {
		out := source.method("Unwrap")
		if len(out) == 0 {
			return nil
		}
		if single, ok := out[0].Interface().(error); ok {
			return []error{single}
		}
		if multiple, ok := out[0].Interface().([]error); ok {
			return multiple
		}
		return nil
	}
	switch err := err.(type) {
	case interface{ Unwrap() error }:
		return []error{err.Unwrap()}
	case interface{ Unwrap() []error }:
		return err.Unwrap()
	}
	return nil
}

func interpretedErrorsIs(err, target error) bool {
	if err == nil || target == nil {
		return err == target
	}
	targetValue, _ := sourceDynamicValue(reflect.ValueOf(target), nil)
	if targetValue.Type().Comparable() && sourceValuesEqual(reflect.ValueOf(err), reflect.ValueOf(target), nil, nil) {
		return true
	}
	if source, ok := err.(*interpretedErrorValue); ok {
		if out := source.method("Is", reflect.ValueOf(target)); len(out) != 0 && out[0].Bool() {
			return true
		}
	} else if matcher, ok := err.(interface{ Is(error) bool }); ok && matcher.Is(target) {
		return true
	}
	for _, child := range errorChildren(err) {
		if child != nil && interpretedErrorsIs(child, target) {
			return true
		}
	}
	return false
}

func interpretedErrorsAs(err error, target reflect.Value, sourceType *itype) bool {
	if err == nil {
		return false
	}
	if sourceType == nil || sourceType.cat != ptrT {
		return errors.As(err, target.Interface())
	}
	want := sourceType.val
	if !target.IsValid() || target.Kind() != reflect.Ptr || target.IsNil() {
		panic("errors: target must be a non-nil pointer")
	}
	nativeTarget := target.Elem().Type()
	if nativeTarget.Kind() != reflect.Interface && !nativeTarget.Implements(reflect.TypeOf((*error)(nil)).Elem()) && !isInterface(want) && want.methods()["Error"] != "func() string" {
		panic("errors: *target must be interface or implement error")
	}
	var visit func(error) bool
	visit = func(err error) bool {
		if err == nil {
			return false
		}
		if source, ok := err.(*interpretedErrorValue); ok {
			if nativeTarget.Kind() == reflect.Interface && reflect.TypeOf(source).Implements(nativeTarget) {
				target.Elem().Set(reflect.ValueOf(source))
				return true
			}
			if source.value.node.typ.id() == want.id() {
				target.Elem().Set(source.value.value)
				return true
			}
			if isInterfaceSrc(want) && source.value.node.typ.methods().contains(want.methods()) {
				target.Elem().Set(reflect.ValueOf(source.value))
				return true
			}
			if out := source.method("As", target); len(out) != 0 && out[0].Bool() {
				return true
			}
		} else {
			value := reflect.ValueOf(err)
			if value.Type().AssignableTo(target.Elem().Type()) {
				target.Elem().Set(value)
				return true
			}
			if isInterfaceSrc(want) && nativeImplementsSource(value.Type(), want) {
				node := &node{typ: valueTOf(value.Type()), rval: value}
				target.Elem().Set(reflect.ValueOf(valueInterface{node, value}))
				return true
			}
			if matcher, ok := err.(interface{ As(interface{}) bool }); ok && matcher.As(target.Interface()) {
				return true
			}
		}
		for _, child := range errorChildren(err) {
			if visit(child) {
				return true
			}
		}
		return false
	}
	return visit(err)
}

func callInterpretedErrors(function reflect.Value, in []reflect.Value, args []*node) ([]reflect.Value, bool) {
	if function.Kind() != reflect.Func {
		return nil, false
	}
	asError := func(value reflect.Value) error {
		if !value.IsValid() {
			return nil
		}
		if err, ok := value.Interface().(error); ok {
			return err
		}
		return nil
	}
	switch function.Pointer() {
	case reflect.ValueOf(errors.Is).Pointer():
		return []reflect.Value{reflect.ValueOf(interpretedErrorsIs(asError(in[0]), asError(in[1])))}, true
	case reflect.ValueOf(errors.As).Pointer():
		var typ *itype
		if len(args) == 2 {
			typ = args[1].typ
		}
		return []reflect.Value{reflect.ValueOf(interpretedErrorsAs(asError(in[0]), in[1], typ))}, true
	case reflect.ValueOf(errors.Unwrap).Pointer():
		err := asError(in[0])
		if source, ok := err.(*interpretedErrorValue); ok {
			out := source.method("Unwrap")
			if len(out) != 0 && out[0].Type() == reflect.TypeOf((*error)(nil)).Elem() {
				return out, true
			}
			return []reflect.Value{reflect.Zero(reflect.TypeOf((*error)(nil)).Elem())}, true
		}
	}
	return nil, false
}
