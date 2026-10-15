// T093 时间二：定时器、Ticker 与单调时钟。
//
// time.Timer 触发一次；time.Ticker 周期性触发。二者都基于单调时钟，
// 不受系统墙钟调整影响。本示例只断言"触发的次数"，不比较实际耗时，
// 因此输出确定、可离线验证。
package main

import (
	"fmt"
	"time"
)

func main() {
	// Timer：一次性。等待其通道被触发。
	timer := time.NewTimer(1 * time.Millisecond)
	<-timer.C
	fmt.Println("timer fired once")

	// Ticker：周期性。计数到 3 次后停止。
	ticker := time.NewTicker(1 * time.Millisecond)
	defer ticker.Stop()

	count := 0
	for range ticker.C {
		count++
		if count == 3 {
			break
		}
	}
	fmt.Println("ticker fired count:", count)

	// 停止后的 Ticker 不再触发（用 select+default 非阻塞探测，结果确定）。
	ticker.Stop()
	select {
	case <-ticker.C:
		fmt.Println("unexpected tick after stop")
	default:
		fmt.Println("no tick after stop")
	}

	// 演示 Now 的单调性：两次调用取差值为正（不断言具体数值）。
	start := time.Now()
	elapsed := time.Since(start)
	fmt.Println("elapsed is non-negative:", elapsed >= 0)
}
