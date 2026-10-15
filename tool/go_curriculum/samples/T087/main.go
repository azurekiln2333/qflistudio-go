// T087 bufio：按行/按词扫描与缓冲写。
//
// bufio.Scanner 把 Reader 包装成"按行/按词"的迭代器，内部用缓冲减少系统调用。
// 注意默认单行上限约 64KB，超长行需要 Buffer() 调大上限。
// 本示例按行与按词两种方式扫描同一段文本，统计结果确定。
package main

import (
	"bufio"
	"fmt"
	"strings"
)

func main() {
	const text = "go is fun\nbufio scans lines\nand words too\n"

	// 按行扫描。
	lineScan := bufio.NewScanner(strings.NewReader(text))
	lines := 0
	for lineScan.Scan() {
		lines++
		fmt.Printf("line %d: %s\n", lines, lineScan.Text())
	}
	fmt.Println("total lines:", lines)

	// 按词扫描：用 ScanWords 切分。
	wordScan := bufio.NewScanner(strings.NewReader(text))
	wordScan.Split(bufio.ScanWords)
	words := 0
	for wordScan.Scan() {
		words++
	}
	fmt.Println("total words:", words)
}
