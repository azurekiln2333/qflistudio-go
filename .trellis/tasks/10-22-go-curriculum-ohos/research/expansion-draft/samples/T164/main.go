package main

import (
	"fmt"
	"math"
)

type Stats struct {
	Count int
	Mean  float64
	M2    float64
}

func (s *Stats) Add(value float64) {
	s.Count++
	delta := value - s.Mean
	s.Mean += delta / float64(s.Count)
	s.M2 += delta * (value - s.Mean)
}
func (s Stats) Variance() (float64, bool) {
	if s.Count < 2 {
		return 0, false
	}
	return s.M2 / float64(s.Count-1), true
}
func main() {
	stats := Stats{}
	for _, value := range []float64{2, 4, 4, 4, 5, 5, 7, 9} {
		stats.Add(value)
	}
	variance, ok := stats.Variance()
	fmt.Printf("count=%d mean=%.2f sample-variance=%.4f\n", stats.Count, stats.Mean, variance)
	fmt.Printf("verified=%t\n", ok && math.Abs(variance-32.0/7) < 1e-12)
	single := Stats{}
	single.Add(9)
	_, ok = single.Variance()
	fmt.Printf("single-defined=%t\n", ok)
}
