package main

import (
	"bytes"
	"compress/zlib"
	"fmt"
	"io"
	"strings"
)

func compress(text string) []byte {
	var out bytes.Buffer
	w := zlib.NewWriter(&out)
	if _, err := io.WriteString(w, text); err != nil {
		panic(err)
	}
	if err := w.Close(); err != nil {
		panic(err)
	}
	return out.Bytes()
}
func decode(data []byte, budget int64) (string, error) {
	r, err := zlib.NewReader(bytes.NewReader(data))
	if err != nil {
		return "", err
	}
	defer r.Close()
	text, err := io.ReadAll(io.LimitReader(r, budget+1))
	if err != nil {
		return "", err
	}
	if int64(len(text)) > budget {
		return "", fmt.Errorf("expanded data over budget")
	}
	return string(text), nil
}
func main() {
	text, err := decode(compress("small"), 8)
	fmt.Printf("small=%s valid=%t\n", text, err == nil)
	_, err = decode(compress(strings.Repeat("a", 1000)), 8)
	fmt.Printf("expanded-rejected=%t\n", err != nil)
	text, err = decode(compress("12345678"), 8)
	fmt.Printf("exact-limit=%t\n", err == nil && len(text) == 8)
}
