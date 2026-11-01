package main

import (
	"crypto/sha256"
	"crypto/sha512"
	"fmt"
	"io"
	"strings"
)

func main() {
	input := "alpha\nbeta\n"
	small := sha256.New()
	large := sha512.New()
	copied, err := io.Copy(io.MultiWriter(small, large), strings.NewReader(input))
	if err != nil {
		panic(err)
	}
	expected := sha256.Sum256([]byte(input))
	fmt.Printf("bytes=%d\nlengths=%d,%d\nsha256-match=%t\n", copied, len(small.Sum(nil)), len(large.Sum(nil)), fmt.Sprintf("%x", small.Sum(nil)) == fmt.Sprintf("%x", expected))
}
