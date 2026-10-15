// T083 context 二：超时与截止时间。
//
// WithTimeout 在指定时长后自动取消，超时后 ctx.Err() 返回
// context.DeadlineExceeded。本示例只断言「超时是否发生」这类语义结果，
// 不让任何分支依赖墙钟或调度竞速：慢任务用永不就绪的 channel 等待超时，
// 快/未取消路径用一个不会被取消的 context 顺序验证。
package main

import (
	"context"
	"errors"
	"fmt"
)

func main() {
	// 场景一：任务永不完成 -> 一定超时。选择超时分支是确定性的。
	slowCtx, slowCancel := context.WithTimeout(context.Background(), 1)
	defer slowCancel()
	select {
	case <-neverReady():
		fmt.Println("slow: task finished")
	case <-slowCtx.Done():
		fmt.Println("slow: deadline exceeded =", errors.Is(slowCtx.Err(), context.DeadlineExceeded))
	}

	// 场景二：未取消的 context -> 顺序返回结果，不依赖时间竞速。
	okCtx, okCancel := context.WithCancel(context.Background())
	defer okCancel()
	result, err := doWork(okCtx)
	fmt.Println("ok: result =", result, "err =", err)

	// 场景三：显式取消后立即返回 context.Canceled。
	canceledCtx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err = doWork(canceledCtx)
	fmt.Println("canceled: err is context canceled =", errors.Is(err, context.Canceled))
}

// doWork 在 ctx 已取消时返回错误，否则顺序返回结果。
func doWork(ctx context.Context) (int, error) {
	select {
	case <-ctx.Done():
		return 0, ctx.Err()
	default:
		return 42, nil
	}
}

// neverReady 返回一个永不就绪的 channel，用于确定性地触发超时分支。
func neverReady() <-chan struct{} { return make(chan struct{}) }
