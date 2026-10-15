// T080 sync.Pool 与临时对象复用。
//
// sync.Pool 缓存可复用对象，减少高频分配的压力。注意：Pool 中的对象可能被
// GC 随时回收，因此不能用于持久状态，只能当"临时缓冲池"。
//
// 这是一个 test-package / benchmark 工程例子，不能一键导入。完整结构：
//   poolbench/
//   ├── go.mod        // module poolbench\n\ngo 1.27
//   └── pool_test.go  // 本文件
// 运行（官方 SDK）：
//   go test ./...                      // 功能测试（确定性）
//   go test -bench . -benchmem ./...   // 只看分配指标，不作为通过条件
//
// 断言策略：功能测试用确定性"内容正确"断言；benchmark 只要求能跑出 ns/op。
// 移动端不支持 bench，desktop only。
package poolbench

import (
	"bytes"
	"sync"
	"testing"
)

var bufPool = sync.Pool{
	New: func() any { return new(bytes.Buffer) },
}

// render 用池中的 Buffer 组装字符串，用完重置并放回。
func render(parts []string) string {
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset()
	defer bufPool.Put(buf)
	for _, p := range parts {
		buf.WriteString(p)
	}
	return buf.String()
}

// renderNoPool 不使用池，每次新建 Buffer，作为对照。
func renderNoPool(parts []string) string {
	var buf bytes.Buffer
	for _, p := range parts {
		buf.WriteString(p)
	}
	return buf.String()
}

func TestRenderCorrect(t *testing.T) {
	parts := []string{"go", "-", "pool"}
	if got, want := render(parts), "go-pool"; got != want {
		t.Fatalf("render = %q, want %q", got, want)
	}
	// 复用一个池对象多次，结果必须仍然正确（证明 Reset 有效）。
	if got := render([]string{"a", "b"}); got != "ab" {
		t.Fatalf("second render = %q, want %q", got, "ab")
	}
}

func TestRenderNoPoolMatches(t *testing.T) {
	parts := []string{"x", "y", "z"}
	if render(parts) != renderNoPool(parts) {
		t.Fatal("pooled and unpooled results differ")
	}
}

func BenchmarkRenderPool(b *testing.B) {
	parts := []string{"go", "-", "pool", "-", "bench"}
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_ = render(parts)
	}
}

func BenchmarkRenderNoPool(b *testing.B) {
	parts := []string{"go", "-", "pool", "-", "bench"}
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_ = renderNoPool(parts)
	}
}
