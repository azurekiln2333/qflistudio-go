package main

import (
	"fmt"
	"net/url"
	"sort"
)

func main() {
	input, err := url.ParseQuery("tag=offline&secret=x&page=2&tag=go")
	if err != nil {
		panic(err)
	}
	allowed := map[string]bool{"tag": true, "page": true}
	clean := url.Values{}
	dropped := 0
	for key, values := range input {
		if !allowed[key] {
			dropped++
			continue
		}
		copyValues := append([]string(nil), values...)
		sort.Strings(copyValues)
		clean[key] = copyValues
	}
	fmt.Printf("query=%s\ndropped-keys=%d\ntag-count=%d\n", clean.Encode(), dropped, len(clean["tag"]))
	_, err = url.ParseQuery("name=%ZZ")
	fmt.Printf("invalid-escape=%t\n", err != nil)
}
