package main

import (
	"bytes"
	"fmt"
	"text/template"
)

type Row struct {
	Name  string
	Count int
}
type Report struct {
	Title string
	Rows  []Row
}

func main() {
	source := `{{define "header"}}REPORT {{.}}{{end}}{{define "row"}}{{.Name}}={{.Count}}{{end}}{{define "report"}}{{template "header" .Title}}:{{range .Rows}} [{{template "row" .}}]{{end}}{{end}}`
	t, err := template.New("root").Parse(source)
	if err != nil {
		panic(err)
	}
	for _, report := range []Report{{"north", []Row{{"books", 3}, {"pens", 5}}}, {"south", []Row{{"books", 2}}}} {
		var out bytes.Buffer
		if err := t.ExecuteTemplate(&out, "report", report); err != nil {
			panic(err)
		}
		fmt.Println(out.String())
	}
}
