package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"fmt"
)

func tag(key, message []byte) []byte {
	mac := hmac.New(sha256.New, key)
	mac.Write(message)
	return mac.Sum(nil)
}
func verify(key, message, want []byte) bool { return hmac.Equal(tag(key, message), want) }
func main() {
	key := []byte("lesson-only-shared-key")
	message := []byte("invoice:7:1250")
	signature := tag(key, message)
	fmt.Printf("tag-bytes=%d\nvalid=%t\ntampered=%t\nwrong-key=%t\n", len(signature), verify(key, message, signature), verify(key, []byte("invoice:7:9250"), signature), verify([]byte("other-key"), message, signature))
}
