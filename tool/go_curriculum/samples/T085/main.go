// T085 io.Reader / io.Writer 抽象。
//
// io.Reader 只有一个 Read([]byte) 方法，io.Writer 只有一个 Write([]byte) 方法。
// 任何实现了它们的东西都能互相组合：文件、网络、内存缓冲、字符串……
// 本示例把字符串当 Reader、把 bytes.Buffer 当 Writer，用 io.Copy 搬运，
// 从而无需知道底层到底是什么。
package main

import (
	"bytes"
	"fmt"
	"io"
	"strings"
)

func main() {
	// strings.Reader 实现了 io.Reader。
	var r io.Reader = strings.NewReader("hello, io.Reader")

	// bytes.Buffer 实现了 io.Writer。
	var w io.Writer = &bytes.Buffer{}

	// io.Copy 只依赖这两个接口，不关心具体类型。
	n, err := io.Copy(w, r)
	fmt.Println("copied bytes:", n, "err:", err)
	fmt.Println("buffer content:", w.(*bytes.Buffer).String())

	// 自定义 Reader：把固定字节重复 n 次。
	rr := &repeatReader{data: []byte("ab"), times: 3}
	out, _ := io.ReadAll(rr)
	fmt.Println("custom reader:", string(out))
}

// repeatReader 是自定义 io.Reader，演示只要实现 Read 就能被 io 工具使用。
type repeatReader struct {
	data  []byte
	times int
	pos   int
}

func (r *repeatReader) Read(p []byte) (int, error) {
	// 计算还剩多少重复次数。
	if r.pos >= len(r.data)*r.times {
		return 0, io.EOF
	}
	n := copy(p, r.data[r.pos%len(r.data):])
	r.pos += n
	return n, nil
}
