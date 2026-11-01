package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

func handler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/health" {
		http.NotFound(w, r)
		return
	}
	if r.Method != http.MethodGet {
		w.Header().Set("Allow", "GET")
		http.Error(w, "method", http.StatusMethodNotAllowed)
		return
	}
	w.Header().Set("Content-Type", "text/plain")
	w.Write([]byte("ready"))
}
func main() {
	for _, item := range []struct{ method, path string }{{"GET", "/health"}, {"POST", "/health"}, {"GET", "/missing"}} {
		r := httptest.NewRequest(item.method, item.path, nil)
		w := httptest.NewRecorder()
		handler(w, r)
		fmt.Printf("%s %s=%d allow=%q\n", item.method, item.path, w.Code, w.Header().Get("Allow"))
	}
}
