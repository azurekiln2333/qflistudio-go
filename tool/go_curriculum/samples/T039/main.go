package main

import "fmt"

type counter struct {
	n int
}

func (c counter) value() int { return c.n } // 值接收者：拷贝
func (c *counter) inc()      { c.n++ }      // 指针接收者：可修改

func main() {
	c := counter{}
	c.inc()
	c.inc()
	fmt.Println("count", c.value())
	// 值接收者方法作用在副本上，不影响原值
	cp := c
	cp.inc()
	fmt.Println("after copy inc:", c.n, cp.n)
}
