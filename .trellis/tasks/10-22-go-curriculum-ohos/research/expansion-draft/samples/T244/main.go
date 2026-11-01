package main

import (
	"bytes"
	"fmt"
	"text/template"
)

func render(t *template.Template, data map[string]string) (string, error) {
	var buffer bytes.Buffer
	if err := t.Execute(&buffer, data); err != nil {
		return "", err
	}
	return buffer.String(), nil
}
func main() {
	t, err := template.New("profile").Option("missingkey=error").Parse("name={{.name}} role={{.role}}")
	if err != nil {
		panic(err)
	}
	full, err := render(t, map[string]string{"name": "Li", "role": "reader"})
	if err != nil {
		panic(err)
	}
	fmt.Println(full)
	partial, err := render(t, map[string]string{"name": "Yu"})
	fmt.Printf("missing-rejected=%t\npartial-published=%t\n", err != nil, partial != "")
}
