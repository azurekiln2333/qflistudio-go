// T070 代码生成与 go:generate 边界。
//
// go:generate 是注释里的约定指令：运行 `go generate` 时执行其中的命令来生成源码。
// 它不是 go build 的一部分，必须显式运行；移动端 Yaegi 也不执行它。
//
// 本例是一个完整的多文件工程（module-project，不能一键导入）：
//   T070/
//   ├── go.mod            // module qfli.example/t070  (go 1.21)
//   ├── day.go            // type Day + 常量枚举
//   ├── day_string.go     // 本文件：由生成器产出/维护的 String() 与名字表
//   ├── gen_main.go       // 一个本地生成器（//go:build ignore），不参与常规构建
//   └── main.go           // 使用方
//
// 运行（官方 SDK）：
//   go run .            // 使用现成的 day_string.go
//   go generate ./...   // 重新运行 day.go 顶部 //go:generate 指定的生成器
//                       // 生成器写回 day_string.go（内容与现有一致）
//
// 说明：day_string.go 是“生成物”，这里同样提交进仓库，因为它必须随源码可用。
package main

import "fmt"

func main() {
	// 有了 String()，打印 Day 得到名字而不是数字。
	fmt.Println("Monday  =>", Monday)
	fmt.Println("Tuesday =>", Tuesday)

	// 越界值走回退分支。
	out := Day(99)
	fmt.Println("Day(99) =>", out)

	fmt.Println("note: `go generate ./...` reruns the generator for day_string.go;")
	fmt.Println("      it is not part of `go build` and is desktop only here.")
}
