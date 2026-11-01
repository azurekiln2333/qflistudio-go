package main

import (
	"fmt"
	"net/url"
	"strings"
)

func allowed(text string) bool {
	u, err := url.Parse(text)
	if err != nil || u.Scheme != "https" || u.User != nil || u.Opaque != "" {
		return false
	}
	host := strings.ToLower(u.Hostname())
	if u.Port() != "" && u.Port() != "443" {
		return false
	}
	return host == "example.test" || strings.HasSuffix(host, ".example.test")
}
func main() {
	for _, text := range []string{"https://api.example.test/a", "http://example.test", "https://user@example.test", "https://example.test.evil", "https://evil-example.test", "https://example.test:8443"} {
		fmt.Printf("%s=%t\n", text, allowed(text))
	}
}
