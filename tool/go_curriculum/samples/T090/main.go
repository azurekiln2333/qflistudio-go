// T090 JSON 二：struct tag、omitempty 与自定义名称。
//
// struct tag 控制 JSON 字段名、是否省略空值、是否忽略字段等。
// omitempty 在字段为零值时省略该键；"-" 表示完全忽略；自定义名字改变键名。
// 本示例展示三种行为，输出确定。
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

// Account 演示 tag 的常见用法。
type Account struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	Password string `json:"-"`                    // 永不序列化
	Email    string `json:"email,omitempty"`      // 空则省略
	Nickname string `json:"nick_name,omitempty"`  // 改名 + 空则省略
	Balance  int    `json:"balance"`              // 零值也保留
}

func main() {
	a := Account{ID: 7, Name: "alice"}
	data, _ := json.Marshal(a)
	fmt.Println("minimal:", string(data))

	// 填入可选字段后，omitempty 的键出现。
	a.Email = "alice@example.com"
	a.Nickname = "ali"
	a.Balance = 100
	data2, _ := json.Marshal(a)
	fmt.Println("filled: ", string(data2))

	// Password 设为非空也永远不会出现在 JSON 中。
	a.Password = "secret"
	data3, _ := json.Marshal(a)
	fmt.Println("password hidden:", !strings.Contains(string(data3), "secret"))
}
