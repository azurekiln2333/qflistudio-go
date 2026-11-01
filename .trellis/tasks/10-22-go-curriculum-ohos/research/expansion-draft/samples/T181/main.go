package main

import (
	"fmt"
	"path"
	"strings"
)

func projectPath(input string) (string, error) {
	if input == "" || path.IsAbs(input) || strings.Contains(input, `\`) {
		return "", fmt.Errorf("invalid relative path")
	}
	clean := path.Clean(input)
	if clean == "." || clean == ".." || strings.HasPrefix(clean, "../") {
		return "", fmt.Errorf("outside project")
	}
	return clean, nil
}
func main() {
	clean, err := projectPath("docs/../notes/main.go")
	if err != nil {
		panic(err)
	}
	fmt.Printf("clean=%s\n", clean)
	for _, input := range []string{"../secret", "/tmp/x", `dir\file`} {
		_, err := projectPath(input)
		fmt.Printf("rejected=%t\n", err != nil)
	}
}
