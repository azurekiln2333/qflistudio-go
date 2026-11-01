package main

import (
	"fmt"
	"sort"
)

type Key struct {
	Warehouse string
	Product   string
}
type Stock struct {
	Key      Key
	Quantity int
}

func aggregate(rows []Stock) (map[Key]int, error) {
	totals := map[Key]int{}
	for _, row := range rows {
		if row.Quantity < 0 {
			return nil, fmt.Errorf("negative inventory")
		}
		totals[row.Key] += row.Quantity
	}
	return totals, nil
}
func main() {
	totals, err := aggregate([]Stock{{Key{"A", "pen"}, 2}, {Key{"A", "pen"}, 1}, {Key{"A", "book"}, 9}, {Key{"B", "pen"}, 1}, {Key{"B", "book"}, 2}})
	if err != nil {
		panic(err)
	}
	low := []Key{}
	for key, quantity := range totals {
		if quantity < 4 {
			low = append(low, key)
		}
	}
	sort.Slice(low, func(i, j int) bool {
		if low[i].Warehouse != low[j].Warehouse {
			return low[i].Warehouse < low[j].Warehouse
		}
		return low[i].Product < low[j].Product
	})
	for _, key := range low {
		fmt.Printf("%s/%s=%d\n", key.Warehouse, key.Product, totals[key])
	}
}
