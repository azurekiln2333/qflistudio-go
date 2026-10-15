package main

import "fmt"

func main() {
	s := make([]int, 0, 2)
	fmt.Printf("start len=%d cap=%d\n", len(s), cap(s))
	for i := 1; i <= 5; i++ {
		s = append(s, i)
		fmt.Printf("after %d: len=%d cap=%d\n", i, len(s), cap(s))
	}
	fmt.Println("values", s)
}
