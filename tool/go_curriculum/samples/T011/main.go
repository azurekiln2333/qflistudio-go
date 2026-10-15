package main

import "fmt"

func classify(score int) string {
	if v := score / 10; v >= 9 {
		return "A"
	} else if v >= 7 {
		return "B"
	} else {
		return "C"
	}
}

func main() {
	for _, s := range []int{95, 72, 50} {
		fmt.Printf("%d -> %s\n", s, classify(s))
	}
}
