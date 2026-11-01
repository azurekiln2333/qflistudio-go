package main

import (
	"encoding/base32"
	"fmt"
	"strings"
)

func main() {
	codec := base32.StdEncoding.WithPadding(base32.NoPadding)
	id := codec.EncodeToString([]byte("foo"))
	restored, err := codec.DecodeString(id)
	if err != nil {
		panic(err)
	}
	fmt.Printf("id=%s restored=%s\n", id, restored)
	lower := strings.ToLower(id)
	_, err = codec.DecodeString(lower)
	fmt.Printf("lower-rejected=%t\n", err != nil)
	normalized, err := codec.DecodeString(strings.ToUpper(lower))
	fmt.Printf("normalized=%t\n", err == nil && string(normalized) == "foo")
}
