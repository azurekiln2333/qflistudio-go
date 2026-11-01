package main

import (
	"fmt"
	"strings"
)

func strip(text string) (string, error) {
	var out strings.Builder
	for i := 0; i < len(text); {
		if text[i] == 27 && i+1 < len(text) && text[i+1] == '[' {
			j := i + 2
			for j < len(text) && ((text[j] >= '0' && text[j] <= '9') || text[j] == ';') {
				j++
			}
			if j == len(text) {
				return "", fmt.Errorf("truncated SGR")
			}
			if text[j] == 'm' {
				i = j + 1
				continue
			}
		}
		out.WriteByte(text[i])
		i++
	}
	return out.String(), nil
}
func main() {
	clean, err := strip("A [tag] \x1b[31m红色\x1b[0m B")
	if err != nil {
		panic(err)
	}
	fmt.Println(clean)
	other := "\x1b[2J"
	preserved, err := strip(other)
	fmt.Printf("other-preserved=%t\n", err == nil && preserved == other)
	_, err = strip("\x1b[31")
	fmt.Printf("truncated=%t\n", err != nil)
}
