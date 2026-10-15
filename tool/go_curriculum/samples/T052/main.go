// T052 errors.Is 与 errors.As 的适用差异。
//
// errors.Is 用于“值/身份”匹配（哨兵错误），遍历解包链比较；
// errors.As 用于“类型”匹配，把链上某个具体类型的错误取出到目标变量，读取其字段。
package main

import (
	"errors"
	"fmt"
)

// PathError 是带字段的自定义错误类型。
type PathError struct {
	Path string
	Op   string
}

func (e *PathError) Error() string { return e.Op + " " + e.Path + ": failed" }

var ErrPermission = errors.New("permission denied")

// open 在路径含 "secret" 时返回带类型的错误，否则返回哨兵错误。
func open(path string) error {
	if len(path) >= 6 && path[:6] == "secret" {
		return &PathError{Path: path, Op: "open"}
	}
	return fmt.Errorf("open %s: %w", path, ErrPermission)
}

func main() {
	// errors.Is：判断是否属于某个哨兵错误（值匹配）。
	err := open("data.txt")
	fmt.Println("Is ErrPermission:", errors.Is(err, ErrPermission))

	// errors.As：把具体类型取出，读取其字段（类型匹配）。
	err = open("secret.cfg")
	var pe *PathError
	if errors.As(err, &pe) {
		fmt.Println("As PathError -> path:", pe.Path, "op:", pe.Op)
	}

	// As 对内层包装同样生效。
	inner := fmt.Errorf("wrapped: %w", &PathError{Path: "a", Op: "read"})
	var pe2 *PathError
	fmt.Println("As on wrapped:", errors.As(inner, &pe2), pe2.Op)
}
