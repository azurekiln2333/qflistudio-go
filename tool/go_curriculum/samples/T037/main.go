package main

import "fmt"

type user struct {
	Name string
	Age  int
}

func main() {
	u := user{"Ada", 36}          // 位置字面量
	v := user{Name: "Bob"}        // 键值字面量，未写的字段为零值
	fmt.Println(u.Name, u.Age)
	fmt.Println(v.Name, v.Age)
	// 指针字段访问自动解引用
	p := &u
	p.Age = 37
	fmt.Println("pointer set", u.Age)
}
