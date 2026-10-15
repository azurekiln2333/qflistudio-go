package main

import (
	"fmt"
	"sort"
)

type person struct {
	Name string
	Age  int
}

func main() {
	people := []person{
		{"Bob", 30},
		{"Al", 25},
		{"Cy", 25},
	}
	sort.Slice(people, func(i, j int) bool {
		if people[i].Age != people[j].Age {
			return people[i].Age < people[j].Age
		}
		return people[i].Name < people[j].Name
	})
	fmt.Println(people)
}
