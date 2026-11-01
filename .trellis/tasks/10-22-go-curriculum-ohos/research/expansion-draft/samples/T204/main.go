package main

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"fmt"
)

func main() {
	key := make([]byte, 32)
	if _, err := rand.Read(key); err != nil {
		panic(err)
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		panic(err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		panic(err)
	}
	nonce := make([]byte, gcm.NonceSize())
	if _, err := rand.Read(nonce); err != nil {
		panic(err)
	}
	message := []byte("offline report")
	aad := []byte("report:v1")
	sealed := gcm.Seal(nil, nonce, message, aad)
	plain, err := gcm.Open(nil, nonce, sealed, aad)
	fmt.Printf("roundtrip=%t\n", err == nil && bytes.Equal(plain, message))
	sealed[len(sealed)-1] ^= 1
	_, err = gcm.Open(nil, nonce, sealed, aad)
	fmt.Printf("tamper-rejected=%t\n", err != nil)
}
