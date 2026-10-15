// T056 错误处理模式：立即返回与上下文补充。
//
// 惯例：错误产生处立即 return，调用链每一层用 %w 补充上下文（哪个操作、哪个键），
// 到边界处统一打印一次。这样既不丢因，又能给出可定位的路径。
package main

import (
	"errors"
	"fmt"
)

var ErrNotFound = errors.New("not found")

// 最底层：只返回原始错误。
func readConfig(m map[string]string, key string) (string, error) {
	v, ok := m[key]
	if !ok {
		return "", ErrNotFound
	}
	return v, nil
}

// 中层：补充“读取哪个配置”的上下文。
func loadConfig(m map[string]string) (string, error) {
	v, err := readConfig(m, "db.dsn")
	if err != nil {
		return "", fmt.Errorf("loadConfig: %w", err)
	}
	return v, nil
}

// 上层：再补充“启动阶段”上下文。
func start(m map[string]string) error {
	if _, err := loadConfig(m); err != nil {
		return fmt.Errorf("start: %w", err)
	}
	return nil
}

func main() {
	// 空配置：错误链包含每一层上下文。
	err := start(map[string]string{})
	fmt.Println("error chain:", err)
	fmt.Println("still Is ErrNotFound:", errors.Is(err, ErrNotFound))

	// 逐层打印，展示上下文补充效果。
	for e := err; e != nil; e = errors.Unwrap(e) {
		fmt.Println("  -", e)
	}

	// 有配置时成功。
	if err := start(map[string]string{"db.dsn": "postgres://x"}); err != nil {
		fmt.Println("unexpected:", err)
	} else {
		fmt.Println("started ok")
	}
}
