package main

import "fmt"

func process(items []int) (err string) {
	for _, v := range items {
		if v < 0 {
			err = "negative input"
			goto cleanup
		}
	}
	fmt.Println("processed", len(items), "items")
cleanup:
	if err != "" {
		fmt.Println("cleanup after:", err)
	}
	return err
}

func main() {
	process([]int{1, 2, 3})
	process([]int{1, -2})
}
