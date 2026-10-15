// T107 测试夹具：t.TempDir、t.Cleanup。
//
// t.TempDir() 为每个测试提供独立、自动清理的临时目录；
// t.Cleanup(fn) 注册测试结束时执行的清理，即使测试失败也会运行。
// 二者让涉及文件系统的测试隔离且无残留。
//
// test-package 工程例子，不能一键导入。完整结构：
//   fixturetest/
//   ├── go.mod         // module fixturetest\n\ngo 1.27
//   └── fixture_test.go // 本文件
// 运行：go test ./...   desktop only（文件系统）。
package fixturetest

import (
	"os"
	"path/filepath"
	"testing"
)

func TestWriteAndReadFixture(t *testing.T) {
	dir := t.TempDir() // 每个测试独享，测试结束自动删除

	// 注册清理：验证确实执行（演示 t.Cleanup 语义）。
	cleaned := false
	t.Cleanup(func() { cleaned = true })

	path := filepath.Join(dir, "data.txt")
	if err := os.WriteFile(path, []byte("hello"), 0o644); err != nil {
		t.Fatalf("write: %v", err)
	}
	got, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if string(got) != "hello" {
		t.Fatalf("content = %q, want hello", string(got))
	}
	// 同一测试内 cleaned 仍为 false（Cleanup 在测试返回后才跑）。
	if cleaned {
		t.Fatal("cleanup ran too early")
	}
}

func TestTempDirIsolated(t *testing.T) {
	// 第二个测试拿到不同的临时目录，互不影响。
	dir := t.TempDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatalf("readdir: %v", err)
	}
	if len(entries) != 0 {
		t.Fatalf("expected empty temp dir, got %d entries", len(entries))
	}
}
