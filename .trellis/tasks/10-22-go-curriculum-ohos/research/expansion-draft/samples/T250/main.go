package main

import (
	"fmt"
	"strings"
)

func progress(done, total, width int) string {
	if width <= 0 {
		return "[]"
	}
	if total <= 0 {
		return "[" + strings.Repeat("-", width) + "] n/a"
	}
	if done < 0 {
		done = 0
	}
	if done > total {
		done = total
	}
	filled := int(float64(done) / float64(total) * float64(width))
	return fmt.Sprintf("[%s%s] %d/%d", strings.Repeat("#", filled), strings.Repeat("-", width-filled), done, total)
}
func main() {
	for _, pair := range [][2]int{{0, 8}, {3, 8}, {10, 8}, {-2, 8}, {0, 0}} {
		fmt.Println(progress(pair[0], pair[1], 8))
	}
}
