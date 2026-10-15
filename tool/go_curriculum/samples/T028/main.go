package main

import "fmt"

func main() {
	defer fmt.Println("first deferred")
	defer fmt.Println("second deferred")
	fmt.Println("body")
	// 命名返回值与 defer 配合可修改返回值
	fmt.Println("result:", double(21))
}

func double(n int) (result int) {
	defer func() { result *= 2 }()
	return n
}
