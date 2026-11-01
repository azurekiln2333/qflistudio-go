package main

import (
	"fmt"
	"sort"
	"sync"
)

type Job struct{ Index, Value int }
type Result struct{ Index, Value int }

func main() {
	input := []int{2, 3, 4, 5}
	jobs := make(chan Job, len(input))
	results := make(chan Result, len(input))
	for i, value := range input {
		jobs <- Job{i, value}
	}
	close(jobs)
	var workers sync.WaitGroup
	for n := 0; n < 2; n++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for job := range jobs {
				results <- Result{job.Index, job.Value * job.Value}
			}
		}()
	}
	workers.Wait()
	close(results)
	ordered := []Result{}
	for result := range results {
		ordered = append(ordered, result)
	}
	sort.Slice(ordered, func(i, j int) bool { return ordered[i].Index < ordered[j].Index })
	values := []int{}
	for _, result := range ordered {
		values = append(values, result.Value)
	}
	fmt.Printf("ordered=%v\n", values)
}
