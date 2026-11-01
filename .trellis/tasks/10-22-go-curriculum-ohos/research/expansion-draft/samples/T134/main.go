package main

import (
	"encoding/json"
	"fmt"
	"io"
	"strings"
)

type Config struct {
	Name    string `json:"name"`
	Timeout int    `json:"timeout"`
	Enabled bool   `json:"enabled"`
}

func load(text string) (Config, error) {
	cfg := Config{Name: "default", Timeout: 3, Enabled: true}
	decoder := json.NewDecoder(strings.NewReader(text))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&cfg); err != nil {
		return cfg, err
	}
	var extra interface{}
	if err := decoder.Decode(&extra); err != io.EOF {
		if err == nil {
			err = fmt.Errorf("second JSON value")
		}
		return cfg, err
	}
	return cfg, nil
}

func main() {
	cfg, err := load(`{"name":"local","enabled":false}`)
	if err != nil {
		panic(err)
	}
	fmt.Printf("name=%s timeout=%d enabled=%t\n", cfg.Name, cfg.Timeout, cfg.Enabled)
	_, err = load(`{"timeuot":8}`)
	fmt.Printf("unknown=%t\n", err != nil)
	_, err = load(`{} {}`)
	fmt.Printf("trailing=%t\n", err != nil)
}
