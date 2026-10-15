// T102 JSON API 与错误响应约定。
//
// 一个 JSON API 应统一响应结构：成功返回数据，失败返回错误码与消息，
// 并设置 Content-Type: application/json。本示例用统一 envelope 输出，
// 并测试正常与错误两条路径。
//
// test-package 工程例子，不能一键导入。完整结构：
//   httpjson/
//   ├── go.mod      // module httpjson\n\ngo 1.27
//   └── api_test.go // 本文件
// 运行：go test ./...   desktop only。
package httpjson

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// Envelope 是所有响应的统一外壳。
type Envelope struct {
	OK    bool   `json:"ok"`
	Data  any    `json:"data,omitempty"`
	Error string `json:"error,omitempty"`
}

// handler 依赖查询参数 name：有则成功，无则错误。
func handler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	name := r.URL.Query().Get("name")
	if name == "" {
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(Envelope{OK: false, Error: "name is required"})
		return
	}
	_ = json.NewEncoder(w).Encode(Envelope{OK: true, Data: map[string]string{"name": name}})
}

func TestJSONAPI(t *testing.T) {
	// 成功路径。
	okReq := httptest.NewRequest(http.MethodGet, "/?name=alice", nil)
	okRec := httptest.NewRecorder()
	handler(okRec, okReq)
	if okRec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", okRec.Code)
	}
	if ct := okRec.Header().Get("Content-Type"); ct != "application/json" {
		t.Fatalf("content-type = %q", ct)
	}
	var okEnv Envelope
	if err := json.Unmarshal(okRec.Body.Bytes(), &okEnv); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if !okEnv.OK {
		t.Fatalf("ok = false, want true")
	}

	// 错误路径。
	badReq := httptest.NewRequest(http.MethodGet, "/", nil)
	badRec := httptest.NewRecorder()
	handler(badRec, badReq)
	if badRec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400", badRec.Code)
	}
	var badEnv Envelope
	if err := json.Unmarshal(badRec.Body.Bytes(), &badEnv); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if badEnv.OK || badEnv.Error == "" {
		t.Fatalf("error envelope = %+v", badEnv)
	}
	var raw map[string]json.RawMessage
	_ = json.Unmarshal(badRec.Body.Bytes(), &raw)
	if _, present := raw["data"]; present {
		t.Fatal("error response must not include data")
	}
}
