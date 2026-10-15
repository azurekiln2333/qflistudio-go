package main

import "fmt"

type point struct {
	X int
	Y int
}

func main() {
	p := point{X: 3, Y: 4}
	fmt.Printf("v=%v +v=%+v\n", p, p)
	fmt.Printf("d=%d q=%q t=%T\n", 42, "go", p)
	fmt.Printf("f=%.2f e=%e\n", 3.14159, 1234.5)
}
