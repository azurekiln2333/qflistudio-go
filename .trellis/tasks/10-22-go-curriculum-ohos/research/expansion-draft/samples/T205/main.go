package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"fmt"
)

func main() {
	public, private, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		panic(err)
	}
	manifest := []byte("files=2;version=3")
	signature := ed25519.Sign(private, manifest)
	fmt.Printf("signature-bytes=%d\nvalid=%t\nchanged=%t\n", len(signature), ed25519.Verify(public, manifest, signature), ed25519.Verify(public, []byte("files=9;version=3"), signature))
	signature[0] ^= 1
	fmt.Printf("bad-signature=%t\n", ed25519.Verify(public, manifest, signature))
}
