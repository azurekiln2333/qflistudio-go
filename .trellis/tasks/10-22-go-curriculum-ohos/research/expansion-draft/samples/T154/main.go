package main

import (
	"container/list"
	"fmt"
)

func route(graph map[string][]string, start, target string) []string {
	queue := list.New()
	queue.PushBack(start)
	parent := map[string]string{start: ""}
	for queue.Len() > 0 {
		element := queue.Front()
		at := element.Value.(string)
		queue.Remove(element)
		if at == target {
			path := []string{}
			for node := target; node != ""; node = parent[node] {
				path = append(path, node)
			}
			for left, right := 0, len(path)-1; left < right; left, right = left+1, right-1 {
				path[left], path[right] = path[right], path[left]
			}
			return path
		}
		for _, next := range graph[at] {
			if _, seen := parent[next]; !seen {
				parent[next] = at
				queue.PushBack(next)
			}
		}
	}
	return nil
}
func main() {
	graph := map[string][]string{"A": {"B", "C"}, "B": {"D"}, "C": {"D", "E"}, "D": {"F"}, "E": {"F"}, "F": {}}
	path := route(graph, "A", "F")
	fmt.Printf("path=%v hops=%d\n", path, len(path)-1)
	fmt.Printf("unreachable=%t same=%v\n", route(graph, "A", "Z") == nil, route(graph, "A", "A"))
}
