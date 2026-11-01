package main

import (
	"fmt"
	"sort"
)

func cycle(graph map[string][]string) []string {
	colors := map[string]int{}
	positions := map[string]int{}
	stack := []string{}
	result := []string{}
	nodes := map[string]bool{}
	for node, next := range graph {
		nodes[node] = true
		for _, name := range next {
			nodes[name] = true
		}
	}
	keys := []string{}
	for node := range nodes {
		keys = append(keys, node)
	}
	sort.Strings(keys)
	var visit func(string) bool
	visit = func(node string) bool {
		colors[node] = 1
		positions[node] = len(stack)
		stack = append(stack, node)
		neighbors := append([]string(nil), graph[node]...)
		sort.Strings(neighbors)
		for _, next := range neighbors {
			if colors[next] == 1 {
				result = append([]string(nil), stack[positions[next]:]...)
				result = append(result, next)
				return true
			}
			if colors[next] == 0 && visit(next) {
				return true
			}
		}
		stack = stack[:len(stack)-1]
		delete(positions, node)
		colors[node] = 2
		return false
	}
	for _, node := range keys {
		if colors[node] == 0 && visit(node) {
			return result
		}
	}
	return nil
}
func main() {
	fmt.Printf("cycle=%v\n", cycle(map[string][]string{"app": {"db"}, "db": {"cache"}, "cache": {"app"}}))
	fmt.Printf("acyclic=%t\n", cycle(map[string][]string{"build": {"parse"}, "parse": {"scan"}, "scan": {}}) == nil)
}
