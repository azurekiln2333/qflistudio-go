package main

import "fmt"

func sum(nums ...int) int {
	total := 0
	for _, n := range nums {
		total += n
	}
	return total
}

func main() {
	fmt.Println(sum(1, 2, 3))
	values := []int{4, 5, 6}
	fmt.Println(sum(values...)) // 展开切片
}
