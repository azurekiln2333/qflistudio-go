// T054 panic 与 recover：边界与代价。
//
// panic 表示不可继续的程序错误；recover 只能在 defer 中调用，用于兜底。
// 惯例：库函数用 error，不使用 panic；recover 一般只用在进程/请求边界。
package main

import "fmt"

// safeDivide 用 recover 把除零 panic 转成 error（边界兜底）。
func safeDivide(a, b int) (result int, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("recovered: %v", r)
		}
	}()
	return a / b, nil // b==0 时 panics，被上面 recover 捕获
}

// mustPositive panics 表示违反前提（不可恢复）。
func mustPositive(n int) int {
	if n <= 0 {
		panic("n must be positive")
	}
	return n
}

func main() {
	// 正常路径。
	r, err := safeDivide(10, 2)
	fmt.Println("10/2:", r, "err:", err)

	// 除零被 recover 转成 error，程序继续运行。
	r, err = safeDivide(1, 0)
	fmt.Println("1/0 ->", r, "err:", err)

	// 直接 panic 且不 recover 会终止程序；示例用 recover 演示其可被捕获。
	func() {
		defer func() {
			fmt.Println("caught panic:", recover())
		}()
		mustPositive(0)
	}()

	fmt.Println("program continues after recovered panic")
}
