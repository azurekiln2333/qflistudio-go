package main

import (
	"fmt"
	"io/fs"
	"strings"
	"testing/fstest"
)

func main() {
	tree := fstest.MapFS{"src/main.go": &fstest.MapFile{Data: []byte("abc")}, "src/lib/util.go": &fstest.MapFile{Data: []byte("12345")}, "src/cache/old.go": &fstest.MapFile{Data: []byte(strings.Repeat("x", 100))}, "notes.md": &fstest.MapFile{Data: []byte("notes")}}
	files := 0
	var bytes int64
	err := fs.WalkDir(tree, ".", func(name string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() {
			if entry.Name() == "cache" {
				return fs.SkipDir
			}
			return nil
		}
		if !strings.HasSuffix(name, ".go") {
			return nil
		}
		info, err := entry.Info()
		if err != nil {
			return err
		}
		files++
		bytes += info.Size()
		return nil
	})
	if err != nil {
		panic(err)
	}
	fmt.Printf("files=%d bytes=%d\n", files, bytes)
}
