package main

import (
	"fmt"
	"strconv"
	"strings"
)

func cents(text string) (int64, error) {
	parts := strings.Split(text, ".")
	if len(parts) > 2 || parts[0] == "" {
		return 0, fmt.Errorf("invalid amount")
	}
	fraction := "00"
	if len(parts) == 2 {
		if len(parts[1]) < 1 || len(parts[1]) > 2 {
			return 0, fmt.Errorf("invalid precision")
		}
		fraction = parts[1]
		if len(fraction) == 1 {
			fraction += "0"
		}
	}
	for _, r := range parts[0] + fraction {
		if r < '0' || r > '9' {
			return 0, fmt.Errorf("invalid digit")
		}
	}
	whole, err := strconv.ParseInt(parts[0], 10, 64)
	if err != nil || whole > 1000000000 {
		return 0, fmt.Errorf("amount exceeds budget")
	}
	tail, err := strconv.ParseInt(fraction, 10, 64)
	if err != nil {
		return 0, err
	}
	return whole*100 + tail, nil
}
func roundRate(amount, basisPoints int64) int64 { return (amount*basisPoints + 5000) / 10000 }
func main() {
	base, err := cents("12.35")
	if err != nil {
		panic(err)
	}
	discount := roundRate(base, 1000)
	tax := roundRate(base-discount, 825)
	fmt.Printf("base=%d discount=%d tax=%d total=%d\n", base, discount, tax, base-discount+tax)
	_, err = cents("12.345")
	fmt.Printf("precision-rejected=%t\n", err != nil)
	_, err = cents("-1.00")
	fmt.Printf("negative-rejected=%t\n", err != nil)
}
