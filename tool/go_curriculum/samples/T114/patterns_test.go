// T114 性能优化范式：预分配、批处理、零拷贝。
//
// 常见优化：用预分配切片（make([]T, 0, n)）避免反复扩容；
// 用 strings.Builder 拼接避免多次分配；用复用缓冲避免重复分配。
// 断言策略：功能等价断言（输出正确）+ 基准只作参考，不作通过条件。
//
// test-package / benchmark 工程例子，不能一键导入。完整结构：
//   perfpatterns/
//   ├── go.mod           // module perfpatterns\n\ngo 1.27
//   └── patterns_test.go // 本文件
// 运行（官方 SDK）：
//   go test ./...
//   go test -bench . -benchmem ./...
// desktop only。
package perfpatterns

import (
	"strings"
	"testing"
)

// appendNoPrealloc 不预分配，靠 append 扩容。
func appendNoPrealloc(n int) []int {
	var s []int
	for i := 0; i < n; i++ {
		s = append(s, i)
	}
	return s
}

// appendPrealloc 预分配容量，减少扩容次数。
func appendPrealloc(n int) []int {
	s := make([]int, 0, n)
	for i := 0; i < n; i++ {
		s = append(s, i)
	}
	return s
}

// joinConcat 用 + 拼接。
func joinConcat(parts []string) string {
	out := ""
	for _, p := range parts {
		out += p
	}
	return out
}

// joinBuilder 用 strings.Builder 拼接。
func joinBuilder(parts []string) string {
	var b strings.Builder
	for _, p := range parts {
		b.WriteString(p)
	}
	return b.String()
}

func TestEquivalence(t *testing.T) {
	a := appendNoPrealloc(10)
	b := appendPrealloc(10)
	if len(a) != len(b) {
		t.Fatalf("lengths differ: %d vs %d", len(a), len(b))
	}
	for i := range a {
		if a[i] != b[i] {
			t.Fatalf("element %d differs", i)
		}
	}
	parts := []string{"a", "b", "c"}
	if joinConcat(parts) != joinBuilder(parts) {
		t.Fatal("join results differ")
	}
}

func BenchmarkAppendNoPrealloc(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_ = appendNoPrealloc(256)
	}
}

func BenchmarkAppendPrealloc(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_ = appendPrealloc(256)
	}
}
