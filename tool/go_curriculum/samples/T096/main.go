// T096 文本模板 text/template。
//
// text/template 用 {{.Field}} 占位符渲染结构化数据。模板可包含
// 条件 {{if}}、循环 {{range}}。本示例把渲染结果写入 bytes.Buffer，
// 再统一打印——不直接依赖 os.Stdout 捕获，输出因此确定、易测试。
package main

import (
	"bytes"
	"fmt"
	"text/template"
)

func main() {
	const tpl = `Inventory for {{.Owner}}:
{{range .Items}}- {{.Name}} x{{.Qty}} ({{if .InStock}}in stock{{else}}out of stock{{end}})
{{end}}Total lines: {{len .Items}}`

	data := struct {
		Owner string
		Items []struct {
			Name    string
			Qty     int
			InStock bool
		}
	}{
		Owner: "warehouse-a",
		Items: []struct {
			Name    string
			Qty     int
			InStock bool
		}{
			{"bolt", 100, true},
			{"nut", 0, false},
		},
	}

	t := template.Must(template.New("inv").Parse(tpl))

	// 渲染到内存缓冲，再打印，避免依赖底层 stdout 的捕获方式。
	var buf bytes.Buffer
	if err := t.Execute(&buf, data); err != nil {
		panic(err)
	}
	fmt.Println(buf.String())
}
