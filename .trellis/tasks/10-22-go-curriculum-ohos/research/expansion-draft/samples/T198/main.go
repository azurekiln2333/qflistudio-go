package main

import (
	"fmt"
	"strings"
	"unicode"
)

func split(text string) ([]string, error) {
	arguments := []string{}
	var word strings.Builder
	quote := rune(0)
	escaped := false
	active := false
	for _, r := range text {
		if escaped {
			word.WriteRune(r)
			escaped = false
			active = true
			continue
		}
		if quote == '\'' {
			if r == quote {
				quote = 0
			} else {
				word.WriteRune(r)
			}
			continue
		}
		if quote == '"' {
			if r == '\\' {
				escaped = true
			} else if r == quote {
				quote = 0
			} else {
				word.WriteRune(r)
			}
			continue
		}
		if unicode.IsSpace(r) {
			if active {
				arguments = append(arguments, word.String())
				word.Reset()
				active = false
			}
			continue
		}
		active = true
		if r == '\'' || r == '"' {
			quote = r
		} else if r == '\\' {
			escaped = true
		} else {
			word.WriteRune(r)
		}
	}
	if quote != 0 || escaped {
		return nil, fmt.Errorf("unfinished quote or escape")
	}
	if active {
		arguments = append(arguments, word.String())
	}
	return arguments, nil
}
func main() {
	arguments, err := split(`run --name "Li Yu" 'literal\path' "" back\ slash`)
	if err != nil {
		panic(err)
	}
	fmt.Printf("tokens=%d\n%q\n", len(arguments), arguments)
	_, err = split(`run "unfinished`)
	fmt.Printf("unclosed=%t\n", err != nil)
	_, err = split(`run trailing\`)
	fmt.Printf("dangling=%t\n", err != nil)
}
