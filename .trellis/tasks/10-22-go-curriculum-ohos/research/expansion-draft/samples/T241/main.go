package main

import (
	"bytes"
	"fmt"
	"text/template"
)

type Item struct {
	Name      string
	Qty, Unit int
}
type Report struct {
	Items []Item
	Total int
}

func money(cents int) string { return fmt.Sprintf("%d.%02d", cents/100, cents%100) }
func main() {
	report := Report{Items: []Item{{"pen", 2, 139}, {"pad", 1, 50}}}
	for _, item := range report.Items {
		report.Total += item.Qty * item.Unit
	}
	source := "{{range .Items}}{{.Name}} {{.Qty}} x {{money .Unit}}\n{{end}}total {{money .Total}}\n"
	t, err := template.New("invoice").Funcs(template.FuncMap{"money": money}).Parse(source)
	if err != nil {
		panic(err)
	}
	var out bytes.Buffer
	if err = t.Execute(&out, report); err != nil {
		panic(err)
	}
	fmt.Print(out.String())
}
