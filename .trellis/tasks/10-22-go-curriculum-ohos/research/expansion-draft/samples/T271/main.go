package main

import (
	"encoding/csv"
	"fmt"
	"sort"
	"strconv"
	"strings"
)

func ledger(text string) (map[string]int, map[string]bool) {
	rows, err := csv.NewReader(strings.NewReader(text)).ReadAll()
	if err != nil {
		panic(err)
	}
	values := map[string]int{}
	duplicates := map[string]bool{}
	for _, row := range rows[1:] {
		if len(row) != 2 {
			panic("bad columns")
		}
		amount, err := strconv.Atoi(row[1])
		if err != nil {
			panic(err)
		}
		if _, exists := values[row[0]]; exists {
			duplicates[row[0]] = true
		} else {
			values[row[0]] = amount
		}
	}
	return values, duplicates
}
func main() {
	left, ld := ledger("id,cents\nt1,100\nt2,200\nt3,300\n")
	right, rd := ledger("id,cents\nt1,110\nt2,200\nt2,200\nt4,400\n")
	set := map[string]bool{}
	for id := range left {
		set[id] = true
	}
	for id := range right {
		set[id] = true
	}
	ids := []string{}
	for id := range set {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	for _, id := range ids {
		a, hasA := left[id]
		b, hasB := right[id]
		if ld[id] {
			fmt.Printf("%s duplicate-left\n", id)
		}
		if rd[id] {
			fmt.Printf("%s duplicate-right\n", id)
		}
		switch {
		case !hasA:
			fmt.Printf("%s missing-left\n", id)
		case !hasB:
			fmt.Printf("%s missing-right\n", id)
		case a != b:
			fmt.Printf("%s mismatch=%d/%d\n", id, a, b)
		}
	}
}
