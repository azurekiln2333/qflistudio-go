package main

import (
	"bytes"
	"encoding/csv"
	"fmt"
	"strings"
)

func main() {
	records := [][]string{{"name", "address"}, {"Lin", "East, Road"}, {"Yu", "\"Suite\" 3\nFloor 2"}}
	var buffer bytes.Buffer
	writer := csv.NewWriter(&buffer)
	if err := writer.WriteAll(records); err != nil {
		panic(err)
	}
	decoded, err := csv.NewReader(strings.NewReader(buffer.String())).ReadAll()
	if err != nil {
		panic(err)
	}
	equal := len(decoded) == len(records)
	if equal {
		for i, row := range records {
			if len(decoded[i]) != len(row) {
				equal = false
				break
			}
			for j, value := range row {
				if decoded[i][j] != value {
					equal = false
				}
			}
		}
	}
	fmt.Printf("rows=%d roundtrip=%t\n", len(decoded)-1, equal)
	fmt.Printf("quotes-doubled=%t\n", strings.Contains(buffer.String(), `""Suite""`))
	fmt.Printf("line-preserved=%t\n", decoded[2][1] == "\"Suite\" 3\nFloor 2")
}
