package main

import (
	"fmt"
	"math"
	"time"
)

type Bucket struct {
	Capacity, Tokens, PerSecond float64
	Last                        time.Time
}

func (b *Bucket) Allow(now time.Time) bool {
	if now.Before(b.Last) {
		return false
	}
	b.Tokens = math.Min(b.Capacity, b.Tokens+now.Sub(b.Last).Seconds()*b.PerSecond)
	b.Last = now
	if b.Tokens < 1 {
		return false
	}
	b.Tokens--
	return true
}
func main() {
	start := time.Date(2026, 10, 23, 0, 0, 0, 0, time.UTC)
	b := &Bucket{Capacity: 2, Tokens: 2, PerSecond: 1, Last: start}
	for _, offset := range []time.Duration{0, 0, 0, 500 * time.Millisecond, time.Second, time.Second, 3 * time.Second} {
		fmt.Printf("t=%4.1f allow=%t\n", offset.Seconds(), b.Allow(start.Add(offset)))
	}
	fmt.Printf("clock-backwards=%t\n", b.Allow(start))
}
