// T073 channel 二：有缓冲与容量语义。
//
// 有缓冲 channel 在缓冲未满时发送不阻塞，缓冲为空时接收才阻塞。
// 本示例用容量为 2 的通道：前两次发送立即成功，第三次会在缓冲满时阻塞，
// 于是我们用一个带 default 的 select 探测"是否还能发送"，把非确定性
// 的阻塞转成一个确定的布尔结果。
package main

import "fmt"

func main() {
	ch := make(chan int, 2) // 容量 2

	// 前两次发送不会阻塞。
	ch <- 10
	ch <- 20
	fmt.Println("buffered:", len(ch), "cap:", cap(ch))

	// 第三次发送：缓冲已满。用 select+default 非阻塞探测，得到确定结果。
	sent := false
	select {
	case ch <- 30:
		sent = true
	default:
		sent = false
	}
	fmt.Println("third send succeeded:", sent)

	// 取走一个后，容量腾出，再次探测就能成功。
	first := <-ch
	fmt.Println("first out:", first)

	again := false
	select {
	case ch <- 30:
		again = true
	default:
		again = false
	}
	fmt.Println("send after one receive succeeded:", again)

	// 清空：按 FIFO 顺序取出剩余元素，顺序确定。
	fmt.Println("remaining:", <-ch, <-ch)
}
