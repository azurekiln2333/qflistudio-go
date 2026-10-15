// T111 接口打桩与依赖替换测试。
//
// 被测逻辑依赖一个接口（如存储）。生产用真实实现，测试注入"桩"（stub）
// 以隔离外部依赖、制造确定结果。这样测试不需要数据库/网络，且能覆盖
// 错误分支。
//
// test-package 工程例子，不能一键导入。完整结构：
//   stubtest/
//   ├── go.mod       // module stubtest\n\ngo 1.27
//   └── stub_test.go // 本文件
// 运行：go test ./...   desktop only（go test）。
package stubtest

import (
	"errors"
	"testing"
)

// Store 是被依赖的接口。
type Store interface {
	Get(key string) (string, error)
}

// Service 通过接口使用 Store。
type Service struct{ store Store }

// Lookup 读取 key 并在缺失时返回统一错误。
func (s *Service) Lookup(key string) (string, error) {
	v, err := s.store.Get(key)
	if err != nil {
		return "", err
	}
	return v, nil
}

// stubStore 是测试桩：用 map 提供确定数据，并可配置返回错误。
type stubStore struct {
	data map[string]string
	err  error
}

func (s stubStore) Get(key string) (string, error) {
	if s.err != nil {
		return "", s.err
	}
	v, ok := s.data[key]
	if !ok {
		return "", errors.New("not found")
	}
	return v, nil
}

func TestLookupSuccess(t *testing.T) {
	svc := &Service{store: stubStore{data: map[string]string{"a": "1"}}}
	v, err := svc.Lookup("a")
	if err != nil || v != "1" {
		t.Fatalf("Lookup(a) = %q,%v", v, err)
	}
}

func TestLookupNotFound(t *testing.T) {
	svc := &Service{store: stubStore{data: map[string]string{}}}
	if _, err := svc.Lookup("missing"); err == nil {
		t.Fatal("expected error for missing key")
	}
}

func TestLookupStoreFailure(t *testing.T) {
	sentinel := errors.New("backend down")
	svc := &Service{store: stubStore{err: sentinel}}
	_, err := svc.Lookup("a")
	if !errors.Is(err, sentinel) {
		t.Fatalf("err = %v, want sentinel", err)
	}
}
