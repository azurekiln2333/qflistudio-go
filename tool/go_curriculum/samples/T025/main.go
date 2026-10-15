package main

import "fmt"

func mapInts(in []int, f func(int) int) []int {
	out := make([]int, len(in))
	for i, v := range in {
		out[i] = f(v)
	}
	return out
}

func main() {
	double := func(v int) int { return v * 2 }
	nums := []int{1, 2, 3}
	fmt.Println(mapInts(nums, double))
	fmt.Println(mapInts(nums, func(v int) int { return v + 10 }))
}
