// T059 包、导出规则与初始化顺序。
//
// 包把代码分组；导出（大写）标识符可被其他包访问，小写仅包内可见。
// init 函数与包级变量初始化在包被导入时按依赖顺序自动执行。
//
// 完整多文件多包工程（module-project，不能一键导入）：
//   T059/
//   ├── go.mod              // module qfli.example/t059  (go 1.21)
//   ├── main.go             // 本文件：程序入口
//   ├── internal/config/config.go  // 包 config：包级变量 + init
//   └── internal/util/util.go      // 包 util：导出/非导出演示
//
// 运行（官方 SDK）：go run .
//
// 为在单文件内演示同一机制，这里用本包内的包级变量初始化与 init，
// 并注释说明真实的跨包结构。
package main

import "fmt"

// 包级变量按声明顺序初始化。
var a = 1
var b = a + 1 // 依赖 a

// exported 大写导出；unexported 小写仅本包可见。
const exported = "visible outside package"
const unexported = "visible only inside package"

// init 在 main 之前执行；多个 init 按文件/声明顺序执行。
func init() {
	fmt.Println("init: package config loaded, a =", a)
}

func main() {
	fmt.Println("a =", a, "b =", b)
	fmt.Println("exported:", exported)
	fmt.Println("unexported:", unexported)

	// 真实工程里，config 包的 init 会先于本 main 包执行（导入依赖顺序）。
	fmt.Println("init runs before main; across packages it follows import order")
}
