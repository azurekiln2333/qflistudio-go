package main

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

type Entry struct {
	Name   string `json:"name"`
	Size   int    `json:"size"`
	Digest string `json:"sha256"`
}

func digest(text string) string { sum := sha256.Sum256([]byte(text)); return fmt.Sprintf("%x", sum) }
func main() {
	directory, err := os.MkdirTemp("", "qfli-package-")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(directory)
	for name, text := range map[string]string{"ok.txt": "ok", "changed.txt": "NEW!"} {
		if err = os.WriteFile(filepath.Join(directory, name), []byte(text), 0600); err != nil {
			panic(err)
		}
	}
	manifest := []Entry{{"ok.txt", 2, digest("ok")}, {"changed.txt", 3, digest("old")}, {"missing.txt", 1, digest("x")}}
	wire, err := json.Marshal(manifest)
	if err != nil {
		panic(err)
	}
	manifestPath := filepath.Join(directory, "manifest.json")
	if err = os.WriteFile(manifestPath, wire, 0600); err != nil {
		panic(err)
	}
	wire, err = os.ReadFile(manifestPath)
	if err != nil {
		panic(err)
	}
	var decoded []Entry
	if err = json.Unmarshal(wire, &decoded); err != nil {
		panic(err)
	}
	issues := []string{}
	for _, item := range decoded {
		if item.Name == "." || item.Name == ".." || filepath.Base(item.Name) != item.Name {
			issues = append(issues, item.Name+":name")
			continue
		}
		data, err := os.ReadFile(filepath.Join(directory, item.Name))
		if os.IsNotExist(err) {
			issues = append(issues, item.Name+":missing")
			continue
		}
		if err != nil {
			issues = append(issues, item.Name+":read")
			continue
		}
		if len(data) != item.Size {
			issues = append(issues, item.Name+":size")
		}
		if digest(string(data)) != item.Digest {
			issues = append(issues, item.Name+":digest")
		}
	}
	sort.Strings(issues)
	for _, issue := range issues {
		fmt.Println(issue)
	}
	fmt.Printf("issues=%d\n", len(issues))
}
