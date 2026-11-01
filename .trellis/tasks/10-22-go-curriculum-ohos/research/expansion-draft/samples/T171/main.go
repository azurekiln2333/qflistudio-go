package main

import (
	"fmt"
	"time"
)

func mustTime(text string) time.Time {
	value, err := time.Parse(time.RFC3339, text)
	if err != nil {
		panic(err)
	}
	return value
}
func main() {
	east := mustTime("2026-03-12T09:30:00+08:00")
	utc := mustTime("2026-03-12T01:30:00Z")
	fmt.Printf("utc=%s equal=%t\n", east.UTC().Format(time.RFC3339), east.Equal(utc))
	west := east.In(time.FixedZone("WEST", -5*60*60))
	fmt.Printf("west=%s\n", west.Format(time.RFC3339))
}
