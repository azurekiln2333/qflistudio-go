package main

import (
	"fmt"
	"strings"
	"unicode"
)

func identifier(text string) string {
	var out strings.Builder
	pending := false
	for _, r := range text {
		if unicode.IsLetter(r) || unicode.IsNumber(r) {
			if pending && out.Len() > 0 {
				out.WriteByte('-')
			}
			out.WriteRune(unicode.ToLower(r))
			pending = false
		} else {
			pending = true
		}
	}
	return out.String()
}

func main() {
	fmt.Println(identifier("  Go 工具：离线 / 版本 2! "))
	fmt.Printf("merged=%s\n", identifier("A---B__C"))
	fmt.Printf("empty=%t\n", identifier(" !? ") == "")
}
