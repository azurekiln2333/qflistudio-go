package main

import (
	"bufio"
	"fmt"
	"strings"
)

func inspect(text string) (int, int, error) {
	scanner := bufio.NewScanner(strings.NewReader(text))
	scanner.Buffer(make([]byte, 4), 12)
	count, longest := 0, 0
	for scanner.Scan() {
		count++
		if len(scanner.Text()) > longest {
			longest = len(scanner.Text())
		}
	}
	return count, longest, scanner.Err()
}

func main() {
	count, longest, err := inspect("short\n" + strings.Repeat("x", 9) + "\n")
	if err != nil {
		panic(err)
	}
	fmt.Printf("lines=%d longest=%d\n", count, longest)
	_, _, err = inspect(strings.Repeat("x", 14))
	fmt.Printf("oversized=%t\n", err != nil)
}
