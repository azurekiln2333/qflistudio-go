package main

import (
	"fmt"
)

type Opening struct {
	Rune   rune
	Offset int
}

func brackets(text string) (int, error) {
	stack := []Opening{}
	pairs := map[rune]rune{')': '(', ']': '[', '}': '{'}
	for offset, c := range text {
		switch c {
		case '(', '[', '{':
			stack = append(stack, Opening{c, offset})
		case ')', ']', '}':
			if len(stack) == 0 || stack[len(stack)-1].Rune != pairs[c] {
				return offset, fmt.Errorf("mismatch")
			}
			stack = stack[:len(stack)-1]
		}
	}
	if len(stack) > 0 {
		return stack[len(stack)-1].Offset, fmt.Errorf("unclosed")
	}
	return -1, nil
}
func main() {
	_, err := brackets("中{a+[b*(c)]}")
	fmt.Printf("nested-valid=%t\n", err == nil)
	offset, err := brackets("中(a]")
	fmt.Printf("mismatch=%t byte-offset=%d\n", err != nil, offset)
	offset, err = brackets("abc(")
	fmt.Printf("unclosed=%t byte-offset=%d\n", err != nil, offset)
}
