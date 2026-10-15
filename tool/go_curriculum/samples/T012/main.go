package main

import "fmt"

func bucket(n int) string {
	switch {
	case n < 0:
		return "negative"
	case n == 0:
		return "zero"
	case n < 10:
		return "small"
	default:
		return "large"
	}
}

func main() {
	for _, n := range []int{-1, 0, 5, 99} {
		fmt.Printf("%d=%s\n", n, bucket(n))
	}
}
