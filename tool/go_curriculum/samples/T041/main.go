// T041 接口基础与鸭子类型。
//
// Go 的接口是“方法集合”：任何类型只要实现了接口要求的全部方法，就自动满足
// 该接口——无需显式声明 implements。这叫结构化类型 / 鸭子类型。
// 本示例定义 Shape 接口，让 Circle 与 Rectangle 各自实现，再统一调用。
package main

import (
	"fmt"
	"math"
)

// Shape 是接口：任何能给出面积与周长的类型都算 Shape。
type Shape interface {
	Area() float64
	Perimeter() float64
}

// Circle 实现 Shape。
type Circle struct{ R float64 }

func (c Circle) Area() float64      { return math.Pi * c.R * c.R }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.R }

// Rectangle 也实现 Shape。
type Rectangle struct{ W, H float64 }

func (r Rectangle) Area() float64      { return r.W * r.H }
func (r Rectangle) Perimeter() float64 { return 2 * (r.W + r.H) }

// describe 只依赖 Shape 接口，不关心具体类型。
func describe(s Shape) string {
	return fmt.Sprintf("area=%.2f perimeter=%.2f", s.Area(), s.Perimeter())
}

func main() {
	// 隐式满足：Circle 与 Rectangle 都没有写 "implements Shape"。
	shapes := []Shape{Circle{R: 1}, Rectangle{W: 2, H: 3}}
	for i, s := range shapes {
		fmt.Printf("shape %d: %s\n", i, describe(s))
	}

	// 接口值可以为 nil；对 nil 接口调用方法会 panic，注意判空。
	var s Shape
	fmt.Println("nil interface is nil:", s == nil)
}
