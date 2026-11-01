package main

import (
	"fmt"
	"strconv"
	"unicode"
)

func precedence(op rune) int {
	if op == '+' || op == '-' {
		return 1
	}
	if op == '*' || op == '/' {
		return 2
	}
	return 0
}
func evaluate(text string) (int, error) {
	values := []int{}
	ops := []rune{}
	apply := func() error {
		if len(values) < 2 || len(ops) == 0 {
			return fmt.Errorf("missing operand")
		}
		op := ops[len(ops)-1]
		ops = ops[:len(ops)-1]
		a, b := values[len(values)-2], values[len(values)-1]
		values = values[:len(values)-2]
		switch op {
		case '+':
			values = append(values, a+b)
		case '-':
			values = append(values, a-b)
		case '*':
			values = append(values, a*b)
		case '/':
			if b == 0 {
				return fmt.Errorf("division by zero")
			}
			values = append(values, a/b)
		default:
			return fmt.Errorf("bad operator")
		}
		return nil
	}
	chars := []rune(text)
	expectValue := true
	for i := 0; i < len(chars); {
		c := chars[i]
		if unicode.IsSpace(c) {
			i++
			continue
		}
		if c >= '0' && c <= '9' {
			if !expectValue {
				return 0, fmt.Errorf("missing operator")
			}
			start := i
			for i < len(chars) && chars[i] >= '0' && chars[i] <= '9' {
				i++
			}
			n, err := strconv.Atoi(string(chars[start:i]))
			if err != nil {
				return 0, err
			}
			values = append(values, n)
			expectValue = false
			continue
		}
		if c == '(' {
			if !expectValue {
				return 0, fmt.Errorf("missing operator")
			}
			ops = append(ops, c)
			i++
			continue
		}
		if c == ')' {
			if expectValue {
				return 0, fmt.Errorf("empty group")
			}
			for len(ops) > 0 && ops[len(ops)-1] != '(' {
				if err := apply(); err != nil {
					return 0, err
				}
			}
			if len(ops) == 0 {
				return 0, fmt.Errorf("unmatched close")
			}
			ops = ops[:len(ops)-1]
			i++
			continue
		}
		if precedence(c) == 0 || expectValue {
			return 0, fmt.Errorf("bad token")
		}
		for len(ops) > 0 && precedence(ops[len(ops)-1]) >= precedence(c) {
			if err := apply(); err != nil {
				return 0, err
			}
		}
		ops = append(ops, c)
		expectValue = true
		i++
	}
	if expectValue {
		return 0, fmt.Errorf("incomplete")
	}
	for len(ops) > 0 {
		if ops[len(ops)-1] == '(' {
			return 0, fmt.Errorf("unmatched open")
		}
		if err := apply(); err != nil {
			return 0, err
		}
	}
	if len(values) != 1 {
		return 0, fmt.Errorf("bad expression")
	}
	return values[0], nil
}
func main() {
	for _, expression := range []string{"2 + 3 * (4 - 1)", "18 / 3 / 2", "4/(2-2)", "1 +"} {
		value, err := evaluate(expression)
		if err != nil {
			fmt.Printf("%s -> error\n", expression)
		} else {
			fmt.Printf("%s -> %d\n", expression, value)
		}
	}
}
