// T069 构建标签与多平台文件后缀。
//
// 用 //go:build 标签与 _GOOS 文件后缀在编译期选择平台相关实现。
//
// 完整多文件工程（module-project，不能一键导入）：
//   T069/
//   ├── go.mod            // module qfli.example/t069  (go 1.21)
//   ├── main.go           // 本文件：打印选中的实现
//   ├── impl_default.go   // //go:build !special
//   └── impl_special.go   // //go:build special
//
// 运行（官方 SDK）：
//   go run .              // 默认实现
//   go run -tags special .// special 实现
//
// 为了输出跨平台确定，这里只打印由构建标签选择的实现名，
// 不打印 runtime.GOOS/GOARCH（那会随平台变化）。
package main

import "fmt"

func main() {
	// implName 由构建标签在编译期决定来源于哪个文件：
	//   include -tags special 时来自 impl_special.go，否则来自 impl_default.go。
	fmt.Println("selected impl =", implName())
	fmt.Println("with -tags special impl =", specialImplName())
}
