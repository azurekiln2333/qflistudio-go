// T053 自定义错误类型与行为方法。
//
// 自定义错误类型可携带结构化信息（字段）并实现额外方法，比字符串错误更有用。
// 实现 Unwrap 还能融入 errors.Is/As 链。
package main

import (
	"errors"
	"fmt"
)

// QueryError 携带 SQL 与原因，并实现 Unwrap 暴露底层错误。
type QueryError struct {
	SQL   string
	Cause error
}

func (e *QueryError) Error() string {
	return fmt.Sprintf("query %q failed: %v", e.SQL, e.Cause)
}

func (e *QueryError) Unwrap() error { return e.Cause }

var ErrTimeout = errors.New("timeout")

// run 返回包装了哨兵错误的 QueryError。
func run(sql string) error {
	return &QueryError{SQL: sql, Cause: ErrTimeout}
}

func main() {
	err := run("SELECT 1")

	// Error() 决定可读文本。
	fmt.Println("text:", err)

	// Unwrap 让 errors.Is 能命中底层哨兵。
	fmt.Println("Is ErrTimeout:", errors.Is(err, ErrTimeout))

	// errors.As 取出带字段的类型并读取元数据。
	var qe *QueryError
	if errors.As(err, &qe) {
		fmt.Println("SQL field:", qe.SQL)
		fmt.Println("Cause field:", qe.Cause)
	}

	// errors.Unwrap 直接取出内层。
	fmt.Println("Unwrap == ErrTimeout:", errors.Unwrap(err) == ErrTimeout)
}
