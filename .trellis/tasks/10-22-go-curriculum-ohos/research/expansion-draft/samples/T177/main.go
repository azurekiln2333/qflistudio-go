package main

import (
	"fmt"
	"time"
)

func next(now time.Time, hour, minute int) (time.Time, error) {
	if hour < 0 || hour > 23 || minute < 0 || minute > 59 {
		return time.Time{}, fmt.Errorf("invalid daily clock")
	}
	candidate := time.Date(now.Year(), now.Month(), now.Day(), hour, minute, 0, 0, now.Location())
	if !candidate.After(now) {
		candidate = candidate.AddDate(0, 0, 1)
	}
	return candidate, nil
}
func main() {
	for _, item := range []struct {
		Label string
		Hour  int
	}{{"before", 8}, {"after", 10}, {"equal", 9}} {
		now := time.Date(2026, time.March, 12, item.Hour, 0, 0, 0, time.UTC)
		candidate, err := next(now, 9, 0)
		if err != nil {
			panic(err)
		}
		fmt.Printf("%s=%s\n", item.Label, candidate.Format(time.RFC3339))
	}
}
