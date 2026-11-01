package main

import (
	"bytes"
	"fmt"
	"io"
)

func main() {
	for _, input := range []struct {
		Label string
		Data  string
	}{{"empty", ""}, {"partial", "ab"}, {"full", "abcd"}} {
		buffer := make([]byte, 4)
		n, err := io.ReadFull(bytes.NewReader([]byte(input.Data)), buffer)
		status := "complete"
		if err == io.EOF {
			status = "EOF"
		} else if err == io.ErrUnexpectedEOF {
			status = "UnexpectedEOF"
		} else if err != nil {
			panic(err)
		}
		fmt.Printf("%s:%s bytes=%d\n", input.Label, status, n)
	}
}
