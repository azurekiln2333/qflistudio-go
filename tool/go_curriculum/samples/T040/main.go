package main

import "fmt"

type rect struct{ w, h int }

func (r rect) area() int { return r.w * r.h }

func main() {
	r := rect{3, 4}
	// 方法值：绑定到具体接收者
	f := r.area
	fmt.Println("method value", f())
	// 方法表达式：接收者作为第一个参数
	g := rect.area
	fmt.Println("method expression", g(r))
	// 对指针的普通调用会自动取址
	p := &r
	fmt.Println("pointer call", p.area())
}
