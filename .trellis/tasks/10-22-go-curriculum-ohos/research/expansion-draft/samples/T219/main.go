package main

import (
	"bytes"
	"encoding/base64"
	"fmt"
	"io"
)

func main() {
	var wire bytes.Buffer
	w := base64.NewEncoder(base64.StdEncoding, &wire)
	for _, chunk := range []string{"g", "o", ":", "42"} {
		if _, err := io.WriteString(w, chunk); err != nil {
			panic(err)
		}
	}
	fmt.Printf("before=%s\n", wire.String())
	if err := w.Close(); err != nil {
		panic(err)
	}
	fmt.Printf("after=%s\n", wire.String())
	decoded, err := io.ReadAll(base64.NewDecoder(base64.StdEncoding, bytes.NewReader(wire.Bytes())))
	if err != nil {
		panic(err)
	}
	fmt.Printf("roundtrip=%t\n", string(decoded) == "go:42")
}
