// T097 strconv 与数据解析。
//
// strconv 在字符串与基础类型之间转换：Atoi/Itoa、ParseFloat、
// ParseBool、Quote 等。解析失败会返回错误，必须处理。
// 本示例解析多种输入并打印结果，输出确定。
package main

import (
	"fmt"
	"strconv"
)

func main() {
	// 字符串 -> int。
	n, err := strconv.Atoi("42")
	fmt.Println("Atoi 42:", n, "err:", err)

	// 解析失败：err 非 nil，n 为零值。
	bad, err := strconv.Atoi("4x2")
	fmt.Println("Atoi 4x2:", bad, "err non-nil:", err != nil)

	// int -> 字符串。
	fmt.Println("Itoa 255:", strconv.Itoa(255))

	// 浮点解析（64 位）。
	f, _ := strconv.ParseFloat("3.140", 64)
	fmt.Println("ParseFloat:", f)

	// 布尔解析：接受 1/t/T/TRUE 等多种形式。
	b, _ := strconv.ParseBool("TRUE")
	fmt.Println("ParseBool TRUE:", b)

	// 进制转换：把十六进制字符串按 16 进制解析。
	h, _ := strconv.ParseInt("ff", 16, 64)
	fmt.Println("ParseInt ff base16:", h)

	// Quote 给字符串加引号并转义。
	fmt.Println("Quote:", strconv.Quote("a\tb"))
}
