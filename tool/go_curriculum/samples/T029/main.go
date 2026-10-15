package main

import "fmt"

func byValue(n int)  { n = 100 }
func byPtr(n *int)   { *n = 100 }

func main() {
	x := 1
	byValue(x)
	fmt.Println("after byValue", x)
	byPtr(&x)
	fmt.Println("after byPtr", x)
	fmt.Printf("address of x is non-nil: %t\n", &x != nil)
}
