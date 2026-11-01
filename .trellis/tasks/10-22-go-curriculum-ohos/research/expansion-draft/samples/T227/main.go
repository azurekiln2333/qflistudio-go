package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

func main() {
	w := httptest.NewRecorder()
	http.SetCookie(w, &http.Cookie{Name: "session", Value: "local-42", Path: "/", HttpOnly: true, Secure: true, SameSite: http.SameSiteLaxMode})
	response := w.Result()
	defer response.Body.Close()
	cookies := response.Cookies()
	if len(cookies) != 1 {
		panic("cookie count")
	}
	cookie := cookies[0]
	fmt.Printf("httponly=%t secure=%t lax=%t\n", cookie.HttpOnly, cookie.Secure, cookie.SameSite == http.SameSiteLaxMode)
	r := httptest.NewRequest("GET", "https://example.test/", nil)
	r.AddCookie(cookie)
	read, err := r.Cookie("session")
	if err != nil {
		panic(err)
	}
	fmt.Printf("request-value=%s\n", read.Value)
	_, err = r.Cookie("missing")
	fmt.Printf("missing=%t\n", err == http.ErrNoCookie)
}
