package main

import "fmt"

func main() {
	grid := [][]int{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}
	target := 5
	found := false
search:
	for i, row := range grid {
		for j, v := range row {
			if v == target {
				fmt.Printf("found at %d,%d\n", i, j)
				found = true
				break search
			}
		}
	}
	if !found {
		fmt.Println("not found")
	}
}
