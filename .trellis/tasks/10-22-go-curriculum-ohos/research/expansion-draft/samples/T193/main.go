package main

import (
	"encoding/json"
	"fmt"
)

type Config struct {
	Port  int
	Debug bool
}

func apply(cfg *Config, sources map[string]string, origin, text string) error {
	var fields map[string]json.RawMessage
	if err := json.Unmarshal([]byte(text), &fields); err != nil {
		return err
	}
	candidate := *cfg
	for name, raw := range fields {
		switch name {
		case "port":
			if err := json.Unmarshal(raw, &candidate.Port); err != nil {
				return err
			}
			if candidate.Port < 1 || candidate.Port > 65535 {
				return fmt.Errorf("invalid port")
			}
		case "debug":
			if err := json.Unmarshal(raw, &candidate.Debug); err != nil {
				return err
			}
		default:
			return fmt.Errorf("unknown field")
		}
	}
	*cfg = candidate
	for name := range fields {
		sources[name] = origin
	}
	return nil
}
func main() {
	cfg := Config{8080, false}
	sources := map[string]string{"port": "default", "debug": "default"}
	for _, layer := range []struct {
		Name string
		JSON string
	}{{"file", `{"port":7000,"debug":true}`}, {"environment", `{"port":9000}`}, {"cli", `{"debug":false}`}} {
		if err := apply(&cfg, sources, layer.Name, layer.JSON); err != nil {
			panic(err)
		}
	}
	fmt.Printf("port=%d source=%s\ndebug=%t source=%s\n", cfg.Port, sources["port"], cfg.Debug, sources["debug"])
}
