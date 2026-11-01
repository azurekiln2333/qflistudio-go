package main

import (
	"fmt"
	"math"
	"sort"
)

func percentile(input []float64, p float64) (float64, error) {
	if len(input) == 0 || math.IsNaN(p) || p < 0 || p > 1 {
		return 0, fmt.Errorf("invalid percentile")
	}
	data := append([]float64(nil), input...)
	for _, v := range data {
		if math.IsNaN(v) || math.IsInf(v, 0) {
			return 0, fmt.Errorf("nonfinite sample")
		}
	}
	sort.Float64s(data)
	position := p * float64(len(data)-1)
	low := int(math.Floor(position))
	high := int(math.Ceil(position))
	return data[low] + (data[high]-data[low])*(position-float64(low)), nil
}
func main() {
	data := []float64{50, 10, 40, 20, 30}
	p50, err := percentile(data, .5)
	if err != nil {
		panic(err)
	}
	p90, err := percentile(data, .9)
	if err != nil {
		panic(err)
	}
	single, err := percentile([]float64{7}, .9)
	if err != nil {
		panic(err)
	}
	fmt.Printf("p50=%.1f p90=%.1f single=%.1f\n", p50, p90, single)
	_, err = percentile(data, 1.1)
	fmt.Printf("invalid=%t\n", err != nil)
	_, err = percentile([]float64{math.NaN()}, .5)
	fmt.Printf("nan-rejected=%t\n", err != nil)
}
