package main

import (
	"fmt"
	"strings"
)

func main() {
	escape := strings.NewReplacer("|", `\|`, `\`, `\\`, "\n", `\n`)
	fmt.Printf("escaped=%s\n", escape.Replace("a|b\\c\nnext"))
	first := strings.NewReplacer("a", "1", "ab", "2")
	longest := strings.NewReplacer("ab", "2", "a", "1")
	fmt.Printf("first=%s\n", first.Replace("ab a"))
	fmt.Printf("longest=%s\n", longest.Replace("ab a"))
}
