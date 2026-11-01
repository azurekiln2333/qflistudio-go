package main

import (
	"container/list"
	"fmt"
)

type Entry struct {
	Key   string
	Value int
}
type Cache struct {
	Capacity int
	Order    *list.List
	Entries  map[string]*list.Element
}

func newCache(capacity int) *Cache {
	if capacity < 1 {
		panic("invalid capacity")
	}
	return &Cache{capacity, list.New(), map[string]*list.Element{}}
}
func (c *Cache) Get(key string) (int, bool) {
	element, ok := c.Entries[key]
	if !ok {
		return 0, false
	}
	c.Order.MoveToFront(element)
	return element.Value.(Entry).Value, true
}
func (c *Cache) Put(key string, value int) {
	if element, ok := c.Entries[key]; ok {
		element.Value = Entry{key, value}
		c.Order.MoveToFront(element)
		return
	}
	c.Entries[key] = c.Order.PushFront(Entry{key, value})
	if c.Order.Len() > c.Capacity {
		last := c.Order.Back()
		delete(c.Entries, last.Value.(Entry).Key)
		c.Order.Remove(last)
	}
}
func (c *Cache) Keys() []string {
	keys := []string{}
	for element := c.Order.Front(); element != nil; element = element.Next() {
		keys = append(keys, element.Value.(Entry).Key)
	}
	return keys
}
func main() {
	cache := newCache(2)
	cache.Put("a", 1)
	cache.Put("b", 2)
	value, ok := cache.Get("a")
	fmt.Printf("hit=%d found=%t\n", value, ok)
	cache.Put("c", 3)
	_, ok = cache.Get("b")
	fmt.Printf("b-evicted=%t order=%v\n", !ok, cache.Keys())
	cache.Put("a", 10)
	value, _ = cache.Get("a")
	fmt.Printf("updated=%d order=%v\n", value, cache.Keys())
}
