package main

import (
	"crypto/subtle"
	"encoding/hex"
	"fmt"
)

func valid(input string, want []byte) bool {
	decoded, err := hex.DecodeString(input)
	if err != nil || len(decoded) != len(want) || len(want) != 4 {
		return false
	}
	return subtle.ConstantTimeCompare(decoded, want) == 1
}
func main() {
	token := []byte{0x21, 0x4a, 0xb0, 0x09}
	for _, input := range []string{"214ab009", "214ab008", "21", "zzzzzzzz"} {
		fmt.Printf("%s=%t\n", input, valid(input, token))
	}
}
