package main

import (
	"fmt"
)

type Change struct {
	Item  string
	Delta int
}

func transact(stock map[string]int, changes []Change) error {
	next := map[string]int{}
	for item, value := range stock {
		next[item] = value
	}
	for _, change := range changes {
		value, exists := next[change.Item]
		if !exists {
			return fmt.Errorf("unknown item")
		}
		value += change.Delta
		if value < 0 {
			return fmt.Errorf("negative stock")
		}
		next[change.Item] = value
	}
	for item, value := range next {
		stock[item] = value
	}
	return nil
}
func main() {
	stock := map[string]int{"pen": 10, "pad": 4}
	err := transact(stock, []Change{{"pen", -3}, {"pad", -9}})
	fmt.Printf("failed=%t pen=%d pad=%d\n", err != nil, stock["pen"], stock["pad"])
	err = transact(stock, []Change{{"pen", -3}, {"pad", 2}})
	fmt.Printf("committed=%t pen=%d pad=%d\n", err == nil, stock["pen"], stock["pad"])
}
