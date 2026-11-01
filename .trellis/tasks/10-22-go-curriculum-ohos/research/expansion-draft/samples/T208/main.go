package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/x509"
	"encoding/pem"
	"fmt"
)

func main() {
	public, _, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		panic(err)
	}
	der, err := x509.MarshalPKIXPublicKey(public)
	if err != nil {
		panic(err)
	}
	encoded := pem.EncodeToMemory(&pem.Block{Type: "PUBLIC KEY", Bytes: der})
	block, rest := pem.Decode(encoded)
	if block == nil || block.Type != "PUBLIC KEY" || len(rest) != 0 {
		panic("unexpected PEM")
	}
	parsed, err := x509.ParsePKIXPublicKey(block.Bytes)
	if err != nil {
		panic(err)
	}
	restored, ok := parsed.(ed25519.PublicKey)
	fmt.Printf("block=%s\nroundtrip=%t\n", block.Type, ok && bytes.Equal(public, restored))
	bad, _ := pem.Decode([]byte("not a PEM block"))
	fmt.Printf("invalid-rejected=%t\n", bad == nil)
}
