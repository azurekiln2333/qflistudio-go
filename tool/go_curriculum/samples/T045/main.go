// T045 标准接口：Stringer 与 error。
//
// fmt.Stringer 的 String() 方法决定 fmt 打印该值时的文本；
// error 接口的 Error() 同理决定错误文本。实现它们即可定制输出。
package main

import (
	"errors"
	"fmt"
)

// Color 实现 Stringer。
type Color int

const (
	Red Color = iota
	Green
	Blue
)

func (c Color) String() string {
	switch c {
	case Red:
		return "RED"
	case Green:
		return "GREEN"
	case Blue:
		return "BLUE"
	default:
		return fmt.Sprintf("Color(%d)", int(c))
	}
}

// ValidationError 实现 error。
type ValidationError struct {
	Field string
	Msg   string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation failed on %s: %s", e.Field, e.Msg)
}

func main() {
	// 有 String() 后，%v/%s 打印的是名字而非数字。
	fmt.Println("color:", Red)
	fmt.Printf("color with %%v: %v, %%d: %d\n", Green, Green)

	// 越界值走回退分支。
	fmt.Println("unknown:", Color(99))

	// error 值：Error() 决定 %v 输出。
	var err error = &ValidationError{Field: "age", Msg: "must be positive"}
	fmt.Println("error:", err)

	// errors.Is 对指针错误按身份匹配（此处与本身比较）。
	fmt.Println("same error:", errors.Is(err, err))
}
