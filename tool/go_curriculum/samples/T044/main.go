// T044 接口组合与最小接口原则。
//
// Go 鼓励“小而专”的接口：Reader、Writer、Closer 各管一件事，再按需组合。
// 接口可以嵌入接口形成组合接口，如 ReadWriteCloser = Reader+Writer+Closer。
// 本示例用合成接口统一读写设备，并演示最小接口的好处。
package main

import (
	"fmt"
	"strings"
)

// Reader / Writer / Closer 是最小的单方法接口。
type Reader interface{ Read() string }
type Writer interface{ Write(s string) }
type Closer interface{ Close() error }

// ReadWriteCloser 组合三个最小接口。
type ReadWriteCloser interface {
	Reader
	Writer
	Closer
}

// MemDevice 实现了全部三个方法，因此满足组合接口。
type MemDevice struct {
	data   string
	closed bool
}

func (d *MemDevice) Read() string { return d.data }
func (d *MemDevice) Write(s string) {
	d.data += s
}
func (d *MemDevice) Close() error {
	d.closed = true
	return nil
}

// useReader 只需要最小的 Reader 接口，任何能 Read 的类型都能传入。
func useReader(r Reader) string { return r.Read() }

func main() {
	var dev ReadWriteCloser = &MemDevice{data: "start"}

	dev.Write("-more")
	fmt.Println("read:", useReader(dev)) // 组合接口可赋给最小接口

	if err := dev.Close(); err != nil {
		panic(err)
	}
	fmt.Println("closed:", dev.(*MemDevice).closed)

	// 只实现 Read 的轻量类型也能满足 Reader，便于替换与测试。
	lit := strings.NewReader("literal")
	_ = lit
	fmt.Println("minimal interface reuse: a one-method type satisfies Reader")
}
