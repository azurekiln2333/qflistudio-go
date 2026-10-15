// T109 覆盖率与测试组织。
//
// go test -coverprofile 生成覆盖率文件，go tool cover 可生成 HTML 报告。
// 本文件既演示如何组织多个测试文件共享同一包（见目录结构说明），
// 又通过一条断言确保关键分支都被覆盖到。
//
// test-package 工程例子，不能一键导入。完整结构：
//   covertest/
//   ├── go.mod        // module covertest\n\ngo 1.27
//   ├── calc.go       // 被测逻辑
//   └── calc_test.go  // 本文件
// 运行（官方 SDK）：
//   go test ./...
//   go test -coverprofile=cover.out ./... && go tool cover -func=cover.out
// desktop only。
package covertest

import "testing"

// Classify 定义在 calc.go（同包另一文件），此处只做测试，
// 演示同一包内多文件如何组织。
func TestClassifyAllBranches(t *testing.T) {
	cases := map[int]string{-1: "negative", 0: "zero", 1: "positive"}
	for in, want := range cases {
		if got := Classify(in); got != want {
			t.Errorf("Classify(%d) = %q, want %q", in, got, want)
		}
	}
}
