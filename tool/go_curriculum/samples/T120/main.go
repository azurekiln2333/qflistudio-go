// T120 综合项目三：极简 HTTP 服务（JSON API + 中间件 + 测试）。
//
// 整合：net/http 路由、JSON 响应、中间件、超时设置与 httptest 测试。
// 服务提供 /health 与 /api/time；中间件记录请求。
//
// module-project 工程例子，不能一键导入。完整结构：
//   miniapi/
//   ├── go.mod       // module miniapi\n\ngo 1.27
//   ├── main.go      // 本文件：路由、中间件、服务器配置
//   └── api_test.go  // httptest 端到端测试（真正断言的地方）
// 运行（官方 SDK）：
//   go test ./...     // 主要验证方式（httptest，离线）
//   go run .          // 构造 handler 并说明如何监听
// desktop only（net 监听 + go test）。
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// response 是统一响应结构。
type response struct {
	Status string `json:"status"`
	Value  string `json:"value,omitempty"`
	Error  string `json:"error,omitempty"`
}

// logging 中间件：记录方法与路径到切片（便于测试断言）。
func logging(log *[]string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		*log = append(*log, r.Method+" "+r.URL.Path)
		next.ServeHTTP(w, r)
	})
}

// NewHandler 构造路由与中间件链。now 注入固定时间以保证响应确定。
func NewHandler(now func() time.Time, log *[]string) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, response{Status: "ok"})
	})

	mux.HandleFunc("/api/time", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			writeJSON(w, http.StatusMethodNotAllowed, response{Status: "error", Error: "GET only"})
			return
		}
		writeJSON(w, http.StatusOK, response{
			Status: "ok",
			Value:  now().Format(time.RFC3339),
		})
	})

	return logging(log, mux)
}

func writeJSON(w http.ResponseWriter, code int, v response) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func main() {
	fixed := func() time.Time { return time.Date(2026, 10, 12, 14, 0, 0, 0, time.UTC) }
	var log []string

	srv := &http.Server{
		Addr:         "127.0.0.1:8080",
		Handler:      NewHandler(fixed, &log),
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 5 * time.Second,
	}
	// main 只说明如何启动；真正的响应断言在 api_test.go 中用 httptest 完成，
	// 因此这里不真正 ListenAndServe，避免示例依赖固定端口。
	_ = srv
	fmt.Println("routes: /health, /api/time")
	fmt.Println("verify with: go test ./...")
}
