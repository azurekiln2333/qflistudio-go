package main

import "fmt"

func main() {
	var i int = 3
	var f float64 = float64(i) // 显式转换
	big := int64(1 << 40)
	small := int32(big) // 截断，保留低位
	fmt.Println(i, f)
	fmt.Printf("big=%d small=%d\n", big, small)
	// 浮点到整数会丢弃小数部分（向零取整）；常量 3.9 不能直接转 int，
	// 必须先放进 float64 变量再转换。
	var x float64 = 3.9
	fmt.Printf("trunc(3.9)=%d\n", int(x))
}
