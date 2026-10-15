// T110 Fuzz 测试发现边界缺陷。
//
// Fuzz 测试（Go 1.18+）用 f.Fuzz 提供随机输入，穷举边界并最小化复现用例。
// 本示例的 ParsePort 只接受 1..65535；fuzz target 断言"要么解析成功且在
// 范围内，要么返回错误"，从而暴露越界。为避免运行时长不确定，
// 常规 go test 只跑种子语料（确定性），fuzz 模式需显式 -fuzz。
//
// test-package / fuzz 工程例子，不能一键导入。完整结构：
//   fuzztest/
//   ├── go.mod       // module fuzztest\n\ngo 1.27
//   └── fuzz_test.go // 本文件
// 运行（官方 SDK）：
//   go test ./...             // 只跑种子
//   go test -fuzz FuzzParsePort -fuzztime 10s ./...
// desktop only（移动端不支持 fuzz）。
package fuzztest

import (
	"fmt"
	"strconv"
	"testing"
)

// ParsePort 解析端口并校验范围。
func ParsePort(s string) (int, error) {
	n, err := strconv.Atoi(s)
	if err != nil {
		return 0, err
	}
	if n < 1 || n > 65535 {
		return 0, fmt.Errorf("port %d out of range", n)
	}
	return n, nil
}

func TestParsePortSeeds(t *testing.T) {
	cases := []struct {
		in      string
		wantErr bool
	}{
		{"80", false},
		{"65535", false},
		{"0", true},
		{"65536", true},
		{"abc", true},
	}
	for _, c := range cases {
		_, err := ParsePort(c.in)
		if (err != nil) != c.wantErr {
			t.Fatalf("ParsePort(%q) err=%v, wantErr=%v", c.in, err, c.wantErr)
		}
	}
}

// FuzzParsePort 断言不变量：成功则必在 [1,65535]，否则必有错误。
func FuzzParsePort(f *testing.F) {
	f.Add("80")
	f.Add("0")
	f.Add("65536")
	f.Add("not-a-number")
	f.Fuzz(func(t *testing.T, s string) {
		n, err := ParsePort(s)
		if err == nil && (n < 1 || n > 65535) {
			t.Fatalf("ParsePort(%q) = %d with nil error, out of range", s, n)
		}
	})
}
