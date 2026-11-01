package main

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

func cell(text string, width int) string {
	runes := []rune(text)
	if len(runes) > width {
		runes = runes[:width]
	}
	out := string(runes)
	return out + strings.Repeat(" ", width-utf8.RuneCountInString(out))
}
func main() {
	for _, text := range []string{"Go", "离线工具", "A😀BC"} {
		value := cell(text, 3)
		fmt.Printf("|%s| runes=%d\n", value, utf8.RuneCountInString(value))
	}
}
