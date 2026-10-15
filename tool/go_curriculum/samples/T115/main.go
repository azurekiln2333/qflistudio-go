// T115 静态检查与工程规范：vet 与 gofmt 基线。
//
// gofmt 统一格式（-l 列出不合规文件，-d 显示 diff）；
// go vet 检查可疑构造（如 Printf 参数不匹配、无用的锁拷贝）。
// 二者是标准库工具链自带的静态检查基线，不依赖第三方。
//
// single-file 示例：本文件本身可由 CodeSnippet 导入；同时用作
// `gofmt`/`go vet` 的检查对象。
//
// 运行（官方 SDK）：
//   gofmt -l .
//   go vet ./...
// desktop only（移动端不提供这些工具）。
package main

import "fmt"

func main() {
	// 正确格式：注意切片字面量对齐由 gofmt 统一。
	nums := []int{1, 2, 3}
	total := 0
	for _, n := range nums {
		total += n
	}
	fmt.Println("total:", total)

	// 演示 vet 会关注的正确写法：Printf 动词与参数类型匹配。
	name := "gopher"
	fmt.Printf("hello, %s (%d items)\n", name, len(nums))

	fmt.Println("run: `gofmt -l .` and `go vet ./...`")
}
