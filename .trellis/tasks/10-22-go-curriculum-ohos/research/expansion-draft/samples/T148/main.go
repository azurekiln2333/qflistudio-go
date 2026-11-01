package main

import (
	"bytes"
	"fmt"
	"io"
)

type PlainReader struct{ Inner io.Reader }

func (r *PlainReader) Read(data []byte) (int, error) { return r.Inner.Read(data) }

type CountingWriter struct {
	Data  bytes.Buffer
	Calls int
}

func (w *CountingWriter) Write(data []byte) (int, error) {
	w.Calls++
	return w.Data.Write(data)
}
func main() {
	source := []byte("abcdefghij")
	reader := &PlainReader{bytes.NewReader(source)}
	writer := &CountingWriter{}
	buffer := make([]byte, 3)
	n, err := io.CopyBuffer(writer, reader, buffer)
	if err != nil {
		panic(err)
	}
	fmt.Printf("copied=%d writes=%d equal=%t\n", n, writer.Calls, bytes.Equal(source, writer.Data.Bytes()))
}
