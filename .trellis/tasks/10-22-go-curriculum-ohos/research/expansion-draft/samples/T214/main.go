package main

import (
	"archive/zip"
	"bytes"
	"fmt"
	"io"
	"sort"
)

func main() {
	var data bytes.Buffer
	w := zip.NewWriter(&data)
	for _, item := range []struct{ name, text string }{{"sales.csv", "a,10\n"}, {"stock.csv", "a,3\n"}} {
		f, err := w.Create(item.name)
		if err != nil {
			panic(err)
		}
		if _, err = io.WriteString(f, item.text); err != nil {
			panic(err)
		}
	}
	if err := w.Close(); err != nil {
		panic(err)
	}
	r, err := zip.NewReader(bytes.NewReader(data.Bytes()), int64(data.Len()))
	if err != nil {
		panic(err)
	}
	rows := []string{}
	for _, file := range r.File {
		f, err := file.Open()
		if err != nil {
			panic(err)
		}
		body, err := io.ReadAll(f)
		f.Close()
		if err != nil {
			panic(err)
		}
		rows = append(rows, fmt.Sprintf("%s:%d", file.Name, len(body)))
	}
	sort.Strings(rows)
	for _, row := range rows {
		fmt.Println(row)
	}
	fmt.Printf("entries=%d\n", len(rows))
}
