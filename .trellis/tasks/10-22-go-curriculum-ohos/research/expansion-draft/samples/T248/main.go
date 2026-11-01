package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
)

type Row struct {
	ID    int    `json:"id"`
	Value string `json:"value"`
}

func main() {
	var source bytes.Buffer
	encoder := json.NewEncoder(&source)
	for _, row := range []Row{{1, "a"}, {2, "b"}} {
		if err := encoder.Encode(row); err != nil {
			panic(err)
		}
	}
	source.WriteString("{broken}\n")
	if err := encoder.Encode(Row{3, "c"}); err != nil {
		panic(err)
	}
	scanner := bufio.NewScanner(&source)
	line := 0
	valid := 0
	for scanner.Scan() {
		line++
		var row Row
		if err := json.Unmarshal(scanner.Bytes(), &row); err != nil {
			fmt.Printf("line=%d invalid\n", line)
			continue
		}
		valid++
		fmt.Printf("id=%d value=%s\n", row.ID, row.Value)
	}
	if err := scanner.Err(); err != nil {
		panic(err)
	}
	fmt.Printf("valid=%d\n", valid)
}
