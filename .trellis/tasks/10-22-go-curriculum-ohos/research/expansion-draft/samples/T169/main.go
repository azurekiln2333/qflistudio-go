package main

import (
	"fmt"
	"math"
)

func sum(values []int64) (int64, int, error) {
	var total int64
	for i, value := range values {
		if (value > 0 && total > math.MaxInt64-value) || (value < 0 && total < math.MinInt64-value) {
			return total, i, fmt.Errorf("sum overflow")
		}
		total += value
	}
	return total, -1, nil
}
func main() {
	total, _, err := sum([]int64{100, -30, 20})
	if err != nil {
		panic(err)
	}
	fmt.Printf("ok=%d\n", total)
	total, index, err := sum([]int64{math.MaxInt64 - 2, 2, 1})
	fmt.Printf("positive=%d index=%d rejected=%t\n", total, index, err != nil)
	total, index, err = sum([]int64{math.MinInt64 + 1, -1, -1})
	fmt.Printf("negative=%d index=%d rejected=%t\n", total, index, err != nil)
}
