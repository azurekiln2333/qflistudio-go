package main

import (
	"bufio"
	"bytes"
	"fmt"
)

func main() {
	var destination bytes.Buffer
	writer := bufio.NewWriterSize(&destination, 32)
	if _, err := writer.WriteString("alpha\n"); err != nil {
		panic(err)
	}
	if _, err := writer.WriteString("beta\n"); err != nil {
		panic(err)
	}
	fmt.Printf("before=%d buffered=%d\n", destination.Len(), writer.Buffered())
	if err := writer.Flush(); err != nil {
		panic(err)
	}
	fmt.Printf("after=%d content=%q\n", destination.Len(), destination.String())
	before := destination.Len()
	err := writer.Flush()
	fmt.Printf("second-flush=%t\n", err == nil && destination.Len() == before)
}
