package main

import (
	"fmt"
	"strings"
)

func fields(text string) ([]string, error) {
	result := []string{}
	var current strings.Builder
	escaped := false
	for _, c := range text {
		if escaped {
			if c != ';' && c != '\\' {
				return nil, fmt.Errorf("bad escape")
			}
			current.WriteRune(c)
			escaped = false
			continue
		}
		switch c {
		case '\\':
			escaped = true
		case ';':
			result = append(result, current.String())
			current.Reset()
		default:
			current.WriteRune(c)
		}
	}
	if escaped {
		return nil, fmt.Errorf("trailing escape")
	}
	return append(result, current.String()), nil
}
func main() {
	values, err := fields(`a\;b;c\\d;`)
	if err != nil {
		panic(err)
	}
	fmt.Printf("fields=%d\nfirst=%s\nsecond=%s\nempty-last=%t\n", len(values), values[0], values[1], values[2] == "")
	_, err = fields(`bad\x`)
	fmt.Printf("invalid=%t\n", err != nil)
}
