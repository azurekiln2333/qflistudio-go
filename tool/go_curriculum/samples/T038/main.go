package main

import "fmt"

type base struct {
	ID int
}

func (b base) describe() string { return fmt.Sprintf("base#%d", b.ID) }

type derived struct {
	base // 嵌入：字段与方法被提升
	Name string
}

func main() {
	d := derived{base{ID: 7}, "child"}
	fmt.Println(d.ID)         // 提升字段
	fmt.Println(d.describe()) // 提升方法
	fmt.Println(d.Name)
}
