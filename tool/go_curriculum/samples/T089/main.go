// T089 JSON 一：Marshal/Unmarshal 基础。
//
// encoding/json 在 Go 值与 JSON 文本之间转换。Marshal 把结构体转成 JSON
// 字节；Unmarshal 把 JSON 解析回结构体。结构体字段必须是导出的（首字母大写）
// 才会被编码，否则会被忽略。
package main

import (
	"encoding/json"
	"fmt"
)

// Profile 是要被编解码的结构体。字段都导出。
type Profile struct {
	Name    string   `json:"name"`
	Age     int      `json:"age"`
	Hobbies []string `json:"hobbies"`
}

func main() {
	p := Profile{
		Name:    "gopher",
		Age:     15,
		Hobbies: []string{"coding", "reading"},
	}

	// 结构体 -> JSON。
	data, err := json.Marshal(p)
	if err != nil {
		panic(err)
	}
	fmt.Println("marshal:", string(data))

	// JSON -> 结构体。
	var back Profile
	if err := json.Unmarshal(data, &back); err != nil {
		panic(err)
	}
	fmt.Println("unmarshal name:", back.Name)
	fmt.Println("unmarshal age:", back.Age)
	fmt.Println("unmarshal hobbies:", back.Hobbies)

	// 往返一致：编码再解码应得到相等结构（切片需用元素比较）。
	again, _ := json.Marshal(back)
	fmt.Println("round-trip stable:", string(again) == string(data))
}
