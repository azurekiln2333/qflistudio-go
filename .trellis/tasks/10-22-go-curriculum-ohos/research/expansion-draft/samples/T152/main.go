package main

import (
	"container/heap"
	"fmt"
)

type Task struct {
	Name  string
	Due   int
	Seq   int
	Index int
}
type Tasks []*Task

func (q Tasks) Len() int { return len(q) }
func (q Tasks) Less(i, j int) bool {
	if q[i].Due != q[j].Due {
		return q[i].Due < q[j].Due
	}
	return q[i].Seq < q[j].Seq
}
func (q Tasks) Swap(i, j int) { q[i], q[j] = q[j], q[i]; q[i].Index = i; q[j].Index = j }
func (q *Tasks) Push(value interface{}) {
	task := value.(*Task)
	task.Index = len(*q)
	*q = append(*q, task)
}
func (q *Tasks) Pop() interface{} {
	old := *q
	task := old[len(old)-1]
	old[len(old)-1] = nil
	*q = old[:len(old)-1]
	task.Index = -1
	return task
}
func main() {
	queue := &Tasks{}
	first := &Task{Name: "A", Due: 5, Seq: 1}
	heap.Push(queue, first)
	heap.Push(queue, &Task{Name: "B", Due: 3, Seq: 2})
	heap.Push(queue, &Task{Name: "C", Due: 3, Seq: 3})
	first.Due = 2
	heap.Fix(queue, first.Index)
	for queue.Len() > 0 {
		task := heap.Pop(queue).(*Task)
		fmt.Printf("%s@%d\n", task.Name, task.Due)
	}
	fmt.Printf("removed-index=%d\n", first.Index)
}
