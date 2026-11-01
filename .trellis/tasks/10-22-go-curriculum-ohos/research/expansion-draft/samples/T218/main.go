package main

import (
	"fmt"
	"mime"
)

func main() {
	media, params, err := mime.ParseMediaType(`Text/Plain; charset=utf-8; title="QFLI report"`)
	if err != nil {
		panic(err)
	}
	fmt.Printf("type=%s\ntitle=%s\nnormalized=%s\n", media, params["title"], mime.FormatMediaType(media, params))
	_, _, err = mime.ParseMediaType("text/plain; charset")
	fmt.Printf("invalid=%t\n", err != nil)
}
