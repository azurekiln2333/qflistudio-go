package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"strconv"
	"strings"
)

func total(text string) (int64, int, int, error) {
	reader := csv.NewReader(strings.NewReader(text))
	header, err := reader.Read()
	if err != nil {
		return 0, 0, 0, err
	}
	columns := map[string]int{}
	for i, name := range header {
		columns[name] = i
	}
	quantity, hasQuantity := columns["quantity"]
	cents, hasCents := columns["cents"]
	if !hasQuantity || !hasCents {
		return 0, 0, 0, fmt.Errorf("missing required header")
	}
	var sum int64
	valid, rejected := 0, 0
	for {
		row, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return 0, valid, rejected, err
		}
		count, countErr := strconv.ParseInt(row[quantity], 10, 64)
		price, priceErr := strconv.ParseInt(row[cents], 10, 64)
		if countErr != nil || priceErr != nil || count < 0 || price < 0 {
			rejected++
			continue
		}
		sum += count * price
		valid++
	}
	return sum, valid, rejected, nil
}

func main() {
	sum, valid, rejected, err := total("quantity,item,cents\n2,\"tea, green\",250\n1,cake,225\n1,invalid,oops\n")
	if err != nil {
		panic(err)
	}
	fmt.Printf("valid=%d rejected=%d total-cents=%d\n", valid, rejected, sum)
	_, _, _, err = total("item,cents\ntea,250\n")
	fmt.Printf("missing-header=%t\n", err != nil)
}
