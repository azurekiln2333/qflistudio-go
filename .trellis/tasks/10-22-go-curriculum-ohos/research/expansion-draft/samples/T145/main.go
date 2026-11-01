package main

import (
	"fmt"
	"io"
	"strings"
)

func main() {
	source := strings.NewReader("0123456789")
	first := io.NewSectionReader(source, 2, 4)
	second := io.NewSectionReader(source, 7, 8)
	a, err := io.ReadAll(first)
	if err != nil {
		panic(err)
	}
	b, err := io.ReadAll(second)
	if err != nil {
		panic(err)
	}
	position, err := source.Seek(0, io.SeekCurrent)
	if err != nil {
		panic(err)
	}
	fmt.Printf("first=%s second=%s cursor=%d\n", a, b, position)
	buffer := make([]byte, 2)
	n, err := first.ReadAt(buffer, 3)
	fmt.Printf("boundary=%t byte=%s\n", n == 1 && err == io.EOF, buffer[:n])
}
