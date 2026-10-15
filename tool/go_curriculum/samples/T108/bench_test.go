// T108 基准测试与 b.RunParallel。
//
// 基准测试函数名形如 BenchmarkXxx(*testing.B)，b.N 由框架自动调整以获得
// 稳定测量。b.RunParallel 用多个 goroutine 并行施压，适合测量并发路径。
// 断言策略：只要求基准能运行并报出指标（ns/op），不把数值作为通过条件。
//
// test-package / benchmark 工程例子，不能一键导入。完整结构：
//   benchparallel/
//   ├── go.mod         // module benchparallel\n\ngo 1.27
//   └── bench_test.go  // 本文件
// 运行（官方 SDK）：
//   go test ./...
//   go test -bench . -benchmem ./...
// 移动端不支持 bench，desktop only。
package benchparallel

import (
	"sync/atomic"
	"testing"
)

// sumTo 是串行基准的被测逻辑。
func sumTo(n int) int {
	total := 0
	for i := 1; i <= n; i++ {
		total += i
	}
	return total
}

func BenchmarkSum(b *testing.B) {
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_ = sumTo(1000)
	}
}

func BenchmarkSumParallel(b *testing.B) {
	var counter atomic.Int64
	b.ReportAllocs()
	b.RunParallel(func(pb *testing.PB) {
		// 每个并行工作者拿到各自的一部分迭代。
		for pb.Next() {
			counter.Add(int64(sumTo(100)))
		}
	})
	// 消费 counter，避免被优化掉。
	if counter.Load() < 0 {
		b.Fatal("negative")
	}
}

func TestSumTo(t *testing.T) {
	if got := sumTo(10); got != 55 {
		t.Fatalf("sumTo(10) = %d, want 55", got)
	}
}
