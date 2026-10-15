package main

import "fmt"

func main() {
	counts := map[string]int{}
	for _, w := range []string{"go", "go", "rust", "go"} {
		counts[w]++
	}
	if v, ok := counts["go"]; ok {
		fmt.Println("go present:", v)
	}
	if _, ok := counts["java"]; !ok {
		fmt.Println("java absent")
	}
	delete(counts, "rust")
	fmt.Println("keys:", len(counts))
}
