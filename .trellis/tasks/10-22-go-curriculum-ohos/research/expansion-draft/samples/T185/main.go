package main

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	directory, err := os.MkdirTemp("", "qfli-replace-")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(directory)
	target := filepath.Join(directory, "state.txt")
	if err := os.WriteFile(target, []byte("old\n"), 0600); err != nil {
		panic(err)
	}
	replacement, err := os.CreateTemp(directory, "next-*")
	if err != nil {
		panic(err)
	}
	name := replacement.Name()
	if _, err := replacement.WriteString("new\n"); err != nil {
		replacement.Close()
		panic(err)
	}
	if err := replacement.Close(); err != nil {
		panic(err)
	}
	if err := os.Rename(name, target); err != nil {
		panic(err)
	}
	data, err := os.ReadFile(target)
	if err != nil {
		panic(err)
	}
	_, gone := os.Stat(name)
	fmt.Printf("content=%s source-gone=%t\n", strings.TrimSuffix(string(data), "\n"), errors.Is(gone, os.ErrNotExist))
	if err := os.RemoveAll(directory); err != nil {
		panic(err)
	}
	_, err = os.Stat(directory)
	fmt.Printf("cleaned=%t\n", errors.Is(err, os.ErrNotExist))
}
