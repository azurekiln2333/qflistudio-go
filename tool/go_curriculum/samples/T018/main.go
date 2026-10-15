package main

import "fmt"

func main() {
	a := [3]int{1, 2, 3}
	b := a // 数组是值语义：整体拷贝
	b[0] = 99
	fmt.Println("a", a)
	fmt.Println("b", b)
	fmt.Println("len", len(a))
}
