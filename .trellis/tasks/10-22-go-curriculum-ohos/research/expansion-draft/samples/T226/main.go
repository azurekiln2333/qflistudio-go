package main

import (
	"fmt"
	"mime"
	"strconv"
	"strings"
)

func choose(accept string) string {
	best := ""
	quality := 0.0
	for _, part := range strings.Split(accept, ",") {
		media, params, err := mime.ParseMediaType(strings.TrimSpace(part))
		if err != nil {
			continue
		}
		q := 1.0
		if value, ok := params["q"]; ok {
			q, err = strconv.ParseFloat(value, 64)
			if err != nil || q < 0 || q > 1 {
				continue
			}
		}
		if media != "text/plain" && media != "application/json" {
			continue
		}
		if q > quality {
			best = media
			quality = q
		}
	}
	return best
}
func main() {
	for _, input := range []string{"application/json;q=0.4, text/plain;q=0.9", "text/plain;q=0, application/json;q=0", "text/plain;q=bad, application/json"} {
		fmt.Printf("selected=%q\n", choose(input))
	}
}
