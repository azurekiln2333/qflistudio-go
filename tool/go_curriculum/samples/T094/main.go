// T094 正则一：regexp 匹配与子匹配。
//
// regexp.MustCompile 在正则非法时 panic，适合包级常量；FindStringSubmatch
// 返回整体匹配与各捕获组。本示例从固定字符串中提取结构化字段，输出确定。
package main

import (
	"fmt"
	"regexp"
)

func main() {
	// 匹配形如 "key=value" 的日志片段，捕获 key 与 value。
	re := regexp.MustCompile(`(\w+)=(\w+)`)

	line := "user=alice role=admin active=true"
	// 找出所有匹配。
	all := re.FindAllStringSubmatch(line, -1)
	fmt.Println("matches:", len(all))
	for _, m := range all {
		// m[0] 是整体，m[1]/m[2] 是捕获组。
		fmt.Printf("  key=%-8s value=%s\n", m[1], m[2])
	}

	// 单个匹配。
	one := re.FindStringSubmatch("host=node1")
	fmt.Println("single full match:", one[0])
	fmt.Println("single group1:", one[1])
	fmt.Println("single group2:", one[2])

	// 无匹配时返回 nil；这里做存在性判断。
	fmt.Println("no match is nil:", re.FindStringSubmatch("nokv") == nil)
}
