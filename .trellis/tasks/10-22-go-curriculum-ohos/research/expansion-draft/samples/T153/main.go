package main

import (
	"container/heap"
	"fmt"
	"sort"
)

type Order struct {
	ID     string
	Amount int
}
type Orders []Order

func (h Orders) Len() int { return len(h) }
func (h Orders) Less(i, j int) bool {
	if h[i].Amount != h[j].Amount {
		return h[i].Amount < h[j].Amount
	}
	return h[i].ID > h[j].ID
}
func (h Orders) Swap(i, j int)           { h[i], h[j] = h[j], h[i] }
func (h *Orders) Push(value interface{}) { *h = append(*h, value.(Order)) }
func (h *Orders) Pop() interface{} {
	old := *h
	value := old[len(old)-1]
	*h = old[:len(old)-1]
	return value
}
func main() {
	best := &Orders{}
	for _, order := range []Order{{"A", 40}, {"B", 10}, {"C", 50}, {"D", 50}, {"E", 30}, {"F", 60}} {
		if best.Len() < 3 {
			heap.Push(best, order)
			continue
		}
		worst := (*best)[0]
		if order.Amount > worst.Amount || (order.Amount == worst.Amount && order.ID < worst.ID) {
			(*best)[0] = order
			heap.Fix(best, 0)
		}
	}
	result := append([]Order(nil), (*best)...)
	sort.Slice(result, func(i, j int) bool {
		if result[i].Amount != result[j].Amount {
			return result[i].Amount > result[j].Amount
		}
		return result[i].ID < result[j].ID
	})
	fmt.Printf("kept=%d\n", len(result))
	for _, order := range result {
		fmt.Printf("%s=%d\n", order.ID, order.Amount)
	}
}
