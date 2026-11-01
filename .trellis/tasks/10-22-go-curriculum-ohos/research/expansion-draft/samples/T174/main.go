package main

import (
	"fmt"
	"time"
)

type Usage struct {
	Date     string
	Duration time.Duration
}

func split(start, end time.Time) ([]Usage, error) {
	if end.Before(start) {
		return nil, fmt.Errorf("reversed interval")
	}
	end = end.In(start.Location())
	result := []Usage{}
	for cursor := start; cursor.Before(end); {
		midnight := time.Date(cursor.Year(), cursor.Month(), cursor.Day()+1, 0, 0, 0, 0, cursor.Location())
		stop := midnight
		if end.Before(stop) {
			stop = end
		}
		result = append(result, Usage{cursor.Format("2006-01-02"), stop.Sub(cursor)})
		cursor = stop
	}
	return result, nil
}
func main() {
	start := time.Date(2026, time.March, 12, 23, 40, 0, 0, time.UTC)
	end := start.Add(45 * time.Minute)
	parts, err := split(start, end)
	if err != nil {
		panic(err)
	}
	var total time.Duration
	for _, part := range parts {
		fmt.Printf("%s=%.0fm\n", part.Date, part.Duration.Minutes())
		total += part.Duration
	}
	fmt.Printf("total=%.0fm preserved=%t\n", total.Minutes(), total == end.Sub(start))
	_, err = split(end, start)
	fmt.Printf("reversed=%t\n", err != nil)
}
