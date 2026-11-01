package main

import (
	"fmt"
	"sort"
	"time"
)

type Bucket struct {
	Count int
	Sum   int
}

func parse(text string) time.Time {
	value, err := time.Parse(time.RFC3339, text)
	if err != nil {
		panic(err)
	}
	return value
}
func main() {
	start := parse("2026-03-12T09:00:00Z")
	end := start.Add(time.Hour)
	buckets := map[time.Time]Bucket{}
	for at := start; at.Before(end); at = at.Add(15 * time.Minute) {
		buckets[at] = Bucket{}
	}
	rejected := 0
	for _, event := range []struct {
		Text  string
		Value int
	}{{"2026-03-12T09:34:00Z", 3}, {"2026-03-12T09:03:00Z", 2}, {"2026-03-12T09:29:00Z", 4}, {"2026-03-12T17:03:00+08:00", 5}, {"2026-03-12T10:00:00Z", 9}} {
		at := parse(event.Text).UTC()
		if at.Before(start) || !at.Before(end) {
			rejected++
			continue
		}
		key := at.Truncate(15 * time.Minute)
		bucket := buckets[key]
		bucket.Count++
		bucket.Sum += event.Value
		buckets[key] = bucket
	}
	keys := []time.Time{}
	for key := range buckets {
		keys = append(keys, key)
	}
	sort.Slice(keys, func(i, j int) bool { return keys[i].Before(keys[j]) })
	for _, key := range keys {
		bucket := buckets[key]
		fmt.Printf("%s count=%d sum=%d\n", key.Format("15:04"), bucket.Count, bucket.Sum)
	}
	fmt.Printf("rejected=%d\n", rejected)
}
