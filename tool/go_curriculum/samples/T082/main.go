// T082 context 一：取消与传播。
//
// context.WithCancel 派生一个可取消的上下文；调用 cancel() 会关闭 Done()
// 返回的 channel，所有监听它的下游任务据此提前退出。本示例启动一个循环
// 任务，取消后通过 channel 汇报"已退出"，主流程等待该信号，结果确定。
package main

import (
	"context"
	"fmt"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())

	done := make(chan struct{})
	go func() {
		// 任务循环：每次迭代检查是否被取消。
		for i := 0; ; i++ {
			select {
			case <-ctx.Done():
				// 被取消：报告原因并退出。
				fmt.Println("worker stopped:", ctx.Err())
				close(done)
				return
			default:
				// 正常继续（这里不做事，仅计数到某个点后自行取消）。
				if i == 3 {
					fmt.Println("worker reached checkpoint, requesting cancel")
					cancel()
				}
			}
		}
	}()

	// 等待 worker 确认退出。不依赖睡眠/时间，用 channel 做同步。
	<-done
	fmt.Println("main observed worker exit")

	// 传播：派生的子 context 也会随父取消而 Done。
	parent, pcancel := context.WithCancel(context.Background())
	child, ccancel := context.WithCancel(parent)
	pcancel()
	<-child.Done()
	fmt.Println("child canceled by parent:", child.Err())
	ccancel()
}
