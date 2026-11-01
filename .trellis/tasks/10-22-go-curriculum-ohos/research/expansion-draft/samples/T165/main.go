package main

import "fmt"

type Window struct {
	Values []int64
	Next   int
	Count  int
	Sum    int64
}

func newWindow(size int) *Window {
	if size <= 0 {
		panic("invalid window")
	}
	return &Window{Values: make([]int64, size)}
}
func (w *Window) Add(value int64) float64 {
	if w.Count == len(w.Values) {
		w.Sum -= w.Values[w.Next]
	} else {
		w.Count++
	}
	w.Values[w.Next] = value
	w.Sum += value
	w.Next = (w.Next + 1) % len(w.Values)
	return float64(w.Sum) / float64(w.Count)
}
func main() {
	window := newWindow(3)
	for _, value := range []int64{10, 20, 30, 50} {
		average := window.Add(value)
		fmt.Printf("value=%d average=%.1f count=%d\n", value, average, window.Count)
	}
}
