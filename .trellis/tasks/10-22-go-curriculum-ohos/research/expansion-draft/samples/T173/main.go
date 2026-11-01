package main

import (
	"fmt"
	"time"
)

func advance(start time.Time, days int) (time.Time, error) {
	if days < 0 {
		return time.Time{}, fmt.Errorf("negative workdays")
	}
	at := start
	for days > 0 {
		at = at.AddDate(0, 0, 1)
		if at.Weekday() != time.Saturday && at.Weekday() != time.Sunday {
			days--
		}
	}
	return at, nil
}
func main() {
	start := time.Date(2026, time.January, 30, 9, 0, 0, 0, time.UTC)
	third, err := advance(start, 3)
	if err != nil {
		panic(err)
	}
	fmt.Printf("start=%s %s\n", start.Format("2006-01-02"), start.Weekday().String())
	fmt.Printf("third=%s %s\n", third.Format("2006-01-02"), third.Weekday().String())
	zero, err := advance(start, 0)
	fmt.Printf("zero=%t\n", err == nil && zero.Equal(start))
	_, err = advance(start, -1)
	fmt.Printf("negative=%t\n", err != nil)
}
