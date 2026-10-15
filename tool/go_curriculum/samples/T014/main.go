package main

import "fmt"

func main() {
	sum := 0
	for i := 1; i <= 5; i++ {
		if i == 3 {
			continue
		}
		sum += i
	}
	fmt.Println("sum", sum)

	n := 0
	for n < 3 {
		n++
	}
	fmt.Println("n", n)

	count := 0
	for {
		count++
		if count >= 2 {
			break
		}
	}
	fmt.Println("count", count)
}
