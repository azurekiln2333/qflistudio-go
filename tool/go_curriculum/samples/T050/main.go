// T050 errors.New、fmt.Errorf 与哨兵错误。
//
// 哨兵错误（sentinel error）是包级导出的错误变量，调用方用 errors.Is
// 判断错误身份，而不比较错误字符串——字符串比较脆弱，包装后即失效。
package main

import (
	"errors"
	"fmt"
)

// ErrNotFound 是一个哨兵错误。
var ErrNotFound = errors.New("not found")

// lookup 在缺少键时返回哨兵错误（可能被外层包装）。
func lookup(m map[string]int, key string) (int, error) {
	v, ok := m[key]
	if !ok {
		return 0, ErrNotFound
	}
	return v, nil
}

// withContext 在外层用 %w 包装，保留可被 errors.Is 识别的原始错误。
func withContext(err error, key string) error {
	return fmt.Errorf("lookup %q: %w", key, err)
}

func main() {
	m := map[string]int{"a": 1}

	v, err := lookup(m, "a")
	fmt.Println("found a:", v, "err:", err)

	_, err = lookup(m, "missing")
	fmt.Println("errors.Is ErrNotFound:", errors.Is(err, ErrNotFound))

	// 包装后仍然可以用 errors.Is 命中哨兵。
	wrapped := withContext(ErrNotFound, "missing")
	fmt.Println("wrapped text:", wrapped)
	fmt.Println("wrapped Is ErrNotFound:", errors.Is(wrapped, ErrNotFound))

	// 直接比较字符串是脆弱的，示例说明不要这样做。
	fmt.Println("string compare is fragile:", errors.Is(err, ErrNotFound))
}
