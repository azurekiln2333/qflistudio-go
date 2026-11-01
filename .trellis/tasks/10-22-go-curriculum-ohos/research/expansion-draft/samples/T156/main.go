package main

import (
	"container/heap"
	"fmt"
)

type Edge struct {
	To   string
	Cost int
}
type State struct {
	Node     string
	Distance int
}
type Frontier []State

func (h Frontier) Len() int { return len(h) }
func (h Frontier) Less(i, j int) bool {
	if h[i].Distance != h[j].Distance {
		return h[i].Distance < h[j].Distance
	}
	return h[i].Node < h[j].Node
}
func (h Frontier) Swap(i, j int)           { h[i], h[j] = h[j], h[i] }
func (h *Frontier) Push(value interface{}) { *h = append(*h, value.(State)) }
func (h *Frontier) Pop() interface{} {
	old := *h
	value := old[len(old)-1]
	*h = old[:len(old)-1]
	return value
}
func shortest(graph map[string][]Edge, start, target string) (int, []string, int, error) {
	for _, edges := range graph {
		for _, edge := range edges {
			if edge.Cost < 0 {
				return 0, nil, 0, fmt.Errorf("negative edge")
			}
		}
	}
	distances := map[string]int{start: 0}
	parent := map[string]string{}
	queue := &Frontier{}
	heap.Push(queue, State{start, 0})
	stale := 0
	for queue.Len() > 0 {
		current := heap.Pop(queue).(State)
		if current.Distance != distances[current.Node] {
			stale++
			continue
		}
		for _, edge := range graph[current.Node] {
			candidate := current.Distance + edge.Cost
			old, exists := distances[edge.To]
			if !exists || candidate < old {
				distances[edge.To] = candidate
				parent[edge.To] = current.Node
				heap.Push(queue, State{edge.To, candidate})
			}
		}
	}
	distance, exists := distances[target]
	if !exists {
		return 0, nil, stale, fmt.Errorf("unreachable")
	}
	path := []string{}
	for node := target; node != ""; node = parent[node] {
		path = append(path, node)
	}
	for i, j := 0, len(path)-1; i < j; i, j = i+1, j-1 {
		path[i], path[j] = path[j], path[i]
	}
	return distance, path, stale, nil
}
func main() {
	graph := map[string][]Edge{"A": {{"B", 5}, {"C", 1}}, "C": {{"B", 2}, {"D", 8}}, "B": {{"D", 3}}}
	distance, path, stale, err := shortest(graph, "A", "D")
	if err != nil {
		panic(err)
	}
	fmt.Printf("distance=%d path=%v stale=%d\n", distance, path, stale)
	_, _, _, err = shortest(map[string][]Edge{"A": {{"B", -1}}}, "A", "B")
	fmt.Printf("negative-rejected=%t\n", err != nil)
}
