// T065 泛型与接口的选型对比。
//
// 同一道题——"对一组元素求和"——用两种方式实现：
//   1) 泛型函数 SumGeneric[T]：编译期特化，无装箱、无断言，但约束必须能表达运算。
//   2) 接口 summable：运行期多态，能容纳异构实现，但有类型断言/装箱开销。
// 运行结果相同；差别在"类型安全与性能"和"扩展性"之间的取舍。
// 泛型 = desktop only（移动端 Yaegi 未实测）。
package main

import "fmt"

// —— 方案一：泛型 ——
type Number interface{ ~int | ~float64 }

func SumGeneric[T Number](xs []T) T {
	var total T
	for _, x := range xs {
		total += x
	}
	return total
}

// —— 方案二：接口 ——
// Summable 是任何能自报数值的类型的接口。
type Summable interface {
	Value() float64
}

// SumInterface 通过接口方法求和，返回 float64。
func SumInterface(xs []Summable) float64 {
	var total float64
	for _, x := range xs {
		total += x.Value()
	}
	return total
}

// Money 是一个实现了 Summable 的具体类型。
type Money float64

func (m Money) Value() float64 { return float64(m) }

func main() {
	nums := []int{1, 2, 3, 4}
	fmt.Println("generic Sum[int] =", SumGeneric(nums))
	fmt.Println("generic Sum[float64] =", SumGeneric([]float64{1.5, 2.5}))

	sums := []Summable{Money(1.5), Money(2.5), Money(3.0)}
	fmt.Println("interface sum =", SumInterface(sums))
}
