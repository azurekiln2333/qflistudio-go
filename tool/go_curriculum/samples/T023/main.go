package main

import "fmt"

func divmod(a, b int) (int, int) {
	return a / b, a % b
}

func split(sum int) (x, y int) {
	x = sum * 4 / 9
	y = sum - x
	return // 命名返回：裸 return
}

func main() {
	q, r := divmod(17, 5)
	fmt.Println("q,r", q, r)
	x, y := split(90)
	fmt.Println("split", x, y)
}
