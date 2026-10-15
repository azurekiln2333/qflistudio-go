// T086 文件读写：os.Open/Create 与缓冲。
//
// 本示例在系统临时目录里创建文件，写入内容后读回，最后清理。
// 使用 os.CreateTemp 得到唯一路径，避免污染工作目录；
// 关键习惯：写后 Close 才能保证数据落盘，读前也用 defer Close。
package main

import (
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	dir, err := os.MkdirTemp("", "qfli-t086-")
	if err != nil {
		panic(err)
	}
	// defer 保证函数退出时清理整个临时目录。
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "notes.txt")

	// 写入：os.Create 会截断或新建文件。
	f, err := os.Create(path)
	if err != nil {
		panic(err)
	}
	content := "line one\nline two\n"
	if _, err := f.WriteString(content); err != nil {
		f.Close()
		panic(err)
	}
	// Close 必须在再次打开前调用，否则缓冲/句柄状态不一致。
	if err := f.Close(); err != nil {
		panic(err)
	}

	// 读取：os.ReadFile 一次性读入。
	data, err := os.ReadFile(path)
	if err != nil {
		panic(err)
	}
	fmt.Println("read back:")
	fmt.Print(string(data))

	// 校验字节数，作为确定性断言。
	info, _ := os.Stat(path)
	fmt.Println("size matches:", int(info.Size()) == len(content))
}
