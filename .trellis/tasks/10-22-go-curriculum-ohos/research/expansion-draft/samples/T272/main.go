package main

import (
	"container/heap"
	"fmt"
	"sort"
)

type Names []string

func (h Names) Len() int            { return len(h) }
func (h Names) Less(i, j int) bool  { return h[i] < h[j] }
func (h Names) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *Names) Push(v interface{}) { *h = append(*h, v.(string)) }
func (h *Names) Pop() interface{} {
	old := *h
	last := old[len(old)-1]
	*h = old[:len(old)-1]
	return last
}
func plan(deps map[string][]string) ([]string, []string) {
	degree := map[string]int{}
	next := map[string][]string{}
	for name, inputs := range deps {
		if _, ok := degree[name]; !ok {
			degree[name] = 0
		}
		for _, input := range inputs {
			degree[name]++
			if _, ok := degree[input]; !ok {
				degree[input] = 0
			}
			next[input] = append(next[input], name)
		}
	}
	ready := &Names{}
	heap.Init(ready)
	for name, n := range degree {
		if n == 0 {
			heap.Push(ready, name)
		}
	}
	order := []string{}
	for ready.Len() > 0 {
		name := heap.Pop(ready).(string)
		order = append(order, name)
		for _, dependent := range next[name] {
			degree[dependent]--
			if degree[dependent] == 0 {
				heap.Push(ready, dependent)
			}
		}
	}
	remaining := []string{}
	for name, n := range degree {
		if n > 0 {
			remaining = append(remaining, name)
		}
	}
	sort.Strings(remaining)
	return order, remaining
}
func main() {
	order, cycle := plan(map[string][]string{"parse": {}, "compile": {"parse"}, "test": {"compile"}, "link": {"compile"}})
	fmt.Printf("order=%v remaining=%v\n", order, cycle)
	_, cycle = plan(map[string][]string{"a": {"b"}, "b": {"a"}})
	fmt.Printf("cycle=%v\n", cycle)
}
