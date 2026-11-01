package main

import (
	"archive/tar"
	"bytes"
	"fmt"
	"io"
	"sort"
)

func main() {
	var data bytes.Buffer
	w := tar.NewWriter(&data)
	for _, h := range []*tar.Header{{Name: "docs/", Mode: 0755, Typeflag: tar.TypeDir}, {Name: "docs/run.sh", Mode: 0750, Size: 3, Typeflag: tar.TypeReg}} {
		if err := w.WriteHeader(h); err != nil {
			panic(err)
		}
		if h.Size > 0 {
			if _, err := w.Write([]byte("go\n")); err != nil {
				panic(err)
			}
		}
	}
	if err := w.Close(); err != nil {
		panic(err)
	}
	r := tar.NewReader(bytes.NewReader(data.Bytes()))
	rows := []string{}
	for {
		h, err := r.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			panic(err)
		}
		kind := "file"
		if h.Typeflag == tar.TypeDir {
			kind = "dir"
		}
		rows = append(rows, fmt.Sprintf("%s %s %04o %d", h.Name, kind, h.Mode, h.Size))
	}
	sort.Strings(rows)
	for _, row := range rows {
		fmt.Println(row)
	}
}
