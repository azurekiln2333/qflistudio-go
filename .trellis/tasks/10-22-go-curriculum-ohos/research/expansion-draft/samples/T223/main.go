package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
)

type requestKey struct{}

func identify(next http.Handler) http.Handler {
	counter := 0
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := r.Header.Get("X-Request-ID")
		if id == "" {
			counter++
			id = fmt.Sprintf("local-%d", counter)
		}
		w.Header().Set("X-Request-ID", id)
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), requestKey{}, id)))
	})
}
func main() {
	app := identify(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id, ok := r.Context().Value(requestKey{}).(string)
		if !ok {
			panic("missing ID")
		}
		fmt.Fprint(w, id)
	}))
	for _, id := range []string{"provided-7", ""} {
		r := httptest.NewRequest("GET", "/", nil)
		if id != "" {
			r.Header.Set("X-Request-ID", id)
		}
		w := httptest.NewRecorder()
		app.ServeHTTP(w, r)
		fmt.Printf("header=%s body=%s\n", w.Header().Get("X-Request-ID"), w.Body.String())
	}
}
