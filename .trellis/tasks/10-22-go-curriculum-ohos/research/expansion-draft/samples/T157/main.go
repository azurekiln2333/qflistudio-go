package main

import (
	"fmt"
	"sort"
)

type Interval struct {
	Start int
	End   int
}

func merge(input []Interval) ([]Interval, error) {
	intervals := append([]Interval(nil), input...)
	for _, item := range intervals {
		if item.Start >= item.End {
			return nil, fmt.Errorf("invalid interval")
		}
	}
	sort.Slice(intervals, func(i, j int) bool {
		if intervals[i].Start != intervals[j].Start {
			return intervals[i].Start < intervals[j].Start
		}
		return intervals[i].End < intervals[j].End
	})
	result := []Interval{}
	for _, item := range intervals {
		if len(result) == 0 || item.Start > result[len(result)-1].End {
			result = append(result, item)
			continue
		}
		if item.End > result[len(result)-1].End {
			result[len(result)-1].End = item.End
		}
	}
	return result, nil
}
func main() {
	input := []Interval{{5, 7}, {1, 3}, {3, 4}, {10, 12}, {6, 8}}
	result, err := merge(input)
	if err != nil {
		panic(err)
	}
	for i, item := range result {
		if i > 0 {
			fmt.Print(" ")
		}
		fmt.Printf("[%d,%d)", item.Start, item.End)
	}
	fmt.Println()
	fmt.Printf("input-preserved=%t\n", input[0].Start == 5)
	_, err = merge([]Interval{{4, 2}})
	fmt.Printf("invalid=%t\n", err != nil)
}
