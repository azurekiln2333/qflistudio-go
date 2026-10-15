// T051 错误包装与 %w 的解包链。
//
// %w 在 fmt.Errorf 中表示“包装”错误，形成可解包的链：
// errors.Unwrap 逐层取出内层错误，errors.Is/As 则会遍历整条链。
package main

import (
	"errors"
	"fmt"
)

var errBase = errors.New("base failure")

// level3 最内层返回基础错误。
func level3() error { return errBase }

// level2 包装一层。
func level2() error { return fmt.Errorf("level2: %w", level3()) }

// level1 再包装一层。
func level1() error { return fmt.Errorf("level1: %w", level2()) }

func main() {
	err := level1()

	// 完整文本保留每一层的上下文。
	fmt.Println("full:", err)

	// 逐层解包，打印链上每一层。
	fmt.Println("unwrap chain:")
	for e := err; e != nil; e = errors.Unwrap(e) {
		fmt.Println(" ", e)
	}

	// errors.Is 会遍历整条链命中基础错误。
	fmt.Println("Is(errBase):", errors.Is(err, errBase))

	// 使用 %v（而非 %w）只做文本拼接，不构成可解包链。
	noChain := fmt.Errorf("context: %v", errBase)
	directive := "%v"
	fmt.Println("with "+directive+" Is(errBase):", errors.Is(noChain, errBase))
}
