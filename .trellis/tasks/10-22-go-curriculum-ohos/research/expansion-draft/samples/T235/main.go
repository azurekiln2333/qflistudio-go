package main

import (
	"context"
	"fmt"
	"sync"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	numbers := make(chan int)
	squares := make(chan int)
	var stages sync.WaitGroup
	stages.Add(2)
	go func() {
		defer stages.Done()
		defer close(numbers)
		for n := 1; ; n++ {
			select {
			case numbers <- n:
			case <-ctx.Done():
				return
			}
		}
	}()
	go func() {
		defer stages.Done()
		defer close(squares)
		for {
			select {
			case <-ctx.Done():
				return
			case n, ok := <-numbers:
				if !ok {
					return
				}
				select {
				case squares <- n * n:
				case <-ctx.Done():
					return
				}
			}
		}
	}()
	consumed := []int{}
	for len(consumed) < 3 {
		consumed = append(consumed, <-squares)
	}
	cancel()
	stages.Wait()
	fmt.Printf("consumed=%v\nstages-exited=true\n", consumed)
}
