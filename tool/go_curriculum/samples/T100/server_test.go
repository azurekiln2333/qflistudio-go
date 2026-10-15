// T100 net/http 服务端：Handler 与路由。
//
// http.ServeMux 把路径映射到 Handler。用 httptest.NewRecorder 可以在不
// 真正监听端口的情况下直接调用 Handler 并检查响应，因此测试离线且确定。
//
// test-package 工程例子，不能一键导入。完整结构：
//   httpserver/
//   ├── go.mod         // module httpserver\n\ngo 1.27
//   └── server_test.go // 本文件
// 运行：go test ./...   desktop only。
package httpserver

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

// NewMux 构造路由表，便于测试直接复用。
func NewMux() *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("/hello", func(w http.ResponseWriter, r *http.Request) {
		_, _ = io.WriteString(w, "hello")
	})
	mux.HandleFunc("/bye", func(w http.ResponseWriter, r *http.Request) {
		_, _ = io.WriteString(w, "bye")
	})
	return mux
}

func TestRoutes(t *testing.T) {
	mux := NewMux()
	cases := []struct {
		path string
		want string
	}{
		{"/hello", "hello"},
		{"/bye", "bye"},
	}
	for _, c := range cases {
		req := httptest.NewRequest(http.MethodGet, c.path, nil)
		rec := httptest.NewRecorder()
		mux.ServeHTTP(rec, req)
		if rec.Code != http.StatusOK {
			t.Fatalf("%s status = %d", c.path, rec.Code)
		}
		if got := rec.Body.String(); got != c.want {
			t.Fatalf("%s body = %q, want %q", c.path, got, c.want)
		}
	}
}
