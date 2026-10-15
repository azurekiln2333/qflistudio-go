package main

import (
	"fmt"
	"sort"
)

func main() {
	nums := []int{1, 3, 5, 7, 9}
	target := 6
	i := sort.SearchInts(nums, target)
	fmt.Printf("insert position for %d: %d\n", target, i)

	j := sort.Search(len(nums), func(i int) bool { return nums[i] >= 7 })
	fmt.Printf("first >= 7 at index %d\n", j)
}
