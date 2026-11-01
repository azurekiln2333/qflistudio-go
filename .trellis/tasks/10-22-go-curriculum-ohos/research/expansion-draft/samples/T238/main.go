package main

import (
	"errors"
	"fmt"
	"sort"
	"sync"
)

type Result struct {
	Index int
	Value int
	Err   error
}

func main() {
	input := []int{4, -2, 0, 7}
	out := make(chan Result, len(input))
	var workers sync.WaitGroup
	for index, value := range input {
		workers.Add(1)
		go func(index, value int) {
			defer workers.Done()
			r := Result{Index: index, Value: value * 2}
			if value <= 0 {
				r.Err = errors.New("must be positive")
			}
			out <- r
		}(index, value)
	}
	workers.Wait()
	close(out)
	rows := []Result{}
	for r := range out {
		rows = append(rows, r)
	}
	sort.Slice(rows, func(i, j int) bool { return rows[i].Index < rows[j].Index })
	failures := 0
	for _, r := range rows {
		if r.Err != nil {
			failures++
			fmt.Printf("%d:error=%s\n", r.Index, r.Err)
		} else {
			fmt.Printf("%d:value=%d\n", r.Index, r.Value)
		}
	}
	fmt.Printf("failures=%d\n", failures)
}
