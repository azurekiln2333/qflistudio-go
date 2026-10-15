package main

import (
	"fmt"
	"strings"
)

func main() {
	var b strings.Builder
	for i := 0; i < 3; i++ {
		fmt.Fprintf(&b, "item%d;", i)
	}
	out := b.String()
	fmt.Println(out, "len", len(out))
}
