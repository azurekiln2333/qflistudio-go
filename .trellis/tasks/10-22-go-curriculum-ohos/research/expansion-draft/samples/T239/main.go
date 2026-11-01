package main

import (
	"context"
	"fmt"
)

type Request struct {
	Delta   int
	Reply   chan int
	Context context.Context
}

func main() {
	requests := make(chan Request)
	done := make(chan struct{})
	go func() {
		defer close(done)
		balance := 0
		for request := range requests {
			if request.Context.Err() != nil {
				continue
			}
			balance += request.Delta
			request.Reply <- balance
		}
	}()
	ask := func(ctx context.Context, delta int) (int, bool) {
		if ctx.Err() != nil {
			return 0, false
		}
		reply := make(chan int, 1)
		select {
		case requests <- Request{delta, reply, ctx}:
		case <-ctx.Done():
			return 0, false
		}
		select {
		case value := <-reply:
			return value, true
		case <-ctx.Done():
			return 0, false
		}
	}
	first, _ := ask(context.Background(), 5)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, accepted := ask(ctx, 100)
	last, _ := ask(context.Background(), 2)
	close(requests)
	<-done
	fmt.Printf("first=%d\ncancelled-accepted=%t\nfinal=%d\n", first, accepted, last)
}
