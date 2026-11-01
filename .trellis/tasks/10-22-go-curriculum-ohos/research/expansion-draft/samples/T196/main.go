package main

import (
	"fmt"
	"strings"
	"time"
)

type Config struct {
	Port        int
	Timeout     time.Duration
	TLS         bool
	Certificate string
	Key         string
}

func validate(cfg Config) []string {
	issues := []string{}
	if cfg.Port < 1 || cfg.Port > 65535 {
		issues = append(issues, "port must be 1..65535")
	}
	if cfg.Timeout <= 0 {
		issues = append(issues, "timeout must be positive")
	}
	if cfg.TLS && (cfg.Certificate == "" || cfg.Key == "") {
		issues = append(issues, "tls requires certificate and key")
	}
	if !cfg.TLS && (cfg.Certificate != "" || cfg.Key != "") {
		issues = append(issues, "tls paths require tls enabled")
	}
	return issues
}
func main() {
	bad := Config{Port: 70000, TLS: true, Certificate: "cert.pem"}
	fmt.Printf("errors=%s\n", strings.Join(validate(bad), " | "))
	good := Config{443, 2 * time.Second, true, "cert.pem", "key.pem"}
	fmt.Printf("valid=%t\n", len(validate(good)) == 0)
}
