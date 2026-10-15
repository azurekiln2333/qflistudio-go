// T076 单向 channel 与接口约束。
//
// 函数参数可以声明为只发 `chan<- T` 或只收 `<-chan T`，用类型系统表达
// "这个函数只应该发送/只应该接收"。它不能凭空创建方向，只能由双向 channel
// 隐式转换而来，因此起到文档与编译期约束的双重作用。
package main

import "fmt"

// producer 只能向 ch 发送，无法从中接收——编译器会阻止误用。
func producer(out chan<- int) {
	for i := 1; i <= 3; i++ {
		out <- i * i
	}
	close(out)
}

// consumer 只能从 ch 接收，无法发送。
func consumer(in <-chan int) int {
	sum := 0
	for v := range in {
		sum += v
	}
	return sum
}

func main() {
	// 双向 channel，分别以只发/只收的视角传给两个函数。
	ch := make(chan int, 3)
	producer(ch)
	fmt.Println("sum of squares 1..3 =", consumer(ch))

	// 只收 channel 也可直接用于 range；顺序由缓冲保证为 FIFO。
	nums := make(chan int, 3)
	nums <- 10
	nums <- 20
	nums <- 30
	close(nums)
	for v := range nums {
		fmt.Println("read:", v)
	}
}
