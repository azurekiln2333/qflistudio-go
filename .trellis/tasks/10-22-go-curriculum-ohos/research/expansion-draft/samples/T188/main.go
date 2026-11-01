package main

import (
	"fmt"
	"path/filepath"
	"strings"
)

func main() {
	oldRoot := "workspace-old"
	source := filepath.Join(oldRoot, "docs", "guides", "start.md")
	target := filepath.Join(oldRoot, "docs", "images", "logo.svg")
	relative, err := filepath.Rel(filepath.Dir(source), target)
	if err != nil {
		panic(err)
	}
	newRoot := "workspace-new"
	newSource := filepath.Join(newRoot, "docs", "guides", "start.md")
	resolved := filepath.Clean(filepath.Join(filepath.Dir(newSource), relative))
	expected := filepath.Join(newRoot, "docs", "images", "logo.svg")
	contained, err := filepath.Rel(newRoot, resolved)
	if err != nil {
		panic(err)
	}
	inside := contained != ".." && !strings.HasPrefix(contained, ".."+string(filepath.Separator)) && !filepath.IsAbs(contained)
	fmt.Printf("link=%s\nrebased=%t inside=%t\n", filepath.ToSlash(relative), resolved == expected, inside)
}
