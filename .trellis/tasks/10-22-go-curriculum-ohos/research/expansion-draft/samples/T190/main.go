package main

import (
	"fmt"
	"io/fs"
)

func permissions(mode fs.FileMode) string {
	result := []byte("---------")
	symbols := "rwxrwxrwx"
	for i := 0; i < 9; i++ {
		if mode.Perm()&(1<<uint(8-i)) != 0 {
			result[i] = symbols[i]
		}
	}
	return string(result)
}
func main() {
	for _, item := range []struct {
		Name string
		Mode fs.FileMode
	}{{"file", 0640}, {"directory", fs.ModeDir | 0750}, {"special", fs.ModeSetuid | 0755}} {
		fmt.Printf("%s perms=%s dir=%t setuid=%t\n", item.Name, permissions(item.Mode), item.Mode&fs.ModeDir != 0, item.Mode&fs.ModeSetuid != 0)
	}
}
