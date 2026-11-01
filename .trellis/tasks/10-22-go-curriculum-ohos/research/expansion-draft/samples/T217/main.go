package main

import (
	"bytes"
	"fmt"
	"io"
	"mime/multipart"
)

func main() {
	var wire bytes.Buffer
	w := multipart.NewWriter(&wire)
	if err := w.SetBoundary("qfli-boundary"); err != nil {
		panic(err)
	}
	if err := w.WriteField("owner", "Li"); err != nil {
		panic(err)
	}
	file, err := w.CreateFormFile("upload", "notes.txt")
	if err != nil {
		panic(err)
	}
	if _, err = io.WriteString(file, "line1\n"); err != nil {
		panic(err)
	}
	if err = w.Close(); err != nil {
		panic(err)
	}
	r := multipart.NewReader(&wire, w.Boundary())
	for {
		part, err := r.NextPart()
		if err == io.EOF {
			break
		}
		if err != nil {
			panic(err)
		}
		body, err := io.ReadAll(part)
		if err != nil {
			panic(err)
		}
		part.Close()
		fmt.Printf("field=%s file=%q body=%q\n", part.FormName(), part.FileName(), string(body))
	}
}
