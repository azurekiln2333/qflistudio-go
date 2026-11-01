package main

import (
	"bytes"
	"fmt"
	"html/template"
	"strings"
)

func main() {
	t, err := template.New("message").Parse(`<p title="{{.}}">{{.}}</p>`)
	if err != nil {
		panic(err)
	}
	var out bytes.Buffer
	if err = t.Execute(&out, `<b>"x"</b>`); err != nil {
		panic(err)
	}
	html := out.String()
	fmt.Printf("escaped-tags=%t\nescaped-quotes=%t\nraw-tag-absent=%t\n", strings.Contains(html, "&lt;b&gt;"), strings.Contains(html, "&#34;"), !strings.Contains(html, "<b>"))
}
