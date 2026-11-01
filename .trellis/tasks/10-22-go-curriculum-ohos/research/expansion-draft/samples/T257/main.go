package main

import (
	"fmt"
	"strings"
	"unicode"
)

func isbn(text string) bool {
	var digits strings.Builder
	for _, c := range text {
		if c == '-' || unicode.IsSpace(c) {
			continue
		}
		if c < '0' || c > '9' {
			return false
		}
		digits.WriteRune(c)
	}
	code := digits.String()
	if len(code) != 13 || !strings.HasPrefix(code, "978") && !strings.HasPrefix(code, "979") {
		return false
	}
	sum := 0
	for i := 0; i < len(code); i++ {
		weight := 1
		if i%2 == 1 {
			weight = 3
		}
		sum += int(code[i]-'0') * weight
	}
	return sum%10 == 0
}
func main() {
	for _, code := range []string{"978-0-306-40615-7", "9780306406158", "978030640615", "978 0 306 40615 7", "4006381333931"} {
		fmt.Printf("valid=%t\n", isbn(code))
	}
}
