package main

import (
	"fmt"
	"os"
	"strings"
)

func expand(text string, values map[string]string) (string, error) {
	missing := []string{}
	result := os.Expand(text, func(name string) string {
		if name == "$" {
			return "$"
		}
		value, ok := values[name]
		if !ok {
			missing = append(missing, name)
		}
		return value
	})
	if len(missing) > 0 {
		return "", fmt.Errorf("missing variables: %s", strings.Join(missing, ","))
	}
	return result, nil
}
func main() {
	values := map[string]string{"ROOT": "docs", "NAME": "guide", "EMPTY": ""}
	result, err := expand(`${ROOT}/$NAME cost=$$5 empty=${EMPTY}`, values)
	if err != nil {
		panic(err)
	}
	fmt.Printf("expanded=%s\n", result)
	_, err = expand(`${MISSING}`, values)
	fmt.Printf("missing=%t\n", err != nil)
	plain, err := expand("hello[world]", values)
	if err != nil {
		panic(err)
	}
	fmt.Printf("plain=%s\n", plain)
}
