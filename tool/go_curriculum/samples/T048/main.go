// T048 接口的 nil 陷阱与类型比较。
//
// 一个常见陷阱：接口值为 nil 与“接口里装了一个 nil 的具体指针”不是一回事。
// 本示例演示 typed-nil 陷阱：接口非 nil，但内部动态值为 nil，调用方法会 panic。
package main

import "fmt"

// Greeter 是接口。
type Greeter interface {
	Greet() string
}

// Person 实现 Greeter。
type Person struct{ Name string }

func (p *Person) Greet() string { return "hi " + p.Name }

func main() {
	// 情形一：真正的 nil 接口。
	var g Greeter
	fmt.Println("nil interface == nil:", g == nil)

	// 情形二：typed-nil 陷阱。把一个 nil 的 *Person 放进接口。
	var p *Person // p 是 nil
	g = p         // 接口非 nil，但动态类型是 *Person、动态值是 nil
	fmt.Println("typed-nil interface == nil:", g == nil) // 输出 false！

	// 调用会 panic，因为方法在 nil 接收者上解引用字段。
	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Println("calling method on typed-nil panicked:", r != nil)
			}
		}()
		_ = g.Greet()
	}()

	// 正确做法：用类型断言判断内部是否为 nil 指针。
	if pp, ok := g.(*Person); ok && pp == nil {
		fmt.Println("detected typed-nil via assertion")
	}

	// 有实际值时正常。
	g = &Person{Name: "gopher"}
	fmt.Println("real value:", g.Greet())
}
