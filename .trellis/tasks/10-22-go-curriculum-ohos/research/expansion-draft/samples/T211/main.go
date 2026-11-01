package main

import (
	"bytes"
	"compress/gzip"
	"fmt"
	"io"
)

func main() {
	input := []byte("first\nsecond\n")
	var compressed bytes.Buffer
	writer := gzip.NewWriter(&compressed)
	if _, err := writer.Write(input); err != nil {
		panic(err)
	}
	if err := writer.Close(); err != nil {
		panic(err)
	}
	reader, err := gzip.NewReader(bytes.NewReader(compressed.Bytes()))
	if err != nil {
		panic(err)
	}
	restored, err := io.ReadAll(reader)
	if err != nil {
		panic(err)
	}
	if err = reader.Close(); err != nil {
		panic(err)
	}
	fmt.Printf("roundtrip=%t\nlines=%d\n", bytes.Equal(input, restored), bytes.Count(restored, []byte{'\n'}))
	truncated := compressed.Bytes()[:compressed.Len()-3]
	broken, err := gzip.NewReader(bytes.NewReader(truncated))
	if err != nil {
		panic(err)
	}
	_, err = io.ReadAll(broken)
	broken.Close()
	fmt.Printf("missing-trailer=%t\n", err != nil)
}
