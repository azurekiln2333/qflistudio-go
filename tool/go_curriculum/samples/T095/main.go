// T095 正则二：替换、分割与预编译复用。
//
// ReplaceAllStringFunc 允许用函数动态决定每个匹配的替换值；
// Split 用正则切分；预编译（MustCompile 到包级变量）避免重复编译。
// 本示例输出确定。
package main

import (
	"fmt"
	"regexp"
)

// 包级预编译：只编译一次，整个程序复用。
var (
	numberRe = regexp.MustCompile(`\d+`)
	spaceRe  = regexp.MustCompile(`\s+`)
)

func main() {
	src := "a1 b22 c333"

	// 条件替换：把每个数字 n 替换为 n*2 的字符串。
	doubled := numberRe.ReplaceAllStringFunc(src, func(m string) string {
		// m 一定是数字串，这里手工解析以避免引入 strconv 干扰阅读。
		n := 0
		for _, r := range m {
			n = n*10 + int(r-'0')
		}
		return fmt.Sprint(n * 2)
	})
	fmt.Println("doubled:", doubled)

	// 简单替换：把所有数字替换为 "#"。
	masked := numberRe.ReplaceAllString(src, "#")
	fmt.Println("masked: ", masked)

	// 用连续空白分割。
	parts := spaceRe.Split("one   two\tthree  four", -1)
	fmt.Println("split count:", len(parts))
	for i, p := range parts {
		fmt.Printf("  [%d]=%s\n", i, p)
	}
}
