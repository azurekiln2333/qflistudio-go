package main

import (
	"bytes"
	"fmt"
	"io/fs"
	"sort"
	"testing/fstest"
)

func snapshot(tree fs.FS) (map[string][]byte, error) {
	files := map[string][]byte{}
	err := fs.WalkDir(tree, ".", func(name string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() {
			return nil
		}
		data, err := fs.ReadFile(tree, name)
		if err != nil {
			return err
		}
		files[name] = data
		return nil
	})
	return files, err
}
func main() {
	before, err := snapshot(fstest.MapFS{"keep.txt": &fstest.MapFile{Data: []byte("same")}, "change.txt": &fstest.MapFile{Data: []byte("old")}, "deleted.txt": &fstest.MapFile{Data: []byte("gone")}})
	if err != nil {
		panic(err)
	}
	after, err := snapshot(fstest.MapFS{"keep.txt": &fstest.MapFile{Data: []byte("same")}, "change.txt": &fstest.MapFile{Data: []byte("new")}, "added.txt": &fstest.MapFile{Data: []byte("hello")}})
	if err != nil {
		panic(err)
	}
	union := map[string]bool{}
	for name := range before {
		union[name] = true
	}
	for name := range after {
		union[name] = true
	}
	names := []string{}
	for name := range union {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		old, was := before[name]
		current, is := after[name]
		kind := ""
		if !was {
			kind = "added"
		} else if !is {
			kind = "deleted"
		} else if !bytes.Equal(old, current) {
			kind = "modified"
		}
		if kind != "" {
			fmt.Printf("%s %s\n", kind, name)
		}
	}
}
