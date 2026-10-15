// T062 泛型一：类型参数与约束。
//
// Min/Max 在没有泛型时要为每种类型各写一份（或在 interface{} 上做断言），
// 泛型用 [T cmp.Ordered] 表达"T 必须可比较大小"，一份代码服务多种类型。
// 注意：泛型属于 Go 1.18+ 的静态编译特性，本项目的移动端 Yaegi 解释器
// 未实测支持，因此本主题标记为 desktop only。
package main

import (
	"cmp"
	"fmt"
)

// Min 返回 a、b 中较小者。T 被约束为 cmp.Ordered，
// 因此可以在函数体内直接使用 < 比较。
func Min[T cmp.Ordered](a, b T) T {
	if a < b {
		return a
	}
	return b
}

// Max 同理返回较大者。编译器会为每个实际类型参数实例化一份机器码。
func Max[T cmp.Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}

func main() {
	fmt.Println("Min[int](3, 7) =", Min(3, 7))
	fmt.Println("Max[int](3, 7) =", Max(3, 7))

	// 字符串也满足 cmp.Ordered（按字典序比较）。
	fmt.Println("Min[string](\"pear\", \"apple\") =", Min("pear", "apple"))

	// 浮点同样适用；没有为 float64 再写一份代码。
	fmt.Println("Max[float64](2.5, 1.5) =", Max(2.5, 1.5))
}
