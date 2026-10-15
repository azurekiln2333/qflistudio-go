package main

import (
	"fmt"
	"strings"
)

func main() {
	s := "  Go, Rust; Go  "
	trimmed := strings.TrimSpace(s)
	parts := strings.FieldsFunc(trimmed, func(r rune) bool {
		return r == ',' || r == ';' || r == ' '
	})
	fmt.Printf("parts=%v count=%d\n", parts, len(parts))
	joined := strings.Join(parts, "|")
	fmt.Println("joined", joined)
	fmt.Println("contains Go:", strings.Contains(joined, "Go"))
	fmt.Println("replace:", strings.Replace(joined, "Go", "Golang", 1))
}
