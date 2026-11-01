package main

import (
	"archive/zip"
	"fmt"
	"os"
	"path"
	"strings"
)

func safe(h *zip.FileHeader) bool {
	name := h.Name
	if name == "" || strings.Contains(name, "\\") || strings.Contains(name, ":") || path.IsAbs(name) || h.Mode()&os.ModeSymlink != 0 {
		return false
	}
	clean := path.Clean(name)
	return clean != "." && clean != ".." && !strings.HasPrefix(clean, "../")
}
func main() {
	for _, name := range []string{"docs/a.txt", "../escape", "/etc/file", "C:/file", "docs\\..\\escape"} {
		h := &zip.FileHeader{Name: name}
		fmt.Printf("%s=%t\n", name, safe(h))
	}
	link := &zip.FileHeader{Name: "docs/link"}
	link.SetMode(os.ModeSymlink | 0600)
	fmt.Printf("symlink=%t\n", safe(link))
}
