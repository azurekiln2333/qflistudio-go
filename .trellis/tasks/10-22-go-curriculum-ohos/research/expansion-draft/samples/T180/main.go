package main

import (
	"container/heap"
	"fmt"
	"time"
)

type Event struct {
	At   time.Time
	Text string
}
type Cursor struct {
	Event  Event
	Source int
	Index  int
}
type Queue []Cursor

func (q Queue) Len() int { return len(q) }
func (q Queue) Less(i, j int) bool {
	if !q[i].Event.At.Equal(q[j].Event.At) {
		return q[i].Event.At.Before(q[j].Event.At)
	}
	if q[i].Source != q[j].Source {
		return q[i].Source < q[j].Source
	}
	return q[i].Index < q[j].Index
}
func (q Queue) Swap(i, j int)           { q[i], q[j] = q[j], q[i] }
func (q *Queue) Push(value interface{}) { *q = append(*q, value.(Cursor)) }
func (q *Queue) Pop() interface{} {
	old := *q
	value := old[len(old)-1]
	*q = old[:len(old)-1]
	return value
}
func merge(streams [][]Event) ([]Cursor, error) {
	queue := &Queue{}
	for source, stream := range streams {
		for i := 1; i < len(stream); i++ {
			if stream[i].At.Before(stream[i-1].At) {
				return nil, fmt.Errorf("unsorted stream")
			}
		}
		if len(stream) > 0 {
			heap.Push(queue, Cursor{stream[0], source, 0})
		}
	}
	result := []Cursor{}
	for queue.Len() > 0 {
		current := heap.Pop(queue).(Cursor)
		result = append(result, current)
		next := current.Index + 1
		if next < len(streams[current.Source]) {
			heap.Push(queue, Cursor{streams[current.Source][next], current.Source, next})
		}
	}
	return result, nil
}
func main() {
	base := time.Date(2026, time.March, 12, 10, 0, 0, 0, time.UTC)
	streams := [][]Event{{{base, "a0"}, {base.Add(2 * time.Minute), "a1"}}, {{base, "b0"}, {base.Add(time.Minute), "b1"}}, {{base.Add(time.Minute), "c0"}, {base.Add(2 * time.Minute), "c1"}}}
	result, err := merge(streams)
	if err != nil {
		panic(err)
	}
	for _, item := range result {
		fmt.Printf("%s source=%d %s\n", item.Event.At.Format("15:04"), item.Source, item.Event.Text)
	}
}
