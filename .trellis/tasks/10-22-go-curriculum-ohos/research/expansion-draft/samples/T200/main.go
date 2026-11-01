package main

import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"
)

type Config struct {
	Name string
	Port int
	Tags []string
}

func patch(cfg *Config, text string) ([]string, error) {
	var fields map[string]json.RawMessage
	if err := json.Unmarshal([]byte(text), &fields); err != nil {
		return nil, err
	}
	keys := []string{}
	for key := range fields {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		if key != "name" && key != "port" && key != "tags" {
			return nil, fmt.Errorf("unknown key %s", key)
		}
	}
	candidate := *cfg
	candidate.Tags = append([]string(nil), cfg.Tags...)
	for _, key := range keys {
		raw := fields[key]
		switch key {
		case "name":
			if err := json.Unmarshal(raw, &candidate.Name); err != nil {
				return nil, err
			}
			if strings.TrimSpace(candidate.Name) == "" {
				return nil, fmt.Errorf("empty name")
			}
		case "port":
			if err := json.Unmarshal(raw, &candidate.Port); err != nil {
				return nil, err
			}
			if candidate.Port < 1 || candidate.Port > 65535 {
				return nil, fmt.Errorf("invalid port")
			}
		case "tags":
			if err := json.Unmarshal(raw, &candidate.Tags); err != nil {
				return nil, err
			}
		}
	}
	*cfg = candidate
	return keys, nil
}
func main() {
	cfg := Config{"local", 8080, []string{"old"}}
	keys, err := patch(&cfg, `{"port":9090,"name":"dev"}`)
	if err != nil {
		panic(err)
	}
	fmt.Printf("name=%s port=%d changed=%v\n", cfg.Name, cfg.Port, keys)
	_, err = patch(&cfg, `{"name":"broken","unknown":1}`)
	fmt.Printf("unknown=%t preserved=%t\n", err != nil, cfg.Name == "dev" && cfg.Port == 9090)
	_, err = patch(&cfg, `{"name":"changed","port":"bad"}`)
	fmt.Printf("bad-type=%t preserved=%t\n", err != nil, cfg.Name == "dev" && cfg.Port == 9090)
}
