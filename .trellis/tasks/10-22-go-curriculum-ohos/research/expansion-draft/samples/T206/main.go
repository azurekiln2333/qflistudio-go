package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"fmt"
)

func main() {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		panic(err)
	}
	digest := sha256.Sum256([]byte("release:42"))
	signature, err := ecdsa.SignASN1(rand.Reader, key, digest[:])
	if err != nil {
		panic(err)
	}
	changed := sha256.Sum256([]byte("release:43"))
	fmt.Printf("valid=%t\nchanged=%t\nmalformed=%t\n", ecdsa.VerifyASN1(&key.PublicKey, digest[:], signature), ecdsa.VerifyASN1(&key.PublicKey, changed[:], signature), ecdsa.VerifyASN1(&key.PublicKey, digest[:], []byte{1, 2, 3}))
}
