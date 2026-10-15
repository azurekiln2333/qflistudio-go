// T042 接口的动态类型与类型断言。
//
// 接口值内部保存“动态类型 + 动态值”。用类型断言 x.(T) 取出具体类型：
// 单返回值形式在失败时 panic，逗号-ok 形式安全返回零值与 false。
// 本示例演示两种断言与安全降级。
package main

import "fmt"

// Stringer 是一个简单接口。
type Stringer interface {
	String() string
}

// Name 实现了 Stringer。
type Name string

func (n Name) String() string { return string(n) }

// Number 也实现了 Stringer，便于在同一接口值上演示断言成功/失败。
type Number int

func (n Number) String() string { return fmt.Sprintf("#%d", int(n)) }

func main() {
	var s Stringer = Name("gopher")

	// 安全的逗号-ok 断言：成功时 ok 为 true。
	name, ok := s.(Name)
	fmt.Println("assert Name ok:", ok, "value:", name)

	// 失败断言：动态类型是 Name，断言为 Number 不成立，返回零值与 false。
	_, ok = s.(Number)
	fmt.Println("assert Number while type is Name:", ok)

	// 单返回值形式在失败时 panic；示例用 recover 演示其代价。
	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Println("single-value assert panicked:", r != nil)
			}
		}()
		_ = s.(Number) // 会 panic
	}()

	// 动态类型改赋为 Number；此时断言成功并取到值。
	s = Number(7)
	n, ok := s.(Number)
	fmt.Println("after reassign assert Number ok:", ok, "value:", int(n))

	// 对 any 的接口值断言为 string。
	var anyv any = "text"
	if str, ok := anyv.(string); ok {
		fmt.Println("any->string ok:", str)
	}
}
