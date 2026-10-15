// T058 错误集合并发安全的收集。
//
// 并行处理多个子任务时，需要并发安全地收集错误。
// errors.Join（Go 1.20+）把多个错误合并成一个，errors.Is/As 仍可遍历全部。
package main

import (
	"errors"
	"fmt"
	"sort"
	"sync"
)

// task 模拟一个可能失败的任务。
func task(id int, failIDs map[int]bool) error {
	if failIDs[id] {
		return fmt.Errorf("task %d failed", id)
	}
	return nil
}

// runAll 并发跑所有任务，用 Mutex 保护错误切片，返回聚合错误。
func runAll(ids []int, failIDs map[int]bool) error {
	var mu sync.Mutex
	var errs []error

	var wg sync.WaitGroup
	for _, id := range ids {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			if err := task(id, failIDs); err != nil {
				mu.Lock()
				errs = append(errs, err)
				mu.Unlock()
			}
		}(id)
	}
	wg.Wait()

	return errors.Join(errs...)
}

// multiUnwrapper 是 errors.Join 返回值实现的接口：可展开出多个错误。
type multiUnwrapper interface{ Unwrap() []error }

func main() {
	ids := []int{1, 2, 3, 4, 5}
	failIDs := map[int]bool{2: true, 4: true}

	err := runAll(ids, failIDs)
	if err != nil {
		// Join 的结果可通过 Unwrap() []error 展开成多个子错误。
		if mu, ok := err.(multiUnwrapper); ok {
			parts := make([]string, 0, len(mu.Unwrap()))
			for _, e := range mu.Unwrap() {
				parts = append(parts, e.Error())
			}
			// 并发完成顺序不定，排序以保证输出确定。
			sort.Strings(parts)
			fmt.Println("collected errors:", len(parts))
			for _, p := range parts {
				fmt.Println(" ", p)
			}
		}
	}

	// 无失败时返回 nil。
	fmt.Println("all-ok err is nil:", runAll(ids, map[int]bool{}) == nil)

	// 演示单个 error 的 Unwrap 对 Join 结果不可用（它返回 nil）。
	fmt.Println("single Unwrap(join) is nil:", errors.Unwrap(err) == nil)
}
