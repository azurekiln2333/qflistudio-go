// T119 综合项目二：并发词频统计器（worker pool + IO）。
//
// 整合：worker pool、文件/字符串 IO、结果聚合。多个 worker 并发统计
// 若干文本的词频，最后按词排序输出，因此结果与串行一致且确定。
//
// module-project 工程例子，不能一键导入。完整结构：
//   wordfreq/
//   ├── go.mod          // module wordfreq\n\ngo 1.27
//   ├── main.go         // 本文件
//   └── freq_test.go    // 端到端测试（含串行/并发一致性）
// 运行（官方 SDK）：
//   go run .
//   go test ./...
// desktop only（并发 + 文件）。
package main

import (
	"fmt"
	"sort"
	"strings"
	"sync"
)

// countWords 串行统计一段文本的词频。
func countWords(text string) map[string]int {
	counts := make(map[string]int)
	for _, w := range strings.Fields(strings.ToLower(text)) {
		counts[w]++
	}
	return counts
}

// merge 把一个局部计数并入全局计数。
func merge(dst, src map[string]int) {
	for k, v := range src {
		dst[k] += v
	}
}

// CountParallel 用 workers 个 goroutine 并发统计多段文本。
func CountParallel(texts []string, workers int) map[string]int {
	if workers < 1 {
		workers = 1
	}
	jobs := make(chan string)
	partials := make(chan map[string]int)

	var wg sync.WaitGroup
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer wg.Done()
			for text := range jobs {
				partials <- countWords(text)
			}
		}()
	}

	go func() {
		for _, t := range texts {
			jobs <- t
		}
		close(jobs)
	}()

	go func() {
		wg.Wait()
		close(partials)
	}()

	total := make(map[string]int)
	for p := range partials {
		merge(total, p)
	}
	return total
}

// sortedKeys 返回排序后的键，保证输出确定。
func sortedKeys(m map[string]int) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

func main() {
	texts := []string{
		"go go gopher",
		"gopher runs go",
		"go test",
	}

	serial := make(map[string]int)
	for _, t := range texts {
		merge(serial, countWords(t))
	}

	parallel := CountParallel(texts, 3)

	// 并发结果必须与串行完全一致。
	fmt.Println("parallel matches serial:", sameCounts(serial, parallel))

	for _, k := range sortedKeys(parallel) {
		fmt.Printf("%-8s %d\n", k, parallel[k])
	}
}

func sameCounts(a, b map[string]int) bool {
	if len(a) != len(b) {
		return false
	}
	for k, v := range a {
		if b[k] != v {
			return false
		}
	}
	return true
}
