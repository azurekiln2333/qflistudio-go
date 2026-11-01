package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"testing/fstest"
)

type Config struct {
	Port int `json:"port"`
}

func load(tree fs.FS, name string) (Config, error) {
	var cfg Config
	data, err := fs.ReadFile(tree, name)
	if err != nil {
		return cfg, err
	}
	err = json.Unmarshal(data, &cfg)
	return cfg, err
}
func main() {
	tree := fstest.MapFS{"defaults.json": &fstest.MapFile{Data: []byte(`{"port":8080}`)}, "profiles/dev/config.json": &fstest.MapFile{Data: []byte(`{"port":9090}`)}}
	defaults, err := load(tree, "defaults.json")
	if err != nil {
		panic(err)
	}
	sub, err := fs.Sub(tree, "profiles/dev")
	if err != nil {
		panic(err)
	}
	dev, err := load(sub, "config.json")
	if err != nil {
		panic(err)
	}
	fmt.Printf("default=%d dev=%d\n", defaults.Port, dev.Port)
	_, err = load(sub, "missing.json")
	fmt.Printf("missing=%t\n", errors.Is(err, fs.ErrNotExist))
}
