package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	s := "héllo, 世界"
	fmt.Println("bytes:", len(s))
	fmt.Println("runes:", utf8.RuneCountInString(s))
	for i, r := range s {
		fmt.Printf("at %d: %c\n", i, r)
	}
}
