package main

import (
	"fmt"
	"strings"
)

func hostname(text string) bool {
	if text == "" || len(text) > 253 {
		return false
	}
	for _, label := range strings.Split(text, ".") {
		if len(label) == 0 || len(label) > 63 || label[0] == '-' || label[len(label)-1] == '-' {
			return false
		}
		for _, c := range label {
			if !(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '-') {
				return false
			}
		}
	}
	return true
}
func main() {
	for _, text := range []string{"api.example.test", "-bad.test", "a..test", "中文.test", strings.Repeat("a", 64) + ".test"} {
		fmt.Printf("valid=%t\n", hostname(text))
	}
}
