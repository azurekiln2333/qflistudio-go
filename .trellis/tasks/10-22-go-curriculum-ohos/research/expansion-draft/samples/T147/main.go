package main

import (
	"fmt"
	"io"
	"strings"
)

func readBudget(reader io.Reader, max int64) ([]byte, error) {
	if max < 0 || max > 1024 {
		return nil, fmt.Errorf("invalid budget")
	}
	data, err := io.ReadAll(io.LimitReader(reader, max+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > max {
		return nil, fmt.Errorf("input exceeds budget")
	}
	return data, nil
}
func main() {
	data, err := readBudget(strings.NewReader("data"), 4)
	if err != nil {
		panic(err)
	}
	fmt.Printf("exact=%s\n", data)
	_, err = readBudget(strings.NewReader("extra"), 4)
	fmt.Printf("oversized=%t\n", err != nil)
	empty, err := readBudget(strings.NewReader(""), 0)
	fmt.Printf("zero=%d valid=%t\n", len(empty), err == nil)
}
