package main

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

func common(names []string) (string, string) {
	if len(names) == 0 {
		return "", ""
	}
	prefix, suffix := []rune(names[0]), []rune(names[0])
	for _, name := range names[1:] {
		for !strings.HasPrefix(name, string(prefix)) {
			prefix = prefix[:len(prefix)-1]
		}
		for !strings.HasSuffix(name, string(suffix)) {
			suffix = suffix[1:]
		}
	}
	return string(prefix), string(suffix)
}

func main() {
	prefix, suffix := common([]string{"报告-2024.csv", "报告-2025.csv", "报告-2026.csv"})
	fmt.Printf("prefix=%s suffix=%s\n", prefix, suffix)
	fmt.Printf("utf8=%t\n", utf8.ValidString(prefix) && utf8.ValidString(suffix))
	a, b := common(nil)
	fmt.Printf("empty=%t\n", a == "" && b == "")
}
