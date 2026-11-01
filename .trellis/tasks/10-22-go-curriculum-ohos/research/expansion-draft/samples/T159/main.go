package main

import (
	"fmt"
	"sort"
)

type Groups struct{ Parent []int }

func (g *Groups) Find(id int) int {
	if g.Parent[id] != id {
		g.Parent[id] = g.Find(g.Parent[id])
	}
	return g.Parent[id]
}
func (g *Groups) Union(a, b int) {
	a = g.Find(a)
	b = g.Find(b)
	if a > b {
		a, b = b, a
	}
	g.Parent[b] = a
}
func main() {
	accounts := [][]string{{"a@local", "shared@local"}, {"b@local", "shared@local"}, {"c@local"}, {"d@local", "c@local"}}
	groups := &Groups{Parent: make([]int, len(accounts))}
	for i := range groups.Parent {
		groups.Parent[i] = i
	}
	owners := map[string]int{}
	for id, emails := range accounts {
		for _, email := range emails {
			if previous, exists := owners[email]; exists {
				groups.Union(id, previous)
			} else {
				owners[email] = id
			}
		}
	}
	buckets := map[int][]int{}
	for id := range accounts {
		root := groups.Find(id)
		buckets[root] = append(buckets[root], id+1)
	}
	roots := []int{}
	for root := range buckets {
		roots = append(roots, root)
	}
	sort.Ints(roots)
	for _, root := range roots {
		sort.Ints(buckets[root])
		fmt.Printf("group=%v\n", buckets[root])
	}
	fmt.Printf("shared=%t distinct=%t\n", groups.Find(0) == groups.Find(1), groups.Find(0) != groups.Find(2))
}
