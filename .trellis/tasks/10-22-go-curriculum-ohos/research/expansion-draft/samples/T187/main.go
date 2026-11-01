package main

import (
	"crypto/sha256"
	"fmt"
	"sort"
)

func main() {
	files := map[string][]byte{"a.txt": []byte("same"), "nested/b.txt": []byte("same"), "unique.txt": []byte("unique"), "c.bin": []byte("other"), "d.bin": []byte("other")}
	index := map[[32]byte][]string{}
	for name, data := range files {
		digest := sha256.Sum256(data)
		index[digest] = append(index[digest], name)
	}
	groups := [][]string{}
	for _, names := range index {
		if len(names) > 1 {
			sort.Strings(names)
			groups = append(groups, names)
		}
	}
	sort.Slice(groups, func(i, j int) bool { return groups[i][0] < groups[j][0] })
	for _, names := range groups {
		fmt.Printf("duplicate=%v\n", names)
	}
	fmt.Printf("groups=%d\n", len(groups))
}
