package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

func digest(text string) string {
	sum := sha256.Sum256([]byte(text))
	return hex.EncodeToString(sum[:])
}
func validDigest(text string) bool {
	decoded, err := hex.DecodeString(text)
	return err == nil && len(decoded) == sha256.Size
}
func main() {
	directory, err := os.MkdirTemp("", "qfli-integrity-")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(directory)
	for name, text := range map[string]string{"a.txt": "alpha", "b.txt": "changed"} {
		if err = os.WriteFile(filepath.Join(directory, name), []byte(text), 0600); err != nil {
			panic(err)
		}
	}
	manifest := map[string]string{"a.txt": digest("alpha"), "b.txt": digest("beta")}
	names := []string{}
	for name := range manifest {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		if !validDigest(manifest[name]) {
			panic("invalid manifest digest")
		}
		data, err := os.ReadFile(filepath.Join(directory, name))
		if err != nil && !os.IsNotExist(err) {
			panic(err)
		}
		exists := err == nil
		fmt.Printf("%s exists=%t match=%t\n", name, exists, exists && digest(string(data)) == manifest[name])
	}
	fmt.Printf("bad-manifest=%t\n", !validDigest("xyz"))
}
