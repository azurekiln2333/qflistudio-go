package main

import "fmt"

var memo = map[int]int{}

func fib(n int) int {
	if n < 2 {
		return n
	}
	if v, ok := memo[n]; ok {
		return v
	}
	v := fib(n-1) + fib(n-2)
	memo[n] = v
	return v
}

func main() {
	for i := 0; i < 7; i++ {
		fmt.Print(fib(i), " ")
	}
	fmt.Println()
}
