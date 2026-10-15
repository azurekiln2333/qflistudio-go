// T101 请求与响应：Method、Header、状态码。
//
// Handler 可读取 r.Method / r.Header 并据此分支；用 w.WriteHeader 设置
// 状态码。方法不匹配时返回 405 Method Not Allowed 是常见约定。
//
// test-package 工程例子，不能一键导入。完整结构：
//   httpmethod/
//   ├── go.mod         // module httpmethod\n\ngo 1.27
//   └── method_test.go // 本文件
// 运行：go test ./...   desktop only。
package httpmethod

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

// handler 只接受 POST；其他方法返回 405 并带 Allow 头。
func handler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", http.MethodPost)
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	// 回显自定义头。
	w.Header().Set("X-Echo", r.Header.Get("X-Token"))
	w.WriteHeader(http.StatusCreated)
	_, _ = io.WriteString(w, "created")
}

func TestMethodRouting(t *testing.T) {
	// POST：应 201。
	post := httptest.NewRequest(http.MethodPost, "/", nil)
	post.Header.Set("X-Token", "abc")
	postRec := httptest.NewRecorder()
	handler(postRec, post)
	if postRec.Code != http.StatusCreated {
		t.Fatalf("POST status = %d, want 201", postRec.Code)
	}
	if got := postRec.Header().Get("X-Echo"); got != "abc" {
		t.Fatalf("X-Echo = %q, want abc", got)
	}

	// GET：应 405 且带 Allow 头。
	get := httptest.NewRequest(http.MethodGet, "/", nil)
	getRec := httptest.NewRecorder()
	handler(getRec, get)
	if getRec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("GET status = %d, want 405", getRec.Code)
	}
	if got := getRec.Header().Get("Allow"); got != http.MethodPost {
		t.Fatalf("Allow = %q, want POST", got)
	}
}
