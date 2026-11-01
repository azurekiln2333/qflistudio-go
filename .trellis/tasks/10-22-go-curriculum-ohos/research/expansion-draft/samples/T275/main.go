package main

import (
	"fmt"
	"sort"
	"strings"
)

type Order struct {
	Department, State string
	Cents             int
}
type Total struct{ Count, Cents int }

func main() {
	orders := []Order{{"North", "paid", 1200}, {"south", "paid", 900}, {"north", "draft", 300}, {"NORTH", "paid", 700}, {"south", "paid", 100}}
	groups := map[string]Total{}
	for _, order := range orders {
		if order.State != "paid" || order.Cents < 500 {
			continue
		}
		key := strings.ToLower(order.Department)
		total := groups[key]
		total.Count++
		total.Cents += order.Cents
		groups[key] = total
	}
	names := []string{}
	for name := range groups {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		total := groups[name]
		fmt.Printf("%s count=%d cents=%d\n", name, total.Count, total.Cents)
	}
}
