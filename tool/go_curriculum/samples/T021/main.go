package main

import "fmt"

func main() {
	s := []int{1, 2, 3, 4, 5}
	// copy 到等长目标
	dst := make([]int, len(s))
	n := copy(dst, s)
	fmt.Println("copied", n, dst)
	// 删除索引 2；append 会就地覆盖共享数组，s 本身也被改动
	del := append(s[:2], s[3:]...)
	fmt.Println("after delete", del, "s mutated to", s)
	// 去重
	seen := map[int]bool{}
	uniq := s[:0:0]
	for _, v := range []int{1, 1, 2, 3, 3, 3} {
		if !seen[v] {
			seen[v] = true
			uniq = append(uniq, v)
		}
	}
	fmt.Println("unique", uniq)
}
