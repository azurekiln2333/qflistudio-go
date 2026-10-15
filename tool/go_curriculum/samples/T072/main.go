// T072 channel 一：无缓冲与同步通信。
//
// 无缓冲 channel 的发送与接收会"互相等待"，因此天然是一次同步交接：
// 发送方阻塞直到有人接收，接收方阻塞直到有人发送。本示例用一个无缓冲
// channel 把值从 goroutine 交接给 main，顺序天然确定。
package main

import "fmt"

func main() {
	ch := make(chan string) // 无缓冲

	// 生产者 goroutine：发送后阻塞，直到 main 接收。
	go func() {
		ch <- "handoff payload"
	}()

	// 主 goroutine 接收，完成同步交接。
	got := <-ch
	fmt.Println("received:", got)

	// 再来一次，演示"先接收后发送"同样能配对。
	ch2 := make(chan int)
	go func() {
		ch2 <- 42
	}()
	fmt.Println("received:", <-ch2)
}
