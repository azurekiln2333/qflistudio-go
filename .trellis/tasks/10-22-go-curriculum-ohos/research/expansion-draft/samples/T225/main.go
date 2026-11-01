package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"time"
)

func main() {
	r := httptest.NewRequest("GET", "/data.txt", nil)
	r.Header.Set("Range", "bytes=1-3")
	w := httptest.NewRecorder()
	http.ServeContent(w, r, "data.txt", time.Unix(0, 0), strings.NewReader("abcdef"))
	fmt.Printf("status=%d\nrange=%s\nbody=%s\n", w.Code, w.Header().Get("Content-Range"), w.Body.String())
	r = httptest.NewRequest("GET", "/data.txt", nil)
	r.Header.Set("Range", "bytes=99-100")
	w = httptest.NewRecorder()
	http.ServeContent(w, r, "data.txt", time.Unix(0, 0), strings.NewReader("abcdef"))
	fmt.Printf("invalid=%d\n", w.Code)
}
