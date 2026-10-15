package main

import "fmt"

func main() {
	nums := []int{10, 20, 30}
	for i, v := range nums {
		fmt.Printf("slice %d=%d\n", i, v)
	}
	m := map[string]int{"a": 1, "b": 2}
	total := 0
	for _, v := range m {
		total += v
	}
	fmt.Println("map total", total)
	for i, r := range "ab" {
		fmt.Printf("str %d=%c\n", i, r)
	}
}
