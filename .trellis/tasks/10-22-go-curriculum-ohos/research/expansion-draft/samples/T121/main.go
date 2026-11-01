package main

import (
	"fmt"
	"strings"
)

func records(text string) []string {
	if text == "" {
		return nil
	}
	text = strings.ReplaceAll(text, "\r\n", "\n")
	text = strings.ReplaceAll(text, "\r", "\n")
	lines := strings.Split(text, "\n")
	if lines[len(lines)-1] == "" {
		lines = lines[:len(lines)-1]
	}
	return lines
}

func main() {
	lines := records("alpha\r\nbeta\rgamma")
	fmt.Printf("records=%d\n", len(lines))
	for i, line := range lines {
		fmt.Printf("%d:%s\n", i+1, line)
	}
	fmt.Printf("empty=%d trailing=%d\n", len(records("")), len(records("one\n")))
}
