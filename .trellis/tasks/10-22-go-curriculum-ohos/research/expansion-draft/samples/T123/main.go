package main

import (
	"fmt"
	"regexp"
	"strings"
)

func redact(line string) string {
	fields := regexp.MustCompile(`(^|[[:space:]])(email|token)=[^[:space:]]+`)
	return fields.ReplaceAllStringFunc(line, func(field string) string {
		key, _, _ := strings.Cut(field, "=")
		return key + "=***"
	})
}

func main() {
	fmt.Println(redact("10:00 INFO email=lin@example.test token=abc message=ready"))
	fmt.Println(redact("token=secret nottoken=visible message=email-help"))
}
