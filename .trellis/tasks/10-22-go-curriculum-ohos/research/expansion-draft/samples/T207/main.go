package main

import (
	"bytes"
	"crypto/ecdh"
	"crypto/rand"
	"fmt"
)

func main() {
	curve := ecdh.P256()
	alice, err := curve.GenerateKey(rand.Reader)
	if err != nil {
		panic(err)
	}
	bob, err := curve.GenerateKey(rand.Reader)
	if err != nil {
		panic(err)
	}
	first, err := alice.ECDH(bob.PublicKey())
	if err != nil {
		panic(err)
	}
	second, err := bob.ECDH(alice.PublicKey())
	if err != nil {
		panic(err)
	}
	fmt.Printf("same=%t\nsecret-bytes=%d\n", bytes.Equal(first, second), len(first))
	_, err = curve.NewPublicKey([]byte{1, 2, 3})
	fmt.Printf("bad-key-rejected=%t\n", err != nil)
}
