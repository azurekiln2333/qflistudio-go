// T075 select：多路复用与超时。
//
// select 同时等待多个 channel 操作，哪个先就绪就走哪个分支；
// 当所有分支都未就绪且写了 default，则立即走 default。
// 本示例用"已就绪的 channel"制造确定性的选择结果，
// 并用 time.After 演示超时分支，但断言只看"是否走到超时分支"，不看具体耗时。
package main

import (
	"fmt"
	"time"
)

func main() {
	ready := make(chan string, 1)
	ready <- "payload" // 预置，保证接收分支必然就绪

	// 只有一个分支就绪时，select 必然选择它，结果确定。
	select {
	case v := <-ready:
		fmt.Println("took ready channel:", v)
	default:
		fmt.Println("nothing ready")
	}

	// 演示超时分支：慢 channel 永远不发送，超时时间极短。
	// 我们断言"走了哪个分支"，不断言实际耗时。
	slow := make(chan int) // 无人发送
	select {
	case v := <-slow:
		fmt.Println("unexpected value:", v)
	case <-time.After(10 * time.Millisecond):
		fmt.Println("timeout branch taken")
	}

	// 两个 channel 都就绪时，Go 会随机选一个；因此这里不比较谁被选中，
	// 只断言"恰好取到一个值"，用集合语义消解随机性。
	a := make(chan int, 1)
	b := make(chan int, 1)
	a <- 1
	b <- 2
	select {
	case <-a:
		fmt.Println("selected exactly one ready channel")
	case <-b:
		fmt.Println("selected exactly one ready channel")
	}
}
