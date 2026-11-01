package interp

import (
	"fmt"
	"io"
	"reflect"
	"strconv"
	"strings"
	"unicode/utf8"
)

// fmt handles %T before calling Formatter. Rewrite that verb to a private
// Formatter verb, retaining fmt's own indexing/width/precision argument parser.
// No other verb or ordinary text is rewritten.
const sourceTypeVerb = '\ue000'
const sourcePointerVerb = '\ue001'

// Keep fmt's star operands as ordinary integers. Each star gets a plain copy
// at an explicit index; each value keeps its original index and Formatter.
// This also supports using the same operand for width and %T, without making
// width parsing see an interpreter wrapper instead of an integer.
func sourceCallFormat(format string, values []interface{}) (string, []interface{}, bool) {
	var out strings.Builder
	argument := 0
	originalCount := len(values)
	reordered := false
	index := func(position *int) (bool, bool) {
		if *position >= len(format) || format[*position] != '[' {
			return false, true
		}
		end := strings.IndexByte(format[*position:], ']')
		if end < 0 {
			return false, false
		}
		end += *position
		number, err := strconv.Atoi(format[*position+1 : end])
		if err != nil || number < 1 || number > originalCount {
			return false, false
		}
		reordered = true
		argument = number - 1
		*position = end + 1
		return true, true
	}
	star := func() (string, bool) {
		if argument >= originalCount {
			return "", false
		}
		plain := values[argument]
		if wrapped, ok := plain.(sourceFormatValue); ok {
			plain = wrapped.value
		}
		values = append(values, plain)
		argument++
		return "[" + strconv.Itoa(len(values)) + "]*", true
	}
	for position := 0; position < len(format); {
		if format[position] != '%' {
			out.WriteByte(format[position])
			position++
			continue
		}
		position++
		flagsStart := position
		for position < len(format) && strings.ContainsRune("+#- 0", rune(format[position])) {
			position++
		}
		flags := format[flagsStart:position]
		afterIndex, valid := index(&position)
		if !valid {
			return "", nil, false
		}
		width := ""
		if position < len(format) && format[position] == '*' {
			position++
			width, valid = star()
			if !valid {
				return "", nil, false
			}
			afterIndex = false
		} else {
			start := position
			for position < len(format) && format[position] >= '0' && format[position] <= '9' {
				position++
			}
			width = format[start:position]
			if afterIndex && width != "" {
				return "", nil, false
			}
		}
		precision := ""
		if position < len(format) && format[position] == '.' {
			if afterIndex {
				return "", nil, false
			}
			position++
			afterIndex, valid = index(&position)
			if !valid {
				return "", nil, false
			}
			if position < len(format) && format[position] == '*' {
				position++
				precision, valid = star()
				if !valid {
					return "", nil, false
				}
				afterIndex = false
			} else {
				start := position
				for position < len(format) && format[position] >= '0' && format[position] <= '9' {
					position++
				}
				precision = format[start:position]
			}
			precision = "." + precision
		}
		if !afterIndex {
			_, valid = index(&position)
		}
		if !valid || position >= len(format) {
			return "", nil, false
		}
		verb, size := utf8.DecodeRuneInString(format[position:])
		position += size
		if !strings.ContainsRune("vTtbcdoOqxXUeEfFgGsp%", verb) {
			return "", nil, false
		}
		out.WriteByte('%')
		out.WriteString(flags + width + precision)
		if verb != '%' {
			if argument >= originalCount {
				return "", nil, false
			}
			out.WriteString("[" + strconv.Itoa(argument+1) + "]")
			argument++
		}
		if verb == 'T' {
			verb = sourceTypeVerb
		}
		if verb == 'p' {
			verb = sourcePointerVerb
		}
		out.WriteRune(verb)
	}
	if !reordered && argument < originalCount {
		return "", nil, false
	}
	return out.String(), values, true
}

type sourceFormatValue struct {
	value     interface{}
	formatted interface{}
	typeName  string
}

func formatState(state fmt.State, verb rune) string {
	var format strings.Builder
	format.WriteByte('%')
	for _, flag := range "+-# 0" {
		if state.Flag(int(flag)) {
			format.WriteRune(flag)
		}
	}
	if width, ok := state.Width(); ok {
		format.WriteString(strconv.Itoa(width))
	}
	if precision, ok := state.Precision(); ok {
		format.WriteByte('.')
		format.WriteString(strconv.Itoa(precision))
	}
	format.WriteRune(verb)
	return format.String()
}

func (value sourceFormatValue) Format(state fmt.State, verb rune) {
	if verb == sourceTypeVerb {
		fmt.Fprintf(state, formatState(state, 's'), value.typeName)
		return
	}
	if verb == sourcePointerVerb {
		verb = 'p'
	}
	argument := value.value
	if _, custom := value.formatted.(fmt.Formatter); custom ||
		verb == 'v' && !state.Flag('#') || strings.ContainsRune("sqxX", verb) {
		argument = value.formatted
	}
	// A Stringer wrapper is an implementation detail, not a replacement for
	// the original numeric value. Numeric verbs bypass String() in Go's fmt.
	fmt.Fprintf(state, formatState(state, verb), argument)
}

func sourceFormatArgument(value reflect.Value, typ *itype) interface{} {
	for value.IsValid() && value.Kind() == reflect.Interface {
		value = value.Elem()
	}
	if !value.IsValid() {
		return sourceFormatValue{typeName: "<nil>"}
	}
	formatted := value.Interface()
	if wrapped, ok := formatted.(valueInterface); ok {
		if wrapped.node != nil {
			typ = wrapped.node.typ
		}
		value = wrapped.value
		formatted = value.Interface()
	}
	if source, ok := formatted.(*interpretedErrorValue); ok {
		typ = source.value.node.typ
		value = source.value.value
	} else if value.Kind() == reflect.Struct && value.NumField() > 0 && value.Type().Field(0).Name == "IValue" {
		value = value.Field(0)
		for value.Kind() == reflect.Interface && !value.IsNil() {
			value = value.Elem()
		}
	}
	return sourceFormatValue{value.Interface(), formatted, sourceTypeName(typ, value.Type())}
}

func sourceTypeName(typ *itype, runtimeType reflect.Type) string {
	if typ != nil && typ.cat != valueT && typ.cat != errorT && typ.cat != interfaceT {
		if typ.name != "" {
			if typ.path != "" {
				return typ.path + "." + typ.name
			}
			return typ.name
		}
		if typ.cat == ptrT {
			return "*" + sourceTypeName(typ.val, runtimeType.Elem())
		}
	}
	return runtimeType.String()
}

func callInterpretedFormat(interp *Interpreter, function reflect.Value, in []reflect.Value, args []*node, slice bool) ([]reflect.Value, bool) {
	if function.Kind() != reflect.Func {
		return nil, false
	}
	formatIndex, name := 0, ""
	for _, candidate := range []string{"Printf", "Sprintf", "Fprintf"} {
		if symbol := interp.binPkg["fmt"][candidate]; symbol.IsValid() && symbol.Pointer() == function.Pointer() {
			name = candidate
			break
		}
	}
	if name == "" {
		return nil, false
	}
	if name == "Fprintf" {
		formatIndex = 1
	}
	format := in[formatIndex].String()
	values := []interface{}{}
	for i := formatIndex + 1; i < len(in); i++ {
		var typ *itype
		if i < len(args) {
			typ = args[i].typ
		}
		if slice && i == len(in)-1 {
			for j := 0; j < in[i].Len(); j++ {
				values = append(values, sourceFormatArgument(in[i].Index(j), nil))
			}
		} else {
			values = append(values, sourceFormatArgument(in[i], typ))
		}
	}
	format, values, valid := sourceCallFormat(format, values)
	if !valid {
		return nil, false
	}
	if name == "Sprintf" {
		return []reflect.Value{reflect.ValueOf(fmt.Sprintf(format, values...))}, true
	}
	writer := interp.stdout
	if name == "Fprintf" {
		writer = in[0].Interface().(io.Writer)
	}
	written, err := fmt.Fprintf(writer, format, values...)
	status := reflect.Zero(reflect.TypeOf((*error)(nil)).Elem())
	if err != nil {
		status = reflect.ValueOf(err)
	}
	return []reflect.Value{reflect.ValueOf(written), status}, true
}
