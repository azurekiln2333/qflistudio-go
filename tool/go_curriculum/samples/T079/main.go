// T079 sync.WaitGroup 与一次性任务 sync.Once。
//
// WaitGroup 用于等待一组 goroutine 完成；Once 保证某个初始化"在并发下也只
// 执行一次"。本示例用一次受 Once 保护的初始化 + 多 goroutine 并发调用，
// 断言初始化恰好发生一次，并用 WaitGroup 汇合。
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	var once sync.Once
	var initCount int32 // 用原子计数，证明初始化只跑了一次

	initResource := func() {
		atomic.AddInt32(&initCount, 1)
	}

	// 多个 goroutine 同时请求初始化。
	const n = 8
	var wg sync.WaitGroup
	values := make([]int, n)
	wg.Add(n)
	for i := 0; i < n; i++ {
		go func(id int) {
			defer wg.Done()
			once.Do(initResource) // 只有第一个到达的 goroutine 会执行
			values[id] = id * id
		}(i)
	}
	wg.Wait()

	fmt.Println("init executed count:", atomic.LoadInt32(&initCount))
	fmt.Println("all goroutines finished:", len(values) == n)
	fmt.Println("sum of squares:", sum(values))
}

func sum(xs []int) int {
	t := 0
	for _, x := range xs {
		t += x
	}
	return t
}
