package main

import (
	"encoding/json"
	"fmt"
	"io"
	"mime"
	"net/http"
	"net/http/httptest"
	"strings"
)

type Input struct {
	Name string `json:"name"`
}

func post(w http.ResponseWriter, r *http.Request) {
	media, _, err := mime.ParseMediaType(r.Header.Get("Content-Type"))
	if err != nil || media != "application/json" {
		http.Error(w, "media", 415)
		return
	}
	decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 128))
	decoder.DisallowUnknownFields()
	var input Input
	if err = decoder.Decode(&input); err != nil {
		http.Error(w, "json", 400)
		return
	}
	var tail interface{}
	if decoder.Decode(&tail) != io.EOF || input.Name == "" {
		http.Error(w, "payload", 400)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(input)
}
func main() {
	for _, item := range []struct{ media, body string }{{"application/json", `{"name":"Li"}`}, {"application/json", `{"name":"Li","admin":true}`}, {"application/json", `{"name":"Li"}{}`}, {"text/plain", `{"name":"Li"}`}} {
		r := httptest.NewRequest("POST", "/profile", strings.NewReader(item.body))
		r.Header.Set("Content-Type", item.media)
		w := httptest.NewRecorder()
		post(w, r)
		fmt.Println(w.Code)
	}
}
