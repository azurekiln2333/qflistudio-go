// T106 断言与辅助函数、t.Helper。
//
// 把重复的断言逻辑抽成 helper，并在 helper 里调用 t.Helper()，
// 这样失败时报告的行号指向调用者而不是 helper 内部，定位更快。
//
// test-package 工程例子，不能一键导入。完整结构：
//   asserthlp/
//   ├── go.mod         // module asserthlp\n\ngo 1.27
//   └── assert_test.go // 本文件
// 运行：go test ./...   desktop only。
package asserthlp

import (
	"strconv"
	"testing"
)

// equalInt 是断言 helper：t.Helper() 让失败堆栈指向调用处。
func equalInt(t *testing.T, got, want int) {
	t.Helper()
	if got != want {
		t.Fatalf("got %d, want %d", got, want)
	}
}

// assertTrue 是布尔断言 helper，单独存在以免混用类型。
func assertTrue(t *testing.T, cond bool, msg string) {
	t.Helper()
	if !cond {
		t.Fatal(msg)
	}
}

// ParseLen 返回字符串长度（作为被测函数）。
func ParseLen(s string) int { return len(s) }

func TestParseLen(t *testing.T) {
	equalInt(t, ParseLen("go"), 2)
	equalInt(t, ParseLen(""), 0)

	// 用 helper 验证 strconv 往返，证明 helper 可复用。
	n, err := strconv.Atoi("123")
	assertTrue(t, err == nil, "Atoi error")
	equalInt(t, n, 123)
}
