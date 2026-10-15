// T084 并发模式：worker pool 与 errgroup 式编排。
//
// 用固定数量的 worker 从任务 channel 取活、把结果写入结果 channel，
// 是经典的 worker pool。本示例不引入第三方 errgroup，而是用标准库
// WaitGroup + error channel 实现等价"并行执行并在有错时返回"的编排。
// 结果收集后排序输出，保证确定性。
package main

import (
	"errors"
	"fmt"
	"sort"
	"sync"
)

func main() {
	jobs := make([]int, 20)
	for i := range jobs {
		jobs[i] = i + 1
	}

	results, err := runPool(jobs, 4, func(n int) (int, error) {
		if n == 13 {
			return 0, errors.New("unlucky 13")
		}
		return n * n, nil
	})
	if err != nil {
		fmt.Println("pool error:", err)
	}

	// 排序后输出，消除 worker 完成顺序的不确定性。
	sort.Ints(results)
	fmt.Println("squares (sorted):", results)
}

// runPool 用 workers 个 goroutine 处理 jobs，返回排序无关的成功结果切片。
// 语义上等价于 errgroup：任一任务出错即记录；这里采用"收集首个错误"策略。
func runPool(jobs []int, workers int, fn func(int) (int, error)) ([]int, error) {
	in := make(chan int)
	out := make(chan int)
	errCh := make(chan error, 1)

	var wg sync.WaitGroup
	wg.Add(workers)
	for w := 0; w < workers; w++ {
		go func() {
			defer wg.Done()
			for n := range in {
				v, err := fn(n)
				if err != nil {
					select {
					case errCh <- err: // 只记录第一个错误
					default:
					}
					continue
				}
				out <- v
			}
		}()
	}

	// 喂任务。
	go func() {
		for _, n := range jobs {
			in <- n
		}
		close(in)
	}()

	// 收结果。
	var results []int
	collectDone := make(chan struct{})
	go func() {
		for v := range out {
			results = append(results, v)
		}
		close(collectDone)
	}()

	wg.Wait()
	close(out)
	<-collectDone

	select {
	case err := <-errCh:
		return results, err
	default:
		return results, nil
	}
}
