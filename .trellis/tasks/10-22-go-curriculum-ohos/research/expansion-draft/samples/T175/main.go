package main

import (
	"fmt"
	"time"
)

func plan(base, cap time.Duration, count int) ([]time.Duration, error) {
	if base <= 0 || cap < base || count < 0 || count > 100 {
		return nil, fmt.Errorf("invalid retry plan")
	}
	result := []time.Duration{}
	delay := base
	for i := 0; i < count; i++ {
		result = append(result, delay)
		if delay > cap/2 {
			delay = cap
		} else {
			delay *= 2
		}
	}
	return result, nil
}
func main() {
	delays, err := plan(100*time.Millisecond, 750*time.Millisecond, 6)
	if err != nil {
		panic(err)
	}
	var total time.Duration
	for _, delay := range delays {
		total += delay
	}
	fmt.Printf("delays=%v\ntotal=%s\n", delays, total.String())
	_, err = plan(0, time.Second, 2)
	fmt.Printf("invalid=%t\n", err != nil)
}
