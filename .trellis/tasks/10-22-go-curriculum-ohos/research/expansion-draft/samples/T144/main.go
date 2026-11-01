package main

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"io"
	"strings"
)

type CountReader struct {
	Inner io.Reader
	Bytes int
}

func (r *CountReader) Read(buffer []byte) (int, error) {
	n, err := r.Inner.Read(buffer)
	r.Bytes += n
	return n, err
}
func main() {
	source := &CountReader{Inner: strings.NewReader("offline")}
	digest := sha256.New()
	var copy bytes.Buffer
	n, err := io.Copy(&copy, io.TeeReader(source, digest))
	if err != nil {
		panic(err)
	}
	expected := sha256.Sum256([]byte("offline"))
	fmt.Printf("copied=%d source-bytes=%d\n", n, source.Bytes)
	fmt.Printf("digest=%t content=%s\n", bytes.Equal(digest.Sum(nil), expected[:]), copy.String())
}
