package main

import (
	"container/heap"
	"fmt"
	"sort"
)

type Booking struct {
	ID         string
	Start, End int
}
type Room struct{ End, ID int }
type Active []Room

func (h Active) Len() int { return len(h) }
func (h Active) Less(i, j int) bool {
	if h[i].End != h[j].End {
		return h[i].End < h[j].End
	}
	return h[i].ID < h[j].ID
}
func (h Active) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *Active) Push(v interface{}) { *h = append(*h, v.(Room)) }
func (h *Active) Pop() interface{}   { old := *h; v := old[len(old)-1]; *h = old[:len(old)-1]; return v }
func main() {
	bookings := []Booking{{"A", 0, 30}, {"B", 5, 10}, {"C", 10, 20}, {"D", 30, 40}}
	sort.SliceStable(bookings, func(i, j int) bool { return bookings[i].Start < bookings[j].Start })
	active := &Active{}
	heap.Init(active)
	rooms := 0
	for _, booking := range bookings {
		if booking.Start >= booking.End {
			panic("bad interval")
		}
		room := 0
		if active.Len() > 0 && (*active)[0].End <= booking.Start {
			room = heap.Pop(active).(Room).ID
		} else {
			rooms++
			room = rooms
		}
		heap.Push(active, Room{booking.End, room})
		fmt.Printf("%s=room%d\n", booking.ID, room)
	}
	fmt.Printf("rooms=%d\n", rooms)
}
