package interp

import "reflect"

// Interface adapters hold execution metadata, which must not participate in Go
// equality. Compare the original dynamic source type and value instead. The
// ordinary interface comparison deliberately retains Go's uncomparable panic.
func sourceDynamicValue(value reflect.Value, typ *itype) (reflect.Value, *itype) {
	for value.IsValid() {
		if value.Kind() == reflect.Interface {
			value, typ = value.Elem(), nil
			continue
		}
		switch wrapped := value.Interface().(type) {
		case valueInterface:
			value = wrapped.value
			if wrapped.node != nil {
				typ = wrapped.node.typ
			}
		case *interpretedErrorValue:
			value, typ = wrapped.value.value, wrapped.value.node.typ
		default:
			if typ == nil {
				typ = valueTOf(value.Type())
			}
			return value, typ
		}
	}
	return value, nil
}

func sourceValuesEqual(left, right reflect.Value, leftType, rightType *itype) bool {
	left, leftType = sourceDynamicValue(left, leftType)
	right, rightType = sourceDynamicValue(right, rightType)
	if !left.IsValid() || !right.IsValid() {
		return left.IsValid() == right.IsValid()
	}
	if leftType.id() != rightType.id() {
		return false
	}
	return left.Interface() == right.Interface()
}

func sourceEqual(n *node) {
	if !sourceInterfaceEquality(n, false) {
		equal(n)
	}
}

func sourceNotEqual(n *node) {
	if !sourceInterfaceEquality(n, true) {
		notEqual(n)
	}
}

func sourceInterfaceEquality(n *node, invert bool) bool {
	c0, c1 := n.child[0], n.child[1]
	if c0.typ.TypeOf().Kind() != reflect.Interface && c1.typ.TypeOf().Kind() != reflect.Interface {
		return false
	}
	v0, v1 := genValue(c0), genValue(c1)
	dest := genValueOutput(n, reflect.TypeOf(true))
	next := getExec(n.tnext)
	failure := next
	if n.fnext != nil {
		failure = getExec(n.fnext)
	}
	n.exec = func(f *frame) bltn {
		result := sourceValuesEqual(v0(f), v1(f), c0.typ, c1.typ) != invert
		dest(f).SetBool(result)
		if result {
			return next
		}
		return failure
	}
	return true
}
