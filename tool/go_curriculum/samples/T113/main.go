// T113 剖析：pprof CPU 与内存。
//
// runtime/pprof 可在程序内采集 CPU/内存剖面；更常用的是在测试里
// `go test -cpuprofile`/`-memprofile` 生成文件，再用 go tool pprof 分析。
// 本示例提供一段可被 profile 的热点函数，并打印如何采集。
//
// module-project 工程例子，不能一键导入。完整结构：
//   pprofdemo/
//   ├── go.mod              // module pprofdemo\n\ngo 1.27
//   ├── main.go             // 本文件
//   └── pprof_test.go       // 基准，供 -cpuprofile 采集
// 运行（官方 SDK）：
//   go test -bench . -cpuprofile=cpu.out .
//   go tool pprof cpu.out
// desktop only。
package main

import "fmt"

// hot 是一个 CPU 热点：反复做整数运算。
func hot(n int) int {
	total := 0
	for i := 0; i < n; i++ {
		total += i % 7
	}
	return total
}

func main() {
	// 运行热点并打印确定结果。
	fmt.Println("hot(1000) =", hot(1000))
	fmt.Println("profile with: go test -bench . -cpuprofile=cpu.out .")
	fmt.Println("then: go tool pprof cpu.out")
}
