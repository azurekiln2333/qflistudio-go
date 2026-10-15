package main

import (
	"fmt"
	"sort"
)

func main() {
	words := []string{"go", "rust", "go", "c", "rust", "go"}
	seen := map[string]bool{}
	for _, w := range words {
		seen[w] = true
	}
	unique := make([]string, 0, len(seen))
	for w := range seen {
		unique = append(unique, w)
	}
	sort.Strings(unique)
	fmt.Println("unique", unique)

	groups := map[int][]string{}
	for _, w := range words {
		groups[len(w)] = append(groups[len(w)], w)
	}
	lens := make([]int, 0, len(groups))
	for k := range groups {
		lens = append(lens, k)
	}
	sort.Ints(lens)
	for _, k := range lens {
		fmt.Printf("len %d -> %d words\n", k, len(groups[k]))
	}
}
