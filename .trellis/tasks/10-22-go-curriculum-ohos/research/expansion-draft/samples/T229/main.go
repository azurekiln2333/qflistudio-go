package main

import (
	"fmt"
	"net/url"
)

func main() {
	base, err := url.Parse("https://example.test/docs/guide/?lang=en")
	if err != nil {
		panic(err)
	}
	for _, text := range []string{"../api.html", "?lang=zh", "#usage", "/assets/a.png"} {
		ref, err := url.Parse(text)
		if err != nil {
			panic(err)
		}
		resolved := base.ResolveReference(ref)
		fmt.Printf("%s -> %s\n", text, resolved.String())
	}
	fmt.Printf("base-unchanged=%t\n", base.RawQuery == "lang=en")
}
