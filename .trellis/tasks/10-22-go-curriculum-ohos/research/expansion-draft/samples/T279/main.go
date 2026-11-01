package main

import (
	"encoding/json"
	"fmt"
)

type Checkpoint struct {
	Next int `json:"next"`
}

func main() {
	records := []string{"A", "B", "C", "D", "E"}
	committed := []string{}
	checkpoint := Checkpoint{}
	wire := []byte{}
	failOnce := true
	for checkpoint.Next < len(records) {
		start := checkpoint.Next
		end := start + 2
		if end > len(records) {
			end = len(records)
		}
		pending := append([]string(nil), records[start:end]...)
		if start == 2 && failOnce {
			failOnce = false
			fmt.Printf("failed-at=%d\n", start)
			if err := json.Unmarshal(wire, &checkpoint); err != nil {
				panic(err)
			}
			continue
		}
		committed = append(committed, pending...)
		checkpoint.Next = end
		var err error
		wire, err = json.Marshal(checkpoint)
		if err != nil {
			panic(err)
		}
	}
	fmt.Printf("committed=%v\ncheckpoint=%s\n", committed, wire)
}
