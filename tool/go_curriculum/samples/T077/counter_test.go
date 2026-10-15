// T077 sync.Mutex 与临界区保护。
//
// 多个 goroutine 并发对同一变量做 += 会产生数据竞争（race）：读-改-写三步
// 可能交错，导致丢失更新。Mutex 把这段临界区串行化，使结果确定。
//
// 这是一个 test-package 工程例子，不能一键导入。完整结构：
//   racecounter/
//   ├── go.mod          // module racecounter\n\ngo 1.27
//   └── counter_test.go // 本文件（含被测逻辑与测试）
// 运行（官方 SDK）：
//   go test ./...
//   go test -race ./...   // 官方 Go 独有，用于证明无数据竞争
//
// 移动端 Yaegi 不支持 go test/-race，故本主题 desktop only。
package racecounter

import (
	"sync"
	"testing"
)

// Counter 是被 Mutex 保护的计数器。
type Counter struct {
	mu sync.Mutex
	n  int
}

// Inc 在锁内完成读-改-写，避免竞争。
func (c *Counter) Inc() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.n++
}

// Value 也在锁内读取，保证看到一致的值。
func (c *Counter) Value() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.n
}

// BadCounter 故意不加锁，用于对照（仅在文档中说明，不在测试里运行以免污染 -race）。
type BadCounter struct{ n int }

func (c *BadCounter) Inc() { c.n++ }

func TestCounterConcurrentIncrement(t *testing.T) {
	const goroutines = 100
	const perGoroutine = 100
	const want = goroutines * perGoroutine

	var c Counter
	var wg sync.WaitGroup
	wg.Add(goroutines)
	for i := 0; i < goroutines; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < perGoroutine; j++ {
				c.Inc()
			}
		}()
	}
	wg.Wait()

	// 确定性断言：最终计数必须精确等于期望值。
	if got := c.Value(); got != want {
		t.Fatalf("counter = %d, want %d", got, want)
	}
}

func TestCounterSequential(t *testing.T) {
	var c Counter
	for i := 0; i < 5; i++ {
		c.Inc()
	}
	if got := c.Value(); got != 5 {
		t.Fatalf("counter = %d, want 5", got)
	}
}
