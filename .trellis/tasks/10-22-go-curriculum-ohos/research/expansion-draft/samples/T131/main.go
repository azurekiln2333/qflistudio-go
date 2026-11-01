package main

import (
	"encoding/hex"
	"fmt"
	"strings"
)

func decode(text string) ([]byte, error) {
	return hex.DecodeString(strings.Join(strings.Fields(text), ""))
}

func main() {
	data, err := decode("0A ff\t10")
	if err != nil {
		panic(err)
	}
	fmt.Printf("bytes=%s length=%d\n", hex.EncodeToString(data), len(data))
	_, err = decode("abc")
	fmt.Printf("odd-rejected=%t\n", err != nil)
	_, err = decode("00 zz")
	fmt.Printf("invalid-rejected=%t\n", err != nil)
}
