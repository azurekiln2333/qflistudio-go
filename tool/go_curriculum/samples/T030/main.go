package main

import "fmt"

func addOneSlice(s []int) { // 修改元素可见
	if len(s) > 0 {
		s[0]++
	}
}

func reassignSlice(s []int) { // 重新赋值切片头，外部不可见
	s = append(s, 999)
	_ = s
}

func main() {
	s := []int{1, 2, 3}
	addOneSlice(s)
	fmt.Println("after element change", s)
	reassignSlice(s)
	fmt.Println("after reassign", s)

	p := new(int) // new 返回指向零值的指针
	*p = 7
	fmt.Println("new value", *p)
}
