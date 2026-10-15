// T099 net/http 客户端：GET 与响应处理。
//
// http.Client 发起请求、读取响应。为避免联网，本示例用
// net/http/httptest 起一个本地测试服务器，Client 请求它并读取 body。
//
// test-package 工程例子，不能一键导入。完整结构：
//   httpclient/
//   ├── go.mod        // module httpclient\n\ngo 1.27
//   └── client_test.go // 本文件
// 运行（官方 SDK）：go test ./...
// 移动端 Yaegi 对 net 未实测，desktop only。
package httpclient

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestClientGet(t *testing.T) {
	// 本地测试服务器，不访问外网。
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("method = %s, want GET", r.Method)
		}
		w.WriteHeader(http.StatusOK)
		_, _ = io.WriteString(w, "hello from server")
	}))
	defer srv.Close()

	resp, err := http.Get(srv.URL)
	if err != nil {
		t.Fatalf("GET failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("read body: %v", err)
	}
	if string(body) != "hello from server" {
		t.Fatalf("body = %q", string(body))
	}
}
