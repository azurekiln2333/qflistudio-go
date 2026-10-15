package main

import "fmt"

type person struct {
	Name string
	Age  int
}

func main() {
	p := new(person) // 指向零值结构体的指针
	p.Name = "Ada"
	fmt.Println(*p)

	q := &person{Name: "Bob", Age: 30} // 取址字面量
	fmt.Println(q.Age)

	r := person{Name: "Cy"}
	modify(&r)
	fmt.Println(r.Name)
}

func modify(p *person) { p.Name = "Modified" }
