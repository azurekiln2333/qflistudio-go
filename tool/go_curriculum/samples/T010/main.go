package main

import "fmt"

func main() {
	a, b := 6, 4
	fmt.Println("add", a+b, "sub", a-b, "mul", a*b, "div", a/b, "mod", a%b)
	fmt.Println("and", a&b, "or", a|b, "xor", a^b, "shl", a<<1, "shr", a>>1)
	// 优先级：* / % 高于 + -，比较低于算术，&& 低于 ||
	fmt.Println("expr", 1+2*3 == 7 && 4%2 == 0)
}
