// T049 error 接口与错误即值。
//
// Go 把错误当作普通值返回：函数返回 (T, error)，调用方必须显式检查。
// error 是一个接口：任何有 Error() string 的类型都能当错误。
package main

import "fmt"

// divide 在两个数相除时检查除零并返回错误。
func divide(a, b int) (int, error) {
	if b == 0 {
		return 0, fmt.Errorf("divide by zero")
	}
	return a / b, nil
}

func main() {
	// 成功：err 为 nil。
	q, err := divide(10, 2)
	fmt.Println("10/2 =", q, "err:", err)

	// 失败：检查 err 并降级处理，而不是忽略。
	q, err = divide(1, 0)
	if err != nil {
		fmt.Println("error:", err)
		fmt.Println("result unusable, defaulting to 0")
		q = 0
	}
	fmt.Println("value after error:", q)

	// 错误是值：可以存入变量、比较、传递。
	var lastErr error
	if _, e := divide(3, 0); e != nil {
		lastErr = e
	}
	fmt.Println("stored error text:", lastErr.Error())
}
