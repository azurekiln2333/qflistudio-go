// T104 超时、重试与优雅关闭。
//
// http.Server 应设置超时避免慢连接耗尽资源；优雅关闭用
// Server.Shutdown(ctx) 等待在途请求结束。本示例用 httptest 服务器 +
// 带 Client.Timeout 的客户端演示超时，并用 Shutdown 演示优雅关闭。
// 断言只看"是否超时/是否成功关闭"，不比较具体耗时。
//
// test-package 工程例子，不能一键导入。完整结构：
//   httptimeout/
//   ├── go.mod            // module httptimeout\n\ngo 1.27
//   └── timeout_test.go   // 本文件
// 运行：go test ./...   desktop only（涉及监听/关闭）。
package httptimeout

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestClientTimeout(t *testing.T) {
	// 服务器故意慢于客户端超时。
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(50 * time.Millisecond)
		_, _ = w.Write([]byte("late"))
	}))
	defer srv.Close()

	client := &http.Client{Timeout: 5 * time.Millisecond}
	_, err := client.Get(srv.URL)
	// 断言：必然超时（错误来自 Client.Timeout），不比较精确耗时。
	if err == nil {
		t.Fatal("expected timeout error, got nil")
	}
}

func TestGracefulShutdown(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte("ok"))
	}))

	// 正常请求成功。
	resp, err := http.Get(srv.URL)
	if err != nil {
		t.Fatalf("GET: %v", err)
	}
	resp.Body.Close()

	// 优雅关闭：给一个确定的短超时；断言关闭调用无错误。
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	if err := srv.Config.Shutdown(ctx); err != nil {
		t.Fatalf("shutdown: %v", err)
	}
	srv.Close()
}
