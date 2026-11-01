package main

import (
	"bytes"
	"fmt"
)

type Ring struct {
	slots []string
	next  int
	count int
}

func newRing(capacity int) *Ring {
	if capacity <= 0 {
		panic("capacity must be positive")
	}
	return &Ring{slots: make([]string, capacity)}
}
func (r *Ring) Add(record string) {
	r.slots[r.next] = record
	r.next = (r.next + 1) % len(r.slots)
	if r.count < len(r.slots) {
		r.count++
	}
}
func (r *Ring) Snapshot() []string {
	result := make([]string, r.count)
	start := (r.next - r.count + len(r.slots)) % len(r.slots)
	for i := range result {
		result[i] = r.slots[(start+i)%len(r.slots)]
	}
	return result
}
func (r *Ring) Text() string {
	var out bytes.Buffer
	for i, record := range r.Snapshot() {
		if i > 0 {
			out.WriteByte('\n')
		}
		out.WriteString(record)
	}
	return out.String()
}
func main() {
	ring := newRing(3)
	for _, record := range []string{"a", "b", "c", "d"} {
		ring.Add(record)
	}
	fmt.Printf("recent=%v\n", ring.Snapshot())
	snapshot := ring.Snapshot()
	snapshot[0] = "changed"
	fmt.Printf("isolated=%t\n", ring.Snapshot()[0] == "b")
	ring.Add("e")
	fmt.Printf("export=%q\n", ring.Text())
}
