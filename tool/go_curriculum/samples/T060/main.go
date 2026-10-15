// T060 Go Modules：go.mod 与依赖版本。
//
// go.mod 声明模块路径与 Go 版本，并记录依赖及版本；go.sum 记录校验和。
// 本例演示“本地替换（replace）”——在完全离线、无第三方依赖的前提下，
// 用 replace 指向同仓本地目录来演示模块依赖解析。
//
// 完整多模块工程（module-project，不能一键导入）：
//   T060/
//   ├── go.mod        // module qfli.example/t060; replace qfli.example/lib => ./lib
//   ├── main.go       // 本文件：导入 lib 包
//   └── lib/
//       ├── go.mod    // module qfli.example/lib  (go 1.21)
//       └── lib.go    // 提供 Greeting()
//
// 运行（官方 SDK，离线）：go run .
//
// 为在单文件内演示“模块版本/依赖”的解析结果，这里内联一个语义化版本比较，
// 并注明确切的 go.mod 结构与命令。
package main

import (
	"fmt"
	"strings"
)

// Version 是简化语义化版本。
type Version struct{ Major, Minor, Patch int }

func parse(s string) Version {
	s = strings.TrimPrefix(s, "v")
	var v Version
	fmt.Sscanf(s, "%d.%d.%d", &v.Major, &v.Minor, &v.Patch)
	return v
}

func compare(a, b Version) int {
	switch {
	case a.Major != b.Major:
		return a.Major - b.Major
	case a.Minor != b.Minor:
		return a.Minor - b.Minor
	default:
		return a.Patch - b.Patch
	}
}

func main() {
	// 模拟 replace + require 的解析：本地 replace 的模块版本仍按声明参与选择。
	require := []string{"v0.1.0", "v0.1.2", "v0.1.1"}
	best := parse(require[0])
	for _, r := range require[1:] {
		if v := parse(r); compare(v, best) > 0 {
			best = v
		}
	}
	fmt.Printf("selected local module version: v%d.%d.%d\n", best.Major, best.Minor, best.Patch)

	fmt.Println("go.mod:")
	fmt.Println("  module qfli.example/t060")
	fmt.Println("  go 1.21")
	fmt.Println("  require qfli.example/lib v0.1.2")
	fmt.Println("  replace qfli.example/lib => ./lib")
	fmt.Println("run: go run .  (no network; resolved via local replace)")
}
