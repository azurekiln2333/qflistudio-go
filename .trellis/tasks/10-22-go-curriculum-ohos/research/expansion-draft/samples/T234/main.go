package main

import (
	"fmt"
	"sort"
	"sync"
)

func main() {
	var mu sync.Mutex
	cond := sync.NewCond(&mu)
	ready := 0
	start := false
	results := make(chan int, 3)
	for id := 1; id <= 3; id++ {
		go func(id int) {
			mu.Lock()
			ready++
			cond.Broadcast()
			for !start {
				cond.Wait()
			}
			mu.Unlock()
			results <- id * 10
		}(id)
	}
	mu.Lock()
	for ready < 3 {
		cond.Wait()
	}
	start = true
	cond.Broadcast()
	mu.Unlock()
	values := []int{}
	for i := 0; i < 3; i++ {
		values = append(values, <-results)
	}
	sort.Ints(values)
	fmt.Printf("ready=%d\nresults=%v\n", ready, values)
}
