// 导入后本文件默认为 src/snippet_test.go，同包辅助源码一并保存。
// T105 表驱动测试与子测试。
//
// 表驱动测试把多组输入/期望写进一个切片，循环用 t.Run 建成子测试。
// 这样新增用例只需加一行数据，且每个子测试可单独运行、单独报错。
//
// test-package 工程例子，导入时附带辅助文件。原始结构：
//   tabletest/
//   ├── go.mod       // module tabletest\n\ngo 1.27
//   └── calc_test.go // 本文件（含被测逻辑与测试）
// 运行：go test ./...   /   go test -run TestAdd ./...
// 选中测试入口执行断言，或使用桌面官方工具链 go test。
package tabletest

import "testing"

// Add 是被测函数。
func Add(a, b int) int { return a + b }

func TestAdd(t *testing.T) {
	cases := []struct {
		name string
		a, b int
		want int
	}{
		{"positive", 2, 3, 5},
		{"with zero", 0, 7, 7},
		{"negative", -2, -3, -5},
		{"mixed", -4, 4, 0},
	}
	for _, c := range cases {
		// t.Run 为每组数据建立独立子测试，名字唯一。
		t.Run(c.name, func(t *testing.T) {
			if got := Add(c.a, c.b); got != c.want {
				t.Fatalf("Add(%d,%d) = %d, want %d", c.a, c.b, got, c.want)
			}
		})
	}
}
