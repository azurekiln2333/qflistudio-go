// T061 internal 包与可见性：演示 Go 如何用 internal 目录限制包被外部导入。
//
// 本文件本身是可直接 `go run` 的单文件程序；它演示 internal 规则时，
// 同时说明一个完整的多文件工程结构（见教程文本）：
//
//	module demo
//	├── main.go            // 导入 demo/internal/secret（合法：同一 module 内）
//	├── internal/secret/secret.go   // 包 secret，只有 demo 模块内可导入
//	└── external/main.go    // 若放在另一个 module，导入 internal 会被编译器拒绝
//
// 这里我们只保留 main 程序，用一段注释与可运行逻辑说明可见性规则：
// 大写标识符导出，小写不导出；internal 目录进一步把包限制在模块内。
package main

import "fmt"

// Exported 以大写字母开头，导出到本包之外可见。
const Exported = "visible outside package"

// unexported 以小写字母开头，仅本包内可见。
const unexported = "visible only inside package"

func main() {
	fmt.Println("exported constant:", Exported)
	fmt.Println("unexported constant:", unexported)

	// 在同一文件内可以访问 unexported；若把这一行放进另一个包，编译会失败：
	//   ./other/main.go: undefined: main.unexported
	fmt.Println("internal rule: a package under an internal/ directory may only")
	fmt.Println("be imported by code in the directory tree rooted at internal's parent.")
}
