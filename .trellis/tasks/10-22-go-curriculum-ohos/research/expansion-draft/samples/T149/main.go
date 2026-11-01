package main

import (
	"bufio"
	"bytes"
	"fmt"
	"strings"
)

func protocol(reader *bufio.Reader) (string, error) {
	prefix, err := reader.Peek(4)
	if err != nil {
		return "", err
	}
	if !bytes.Equal(prefix, []byte("LOG|")) {
		return "", fmt.Errorf("unknown prefix")
	}
	return "LOG", nil
}
func main() {
	reader := bufio.NewReader(strings.NewReader("LOG|ready\n"))
	kind, err := protocol(reader)
	if err != nil {
		panic(err)
	}
	record, err := reader.ReadString('\n')
	if err != nil {
		panic(err)
	}
	fmt.Printf("protocol=%s record=%s", kind, record)
	_, err = protocol(bufio.NewReader(strings.NewReader("BIN!data")))
	fmt.Printf("unknown=%t\n", err != nil)
}
