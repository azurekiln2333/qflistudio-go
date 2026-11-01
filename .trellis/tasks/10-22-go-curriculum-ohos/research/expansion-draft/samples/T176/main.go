package main

import (
	"fmt"
	"sort"
	"time"
)

type Entry struct {
	Value   int
	Expires time.Time
}
type Cache map[string]Entry

func (c Cache) Put(key string, value int, now time.Time, ttl time.Duration) {
	if ttl <= 0 {
		panic("invalid ttl")
	}
	c[key] = Entry{value, now.Add(ttl)}
}
func (c Cache) Get(key string, now time.Time) (int, bool) {
	entry, ok := c[key]
	if !ok || !now.Before(entry.Expires) {
		return 0, false
	}
	return entry.Value, true
}
func (c Cache) Purge(now time.Time) int {
	removed := 0
	for key, entry := range c {
		if !now.Before(entry.Expires) {
			delete(c, key)
			removed++
		}
	}
	return removed
}
func (c Cache) Keys() []string {
	keys := []string{}
	for key := range c {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}
func main() {
	now := time.Date(2026, time.March, 12, 9, 0, 0, 0, time.UTC)
	cache := Cache{}
	cache.Put("a", 1, now, 5*time.Minute)
	cache.Put("b", 2, now, 10*time.Minute)
	value, found := cache.Get("a", now.Add(4*time.Minute))
	fmt.Printf("early=%d found=%t\n", value, found)
	_, found = cache.Get("a", now.Add(5*time.Minute))
	fmt.Printf("at-expiry=%t\n", found)
	removed := cache.Purge(now.Add(5 * time.Minute))
	fmt.Printf("purged=%d remaining=%v\n", removed, cache.Keys())
	removed = cache.Purge(now.Add(10 * time.Minute))
	fmt.Printf("final=%d remaining=%v\n", removed, cache.Keys())
}
