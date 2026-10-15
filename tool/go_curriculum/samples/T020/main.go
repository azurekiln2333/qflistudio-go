package main

import "fmt"

func main() {
	base := []int{1, 2, 3, 4, 5}
	view := base[1:3] // 与 base 共享底层数组
	view[0] = 99
	fmt.Println("base", base)
	fmt.Println("view", view)

	appended := append(view, 100) // 容量足够时写回共享数组
	fmt.Println("appended", appended)
	fmt.Println("base after append", base)
}
