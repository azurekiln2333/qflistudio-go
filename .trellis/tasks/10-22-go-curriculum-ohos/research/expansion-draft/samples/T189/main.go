package main

import (
	"fmt"
	"path"
	"strings"
)

func category(name string) string {
	base := path.Base(name)
	if strings.HasPrefix(base, ".") && strings.Count(base, ".") == 1 {
		return "dotfile"
	}
	switch strings.ToLower(path.Ext(base)) {
	case ".go":
		return "go"
	case ".json":
		return "json"
	case ".gz", ".zip":
		return "compressed"
	case "":
		return "plain"
	default:
		return "unknown"
	}
}
func main() {
	for _, name := range []string{"main.GO", "archive.tar.gz", ".gitignore", ".config.json", "README", "name."} {
		fmt.Printf("%s=%s\n", name, category(name))
	}
}
