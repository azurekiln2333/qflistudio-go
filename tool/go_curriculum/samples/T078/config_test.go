// T078 sync.RWMutex 读写分离。
//
// 读多写少的场景下，用 RWMutex 允许多个读并发进行，只有写才独占。
// 本示例维护一个配置映射：读操作可并发，写操作互斥，最终值确定。
//
// test-package 工程例子，不能一键导入。完整结构：
//   rwconfig/
//   ├── go.mod         // module rwconfig\n\ngo 1.27
//   └── config_test.go // 本文件
// 运行：go test ./...  /  go test -race ./...
// 移动端 Yaegi 不支持 go test/-race，desktop only。
package rwconfig

import (
	"strconv"
	"sync"
	"testing"
)

// Config 是并发安全的键值配置。
type Config struct {
	mu sync.RWMutex
	m  map[string]string
}

// NewConfig 建立空配置。
func NewConfig() *Config { return &Config{m: make(map[string]string)} }

// Set 写操作：独占锁。
func (c *Config) Set(k, v string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.m[k] = v
}

// Get 读操作：共享锁，多读可并发。
func (c *Config) Get(k string) (string, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	v, ok := c.m[k]
	return v, ok
}

func TestConfigConcurrentReadWrite(t *testing.T) {
	c := NewConfig()
	var wg sync.WaitGroup

	// 若干写者写入互不相同的键。
	const writers = 20
	wg.Add(writers)
	for i := 0; i < writers; i++ {
		go func(i int) {
			defer wg.Done()
			c.Set("k"+strconv.Itoa(i), strconv.Itoa(i))
		}(i)
	}
	wg.Wait()

	// 若干读者并发读取；确定性断言：每个键都能读回正确值。
	const readers = 50
	wg.Add(readers)
	errs := make(chan string, readers)
	for i := 0; i < readers; i++ {
		go func(i int) {
			defer wg.Done()
			key := "k" + strconv.Itoa(i%writers)
			v, ok := c.Get(key)
			if !ok || v != strconv.Itoa(i%writers) {
				errs <- "bad value for " + key
			}
		}(i)
	}
	wg.Wait()
	close(errs)

	for e := range errs {
		t.Fatal(e)
	}
}
