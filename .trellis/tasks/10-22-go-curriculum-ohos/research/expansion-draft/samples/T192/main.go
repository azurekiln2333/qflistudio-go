package main

import (
	"fmt"
	"strconv"
	"strings"
)

type Config struct {
	Port  int
	Label string
}

func load(environment []string) (Config, error) {
	values := map[string]string{}
	for _, entry := range environment {
		key, value, ok := strings.Cut(entry, "=")
		if !ok || key == "" {
			return Config{}, fmt.Errorf("bad environment entry")
		}
		values[key] = value
	}
	cfg := Config{Port: 8080, Label: "default"}
	if value, exists := values["APP_PORT"]; exists {
		port, err := strconv.Atoi(value)
		if err != nil || port < 1 || port > 65535 {
			return Config{}, fmt.Errorf("invalid port")
		}
		cfg.Port = port
	}
	if value, exists := values["APP_LABEL"]; exists {
		cfg.Label = value
	}
	return cfg, nil
}
func main() {
	cfg, err := load([]string{"APP_PORT=9000", "APP_LABEL=a=b", "APP_PORT=9100"})
	if err != nil {
		panic(err)
	}
	defaults, err := load(nil)
	if err != nil {
		panic(err)
	}
	fmt.Printf("port=%d label=%s default=%d\n", cfg.Port, cfg.Label, defaults.Port)
	_, err = load([]string{"APP_PORT=no"})
	fmt.Printf("bad-integer=%t\n", err != nil)
}
