package main

import (
	"crypto/sha256"
	"fmt"
	"net/http"
	"net/http/httptest"
)

func main() {
	body := []byte("offline catalog")
	sum := sha256.Sum256(body)
	etag := fmt.Sprintf("\"%x\"", sum[:8])
	app := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("ETag", etag)
		if r.Header.Get("If-None-Match") == etag {
			w.WriteHeader(http.StatusNotModified)
			return
		}
		w.Write(body)
	})
	for _, match := range []bool{false, true} {
		r := httptest.NewRequest("GET", "/catalog", nil)
		if match {
			r.Header.Set("If-None-Match", etag)
		}
		w := httptest.NewRecorder()
		app.ServeHTTP(w, r)
		fmt.Printf("match=%t status=%d bytes=%d\n", match, w.Code, w.Body.Len())
	}
}
