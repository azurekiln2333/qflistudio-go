package main

import (
	"bytes"
	"fmt"
	"io"
	"mime/quotedprintable"
	"strings"
)

func main() {
	decoded, err := io.ReadAll(quotedprintable.NewReader(strings.NewReader("Subject=3A hello=\r\nworld=21")))
	if err != nil {
		panic(err)
	}
	fmt.Printf("decoded=%s\n", decoded)
	original := []byte("你好=go")
	var wire bytes.Buffer
	w := quotedprintable.NewWriter(&wire)
	if _, err = w.Write(original); err != nil {
		panic(err)
	}
	if err = w.Close(); err != nil {
		panic(err)
	}
	restored, err := io.ReadAll(quotedprintable.NewReader(&wire))
	if err != nil {
		panic(err)
	}
	fmt.Printf("utf8-roundtrip=%t\n", bytes.Equal(restored, original))
}
