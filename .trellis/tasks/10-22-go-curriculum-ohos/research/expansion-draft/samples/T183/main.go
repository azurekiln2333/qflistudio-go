package main

import (
	"fmt"
	"io/fs"
	"sort"
	"strings"
	"testing/fstest"
)

func main() {
	tree := fstest.MapFS{"docs/a.md": &fstest.MapFile{}, "docs/b.txt": &fstest.MapFile{}, "docs/nested/c.md": &fstest.MapFile{}, "readme.md": &fstest.MapFile{}}
	direct, err := fs.Glob(tree, "docs/*.md")
	if err != nil {
		panic(err)
	}
	recursive := []string{}
	err = fs.WalkDir(tree, "docs", func(name string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !entry.IsDir() && strings.HasSuffix(name, ".md") {
			recursive = append(recursive, name)
		}
		return nil
	})
	if err != nil {
		panic(err)
	}
	sort.Strings(recursive)
	fmt.Printf("glob=%v\nrecursive=%v\n", direct, recursive)
	_, err = fs.Glob(tree, "[")
	fmt.Printf("bad-pattern=%t\n", err != nil)
}
