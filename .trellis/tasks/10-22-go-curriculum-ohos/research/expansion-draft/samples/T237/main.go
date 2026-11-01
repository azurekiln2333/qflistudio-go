package main

import (
	"fmt"
	"sort"
	"sync"
)

func produce(values []int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for _, value := range values {
			out <- value
		}
	}()
	return out
}
func merge(inputs ...<-chan int) <-chan int {
	out := make(chan int)
	var workers sync.WaitGroup
	for _, input := range inputs {
		workers.Add(1)
		go func(input <-chan int) {
			defer workers.Done()
			for value := range input {
				out <- value
			}
		}(input)
	}
	go func() { workers.Wait(); close(out) }()
	return out
}
func main() {
	values := []int{}
	for value := range merge(produce([]int{1, 3}), produce([]int{2, 4})) {
		values = append(values, value)
	}
	sort.Ints(values)
	fmt.Printf("merged=%v\n", values)
}
