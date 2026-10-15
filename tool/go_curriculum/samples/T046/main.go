// T046 排序与比较：sort.Interface 实现。
//
// sort.Interface 要求三个方法：Len、Less、Swap。实现它即可用 sort.Sort
// 排序任意集合。Less 决定顺序，Swap 决定交换方式。
package main

import (
	"fmt"
	"sort"
)

// Person 是要排序的元素。
type Person struct {
	Name string
	Age  int
}

// ByAge 是 []Person 的排序视图：先按年龄，年龄相同按名字。
type ByAge []Person

func (p ByAge) Len() int      { return len(p) }
func (p ByAge) Swap(i, j int) { p[i], p[j] = p[j], p[i] }
func (p ByAge) Less(i, j int) bool {
	if p[i].Age != p[j].Age {
		return p[i].Age < p[j].Age
	}
	return p[i].Name < p[j].Name
}

func main() {
	people := []Person{
		{"carol", 30},
		{"alice", 25},
		{"bob", 30},
		{"dave", 20},
	}

	// sort.Sort 会读取 Len/Less/Swap 完成排序。
	sort.Sort(ByAge(people))
	for _, p := range people {
		fmt.Printf("%-6s %d\n", p.Name, p.Age)
	}

	// 用 sort.Sort(sort.Reverse(...)) 得到逆序。
	sort.Sort(sort.Reverse(ByAge(people)))
	fmt.Println("reversed first:", people[0].Name)
}
