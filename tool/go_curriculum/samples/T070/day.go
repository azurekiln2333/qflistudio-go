//go:generate go run gen_main.go

package main

// Day 是枚举类型；枚举值顺序即编号。
type Day int

const (
	Monday Day = iota
	Tuesday
	Wednesday
)
