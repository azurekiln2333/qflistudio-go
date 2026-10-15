package main

import "fmt"

type Weekday int

const (
	Sunday Weekday = iota
	Monday
	Tuesday
)

func main() {
	fmt.Println(int(Sunday), int(Monday), int(Tuesday))
	const pi = 3.14159 // 无类型常量，使用时才确定类型
	var f float64 = pi
	fmt.Printf("pi as float64 = %.2f\n", f)
}
