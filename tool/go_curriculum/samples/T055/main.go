// T055 defer 在资源清理与错误聚合中的应用。
//
// defer 在函数返回时执行（LIFO），常用于释放资源。
// 通过命名返回值，defer 可以合并多个清理步骤的错误——避免“只返回最后一个错误”丢因。
package main

import (
	"errors"
	"fmt"
)

// closer 模拟可关闭资源。
type closer struct {
	name string
	err  error
}

func (c *closer) Close() error {
	if c.err != nil {
		return fmt.Errorf("close %s: %w", c.name, c.err)
	}
	return nil
}

// process 打开两个资源，用 defer 关闭并聚合关闭错误。
func process(a, b *closer) (err error) {
	// defer 在 return 之后执行，可修改命名返回值 err。
	defer func() {
		if cerr := a.Close(); cerr != nil {
			err = errors.Join(err, cerr) // 合并，而非覆盖
		}
		if cerr := b.Close(); cerr != nil {
			err = errors.Join(err, cerr)
		}
	}()
	return nil
}

func main() {
	// 两个都正常关闭。
	if err := process(&closer{name: "a"}, &closer{name: "b"}); err != nil {
		fmt.Println("unexpected:", err)
	} else {
		fmt.Println("both closed cleanly")
	}

	// a 关闭失败：错误被保留。
	errA := errors.New("disk io")
	err := process(&closer{name: "a", err: errA}, &closer{name: "b"})
	fmt.Println("close error:", err)
	fmt.Println("preserved cause:", errors.Is(err, errA))

	// defer 的 LIFO 顺序演示。
	func() {
		for i := 1; i <= 3; i++ {
			defer fmt.Println("deferred", i)
		}
		fmt.Println("body done")
	}()
}
