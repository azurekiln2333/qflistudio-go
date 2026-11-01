package main

import (
	"fmt"
	"strconv"
	"strings"
)

func capacity(text string) (uint64, error) {
	text = strings.TrimSpace(text)
	factor := uint64(1)
	if strings.HasSuffix(text, "MiB") {
		factor = 1 << 20
		text = strings.TrimSuffix(text, "MiB")
	} else if strings.HasSuffix(text, "KB") {
		factor = 1000
		text = strings.TrimSuffix(text, "KB")
	}
	value, err := strconv.ParseUint(strings.TrimSpace(text), 10, 64)
	if err != nil {
		return 0, err
	}
	const maximum uint64 = 1<<63 - 1
	if value > maximum/factor {
		return 0, fmt.Errorf("capacity overflow")
	}
	return value * factor, nil
}
func main() {
	for _, input := range []string{"2KB", "2MiB", "512"} {
		value, err := capacity(input)
		if err != nil {
			panic(err)
		}
		fmt.Printf("%s=%d\n", input, value)
	}
	_, err := capacity("3MB")
	fmt.Printf("unknown=%t\n", err != nil)
	_, err = capacity("-1KB")
	fmt.Printf("negative=%t\n", err != nil)
	_, err = capacity("9223372036854775807MiB")
	fmt.Printf("overflow=%t\n", err != nil)
}
