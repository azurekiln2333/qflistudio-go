// T063 泛型二：自定义约束与联合类型。
//
// 约束不仅能用一个现成的接口（如 cmp.Ordered），还能自己定义：
//   type Number interface { ~int | ~float64 }
// 其中 ~int 表示"底层类型是 int 的任意命名类型"，| 是类型并集。
// Sum 因此可以同时接受整数和浮点，且仍然保有编译期类型检查。
// 泛型 = desktop only（移动端 Yaegi 未实测）。
package main

import "fmt"

// Number 是一个自定义约束：允许底层类型为 int、int64 或 float64 的任意类型。
type Number interface {
	~int | ~int64 | ~float64
}

// Sum 把切片里所有元素相加。因为 T 满足 Number，可以直接用 + 运算。
func Sum[T Number](values []T) T {
	var total T // 零值：数值类型为 0
	for _, v := range values {
		total += v
	}
	return total
}

// Celsius 是一个"底层类型为 float64"的命名类型，它同样满足 Number，
// 这就是 ~ 的作用：不要求类型本身叫 float64，只要底层是 float64。
type Celsius float64

func main() {
	fmt.Println("Sum([]int{1,2,3}) =", Sum([]int{1, 2, 3}))
	fmt.Println("Sum([]int64{10,20,30}) =", Sum([]int64{10, 20, 30}))
	fmt.Println("Sum([]float64{1.5,2.5}) =", Sum([]float64{1.5, 2.5}))

	temps := []Celsius{20.5, 19.5, 21.0}
	fmt.Println("Sum([]Celsius{...}) =", Sum(temps))
}
