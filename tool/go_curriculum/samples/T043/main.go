// T043 空接口、any 与类型 switch。
//
// any（即 interface{}）能装任何值。用类型 switch 可以在一个 switch 里
// 按动态类型分发处理，是处理异构集合的常用手段。
package main

import "fmt"

// classify 用类型 switch 对任意值分类，返回可读描述。
func classify(v any) string {
	switch x := v.(type) {
	case nil:
		return "nil"
	case int:
		return fmt.Sprintf("int=%d", x)
	case float64:
		return fmt.Sprintf("float64=%.1f", x)
	case string:
		return fmt.Sprintf("string=%q len=%d", x, len(x))
	case bool:
		return fmt.Sprintf("bool=%t", x)
	case []int:
		return fmt.Sprintf("[]int len=%d", len(x))
	default:
		return fmt.Sprintf("other(%T)", x)
	}
}

func main() {
	// 异构集合：混合类型放进同一个 []any。
	values := []any{nil, 1, 2.5, "go", true, []int{1, 2, 3}, struct{ X int }{X: 9}}

	counts := map[string]int{}
	for _, v := range values {
		desc := classify(v)
		fmt.Println(desc)
		// 按类型名统计，演示对类型 switch 结果的再处理。
		switch v.(type) {
		case int:
			counts["int"]++
		case string:
			counts["string"]++
		default:
			counts["other"]++
		}
	}
	fmt.Println("int count:", counts["int"], "string count:", counts["string"], "other:", counts["other"])
}
