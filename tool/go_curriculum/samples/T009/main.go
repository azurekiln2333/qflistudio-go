package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func main() {
	in := "alpha beta\ngamma\n"
	scanner := bufio.NewScanner(strings.NewReader(in))
	lines := 0
	words := 0
	for scanner.Scan() {
		lines++
		words += len(strings.Fields(scanner.Text()))
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return
	}
	fmt.Printf("lines=%d words=%d\n", lines, words)
}
