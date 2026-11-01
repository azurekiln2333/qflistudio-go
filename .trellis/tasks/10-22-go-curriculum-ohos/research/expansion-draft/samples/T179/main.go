package main

import (
	"fmt"
	"time"
)

func charge(duration, unit time.Duration) (time.Duration, error) {
	if duration < 0 || unit <= 0 {
		return 0, fmt.Errorf("invalid duration")
	}
	blocks := duration / unit
	if duration%unit != 0 {
		blocks++
	}
	const maximum time.Duration = 1<<63 - 1
	if blocks > maximum/unit {
		return 0, fmt.Errorf("charge overflow")
	}
	return blocks * unit, nil
}
func main() {
	var separate, total time.Duration
	for _, duration := range []time.Duration{time.Minute, 14 * time.Minute, 16 * time.Minute} {
		cost, err := charge(duration, 15*time.Minute)
		if err != nil {
			panic(err)
		}
		separate += cost
		total += duration
	}
	combined, err := charge(total, 15*time.Minute)
	if err != nil {
		panic(err)
	}
	fmt.Printf("separate-minutes=%.0f combined-minutes=%.0f\n", separate.Minutes(), combined.Minutes())
	zero, err := charge(0, 15*time.Minute)
	if err != nil {
		panic(err)
	}
	fmt.Printf("zero=%d\n", zero)
	_, err = charge(-time.Second, 15*time.Minute)
	fmt.Printf("negative-rejected=%t\n", err != nil)
}
