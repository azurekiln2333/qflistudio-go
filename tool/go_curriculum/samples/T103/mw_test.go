// T103 中间件：日志、恢复与链式组合。
//
// 中间件是"接收一个 Handler、返回一个 Handler"的函数，可在调用前后插入
// 逻辑（日志、恢复、鉴权）。多个中间件可链式包裹。本示例用中间件记录
// 请求方法并统计调用次数，用 httptest 断言链路确实被经过。
//
// test-package 工程例子，不能一键导入。完整结构：
//   httpmw/
//   ├── go.mod     // module httpmw\n\ngo 1.27
//   └── mw_test.go // 本文件
// 运行：go test ./...   desktop only。
package httpmw

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

// Middleware 是标准中间件签名。
type Middleware func(http.Handler) http.Handler

// logging 记录每个经过的请求方法。
func logging(log *[]string) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			*log = append(*log, r.Method+" "+r.URL.Path)
			next.ServeHTTP(w, r)
		})
	}
}

// recoverer 捕获 panic，返回 500，保证链路不崩。
func recoverer(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				w.WriteHeader(http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// chain 按顺序包裹：chain(h, a, b) == a(b(h))。
func chain(h http.Handler, mws ...Middleware) http.Handler {
	for i := len(mws) - 1; i >= 0; i-- {
		h = mws[i](h)
	}
	return h
}

func TestMiddlewareChain(t *testing.T) {
	var log []string

	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/boom" {
			panic("boom")
		}
		_, _ = io.WriteString(w, "ok")
	})
	h := chain(final, logging(&log), recoverer)

	// 正常请求。
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/ok", nil))
	if rec.Body.String() != "ok" {
		t.Fatalf("body = %q, want ok", rec.Body.String())
	}

	// panic 请求：recoverer 应返回 500。
	rec2 := httptest.NewRecorder()
	h.ServeHTTP(rec2, httptest.NewRequest(http.MethodGet, "/boom", nil))
	if rec2.Code != http.StatusInternalServerError {
		t.Fatalf("panic status = %d, want 500", rec2.Code)
	}

	// 日志中间件应记录两次，且顺序确定。
	if len(log) != 2 || log[0] != "GET /ok" || log[1] != "GET /boom" {
		t.Fatalf("log = %v", log)
	}
}
