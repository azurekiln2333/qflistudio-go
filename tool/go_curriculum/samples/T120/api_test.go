// api_test.go 是 T120 的端到端测试：用 httptest 覆盖正常与错误路径，
// 并断言中间件确实记录了请求，全程离线、确定。
package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func fixedNow() time.Time {
	return time.Date(2026, 10, 12, 14, 0, 0, 0, time.UTC)
}

func TestHealth(t *testing.T) {
	var log []string
	h := NewHandler(fixedNow, &log)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/health", nil))

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", rec.Code)
	}
	if ct := rec.Header().Get("Content-Type"); ct != "application/json" {
		t.Fatalf("content-type = %q", ct)
	}
	var r response
	if err := json.Unmarshal(rec.Body.Bytes(), &r); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if r.Status != "ok" {
		t.Fatalf("status field = %q, want ok", r.Status)
	}
	if len(log) != 1 || log[0] != "GET /health" {
		t.Fatalf("log = %v", log)
	}
}

func TestTimeEndpoint(t *testing.T) {
	var log []string
	h := NewHandler(fixedNow, &log)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/time", nil))

	var r response
	if err := json.Unmarshal(rec.Body.Bytes(), &r); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if r.Value != "2026-10-12T14:00:00Z" {
		t.Fatalf("value = %q, want fixed time", r.Value)
	}
}

func TestTimeEndpointRejectsPost(t *testing.T) {
	var log []string
	h := NewHandler(fixedNow, &log)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodPost, "/api/time", nil))

	if rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d, want 405", rec.Code)
	}
	var r response
	_ = json.Unmarshal(rec.Body.Bytes(), &r)
	if r.Status != "error" || r.Error == "" {
		t.Fatalf("error response = %+v", r)
	}
}
