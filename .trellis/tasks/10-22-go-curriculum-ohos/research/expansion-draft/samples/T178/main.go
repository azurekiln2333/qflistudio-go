package main

import (
	"fmt"
	"time"
)

func strict(text string) (time.Time, error) {
	value, err := time.Parse("2006-01-02", text)
	if err != nil {
		return time.Time{}, err
	}
	if value.Format("2006-01-02") != text {
		return time.Time{}, fmt.Errorf("noncanonical date")
	}
	return value, nil
}
func main() {
	leap, err := strict("2024-02-29")
	if err != nil {
		panic(err)
	}
	fmt.Printf("leap=%s\n", leap.Format("2006-01-02"))
	normalized := time.Date(2025, time.February, 29, 0, 0, 0, 0, time.UTC)
	_, err = strict("2025-02-29")
	fmt.Printf("normalized=%s rejected=%t\n", normalized.Format("2006-01-02"), err != nil)
	_, err = strict("2026-04-31")
	fmt.Printf("april-rejected=%t\n", err != nil)
	_, err = strict("2026-4-01")
	fmt.Printf("nonpadded-rejected=%t\n", err != nil)
}
