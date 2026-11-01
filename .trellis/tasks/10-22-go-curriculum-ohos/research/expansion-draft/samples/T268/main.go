package main

import (
	"fmt"
	"math/bits"
)

func names(set uint64) []string {
	all := []string{"read", "write", "export", "admin"}
	out := []string{}
	for i, name := range all {
		if set&(uint64(1)<<uint(i)) != 0 {
			out = append(out, name)
		}
	}
	return out
}
func main() {
	user := uint64(1<<0 | 1<<1 | 1<<2)
	policy := uint64(1<<0 | 1<<2 | 1<<3)
	intersection := user & policy
	union := user | policy
	removed := user &^ policy
	fmt.Printf("allowed=%v\nunion-count=%d\nremoved=%v\n", names(intersection), bits.OnesCount64(union), names(removed))
	grant := intersection &^ (uint64(1) << 2)
	fmt.Printf("after-revoke=%v\n", names(grant))
}
