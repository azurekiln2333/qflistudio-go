package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	gate := make(chan struct{}, 2)
	var workers sync.WaitGroup
	var active, peak, completed int32
	for i := 0; i < 6; i++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			gate <- struct{}{}
			current := atomic.AddInt32(&active, 1)
			for {
				old := atomic.LoadInt32(&peak)
				if current <= old || atomic.CompareAndSwapInt32(&peak, old, current) {
					break
				}
			}
			atomic.AddInt32(&completed, 1)
			atomic.AddInt32(&active, -1)
			<-gate
		}()
	}
	workers.Wait()
	fmt.Printf("completed=%d\npeak-bounded=%t\nactive=%d\n", completed, peak >= 1 && peak <= 2, active)
}
