// T081 原子操作 sync/atomic。
//
// 对于简单的计数/标志，atomic 提供无锁的原子读改写，避免锁开销。
// 本示例用 atomic.Int64 在多个 goroutine 中并发自增，最终值确定。
//
// test-package 工程例子，不能一键导入。完整结构：
//   atomiccount/
//   ├── go.mod          // module atomiccount\n\ngo 1.27
//   └── atomic_test.go  // 本文件
// 运行：go test ./...  /  go test -race ./...
// 移动端 Yaegi 对 sync/atomic 未实测，desktop only。
package atomiccount

import (
	"sync"
	"sync/atomic"
	"testing"
)

// Counter 用原子量计数。
type Counter struct{ n atomic.Int64 }

// Inc 原子自增。
func (c *Counter) Inc() { c.n.Add(1) }

// Value 原子读取。
func (c *Counter) Value() int64 { return c.n.Load() }

func TestAtomicConcurrentIncrement(t *testing.T) {
	const goroutines = 64
	const per = 1000
	const want = goroutines * per

	var c Counter
	var wg sync.WaitGroup
	wg.Add(goroutines)
	for i := 0; i < goroutines; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < per; j++ {
				c.Inc()
			}
		}()
	}
	wg.Wait()

	// 确定性断言：无锁自增也必须得到精确的总数。
	if got := c.Value(); got != want {
		t.Fatalf("value = %d, want %d", got, want)
	}
}

func TestAtomicCompareAndSwap(t *testing.T) {
	var n atomic.Int64
	n.Store(5)
	// 只有当当前值等于 5 时才替换为 9。
	swapped := n.CompareAndSwap(5, 9)
	if !swapped || n.Load() != 9 {
		t.Fatalf("CAS failed: swapped=%v value=%d", swapped, n.Load())
	}
	// 当前值已是 9，用 5 作为旧值会失败。
	if n.CompareAndSwap(5, 100) {
		t.Fatal("unexpected CAS success")
	}
}
