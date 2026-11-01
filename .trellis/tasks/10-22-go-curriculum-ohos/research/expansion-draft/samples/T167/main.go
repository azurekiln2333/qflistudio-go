package main

import (
	"fmt"
	"sort"
)

func histogram(values, bounds []int) ([]int, int, error) {
	for i, bound := range bounds {
		if bound <= 0 || (i > 0 && bound <= bounds[i-1]) {
			return nil, 0, fmt.Errorf("invalid bounds")
		}
	}
	counts := make([]int, len(bounds)+1)
	rejected := 0
	for _, value := range values {
		if value < 0 {
			rejected++
			continue
		}
		bucket := sort.Search(len(bounds), func(i int) bool { return value < bounds[i] })
		counts[bucket]++
	}
	return counts, rejected, nil
}
func main() {
	counts, rejected, err := histogram([]int{0, 9, 10, 49, 50, 99, 100, 150, -1}, []int{10, 50, 100})
	if err != nil {
		panic(err)
	}
	fmt.Printf("under10=%d under50=%d under100=%d overflow=%d\n", counts[0], counts[1], counts[2], counts[3])
	fmt.Printf("negative-rejected=%d\n", rejected)
}
