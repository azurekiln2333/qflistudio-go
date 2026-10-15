// T088 目录遍历与文件信息。
//
// os.ReadDir 返回目录条目并按文件名排序，因此输出天然确定。
// 用 FileInfo 可拿到名称、大小、是否为目录等元数据。
//
// 注意：目录条目的 Size() 是**文件系统相关**的值（Linux 上常见 4096，
// Windows 上常见 0），不能作为确定性输出。因此本示例对目录只打印类型，
// 只对普通文件打印大小——这样跨平台输出一致。
package main

import (
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	dir, err := os.MkdirTemp("", "qfli-t088-")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(dir)

	// 建两个文件和一个子目录，用于演示“是否目录”的判断。
	mustWrite(filepath.Join(dir, "alpha.txt"), "a")
	mustWrite(filepath.Join(dir, "beta.txt"), "bb")
	if err := os.Mkdir(filepath.Join(dir, "sub"), 0o755); err != nil {
		panic(err)
	}

	entries, err := os.ReadDir(dir)
	if err != nil {
		panic(err)
	}
	// ReadDir 已按名字排序：alpha.txt, beta.txt, sub。
	for _, e := range entries {
		if e.IsDir() {
			// 目录不打印易变的 size。
			fmt.Printf("%-10s dir\n", e.Name())
			continue
		}
		info, err := e.Info()
		if err != nil {
			panic(err)
		}
		fmt.Printf("%-10s file size=%d\n", e.Name(), info.Size())
	}
}

func mustWrite(path, content string) {
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		panic(err)
	}
}
