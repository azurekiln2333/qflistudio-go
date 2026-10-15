// T112 内存分配与逃逸分析。
//
// 编译器决定一个变量分配在栈还是堆上。若变量"逃逸"到函数外（被返回、
// 存入接口、被闭包长期捕获等），就分配到堆。用
//   go build -gcflags=-m
// 可查看逃逸报告。本示例给出可对比的两种写法。
//
// module-project 工程例子，不能一键导入。完整结构：
//   escapeanalyze/
//   ├── go.mod   // module escapeanalyze\n\ngo 1.27
//   └── main.go  // 本文件
// 运行（官方 SDK）：
//   go run .
//   go build -gcflags=-m .    // 查看逃逸报告
// desktop only。
package main

import "fmt"

// Point 是小的值类型。
type Point struct{ X, Y int }

// makeValue 按值返回：调用方拿到副本。
func makeValue() Point {
	p := Point{1, 2} // 可能留在栈上
	return p
}

// makePointer 返回指针：p 逃逸到堆。
func makePointer() *Point {
	p := Point{3, 4} // 逃逸：地址被返回
	return &p
}

// makeInterface 存入接口：通常逃逸（接口值在堆上）。
func makeInterface() any {
	p := Point{5, 6}
	return p
}

func main() {
	v := makeValue()
	fmt.Println("value:", v.X, v.Y)

	p := makePointer()
	fmt.Println("pointer:", p.X, p.Y)

	var a any = makeInterface()
	fmt.Println("interface:", a)

	fmt.Println("hint: `go build -gcflags=-m .` shows which variables escape to the heap")
}
