// T074 channel 三：close 与 range 接收。
//
// close(ch) 表示"不会再有值发送进来"。对已关闭的 channel，range 会在
// 缓冲区取空后自然结束，接收的第二个返回值 ok 会变为 false。
// 发送方关闭、接收方用 range，是 producer/consumer 的惯用收尾方式。
package main

import "fmt"

func main() {
	ch := make(chan int)

	// 生产者：发送 1..5 后关闭 channel，通知消费者结束。
	go func() {
		for i := 1; i <= 5; i++ {
			ch <- i
		}
		close(ch)
	}()

	// 消费者：range 会一直读到 channel 关闭且缓冲为空。
	sum := 0
	count := 0
	for v := range ch {
		sum += v
		count++
	}
	fmt.Println("count:", count)
	fmt.Println("sum:", sum)

	// 逗号-ok 形式：关闭后再接收不阻塞，直接返回零值与 false。
	v, ok := <-ch
	fmt.Println("after close: value =", v, "ok =", ok)
}
