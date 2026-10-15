// T071 goroutine 基础与启动。
//
// 启动 goroutine 只需在调用前加 go。多个 goroutine 的完成顺序不确定，
// 因此本示例不打印"谁先谁后"，而是用 sync.WaitGroup 汇合后，
// 把各自写入的结果收集进切片，排序后再输出——保证输出确定。
package main

import (
	"fmt"
	"sort"
	"sync"
)

func main() {
	const n = 5
	results := make([]string, n)
	var wg sync.WaitGroup

	for i := 0; i < n; i++ {
		wg.Add(1)
		// i 作为参数传入，避免闭包共享同一个循环变量。
		go func(id int) {
			defer wg.Done()
			results[id] = fmt.Sprintf("worker-%d done", id)
		}(i)
	}

	// Wait 阻塞到所有 goroutine 调用 Done，保证 results 已全部写入。
	wg.Wait()

	// 排序消除 goroutine 完成顺序的不确定性，输出因此确定。
	sort.Strings(results)
	for _, r := range results {
		fmt.Println(r)
	}
}
