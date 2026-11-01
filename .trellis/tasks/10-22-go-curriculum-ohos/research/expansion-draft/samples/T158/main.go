package main

import (
	"fmt"
	"sort"
)

func page(data []int, after, size int) ([]int, bool, error) {
	if size < 1 || size > 100 || !sort.IntsAreSorted(data) {
		return nil, false, fmt.Errorf("invalid page request")
	}
	start := sort.Search(len(data), func(i int) bool { return data[i] > after })
	count := len(data) - start
	if count > size {
		count = size
	}
	end := start + count
	return append([]int{}, data[start:end]...), end < len(data), nil
}
func main() {
	data := []int{10, 20, 30, 40, 50}
	for _, after := range []int{25, 40, 50} {
		items, more, err := page(data, after, 2)
		if err != nil {
			panic(err)
		}
		fmt.Printf("after%d=%v more=%t\n", after, items, more)
	}
}
