package main

import (
	"archive/tar"
	"bytes"
	"fmt"
	"io"
)

func main() {
	var archive bytes.Buffer
	w := tar.NewWriter(&archive)
	for _, item := range []struct{ name, text string }{{"notes.txt", "skip"}, {"docs/readme.txt", "offline guide"}} {
		if err := w.WriteHeader(&tar.Header{Name: item.name, Mode: 0600, Size: int64(len(item.text)), Typeflag: tar.TypeReg}); err != nil {
			panic(err)
		}
		if _, err := io.WriteString(w, item.text); err != nil {
			panic(err)
		}
	}
	if err := w.Close(); err != nil {
		panic(err)
	}
	r := tar.NewReader(bytes.NewReader(archive.Bytes()))
	found := ""
	for {
		h, err := r.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			panic(err)
		}
		if h.Name != "docs/readme.txt" {
			continue
		}
		if h.Typeflag != tar.TypeReg || h.Size > 64 {
			panic("invalid target")
		}
		data, err := io.ReadAll(r)
		if err != nil {
			panic(err)
		}
		found = string(data)
	}
	fmt.Printf("document=%s\nbytes=%d\n", found, len(found))
}
