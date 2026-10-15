package main

import "fmt"

func main() {
	var i8 int8 = 127
	var u8 uint8 = 255
	var f float64 = 3.5
	var b bool = true
	var s string = "go"
	fmt.Printf("%T=%v %T=%v %T=%v %T=%v %T=%q\n", i8, i8, u8, u8, f, f, b, b, s, s)
	// 类型推断：值决定默认类型。
	typed := 10
	fmt.Printf("typed 是 %T\n", typed)
}
