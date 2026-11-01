package main

import (
	"fmt"
	"strconv"
)

func checkDigit(body string) (int, error) {
	sum := 0
	double := true
	for i := len(body) - 1; i >= 0; i-- {
		c := body[i]
		if c < '0' || c > '9' {
			return 0, fmt.Errorf("ASCII digits only")
		}
		n := int(c - '0')
		if double {
			n *= 2
			if n > 9 {
				n -= 9
			}
		}
		sum += n
		double = !double
	}
	if body == "" {
		return 0, fmt.Errorf("empty")
	}
	return (10 - sum%10) % 10, nil
}
func valid(code string) bool {
	if len(code) < 2 {
		return false
	}
	digit, err := checkDigit(code[:len(code)-1])
	return err == nil && code[len(code)-1] == byte('0'+digit)
}
func main() {
	body := "7992739871"
	digit, err := checkDigit(body)
	if err != nil {
		panic(err)
	}
	full := body + strconv.Itoa(digit)
	fmt.Printf("code=%s\nvalid=%t\ntampered=%t\n", full, valid(full), valid("79927398714"))
	_, err = checkDigit("12x")
	fmt.Printf("bad-input=%t\n", err != nil)
}
