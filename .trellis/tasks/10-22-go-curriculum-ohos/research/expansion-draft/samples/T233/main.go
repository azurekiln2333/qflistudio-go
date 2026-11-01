package main

import (
	"fmt"
	"sync"
)

type Call struct {
	Done  chan struct{}
	Value string
}
type Group struct {
	mu     sync.Mutex
	calls  map[string]*Call
	joined chan struct{}
}

func (g *Group) Do(key string, load func() string) string {
	g.mu.Lock()
	if existing := g.calls[key]; existing != nil {
		g.mu.Unlock()
		g.joined <- struct{}{}
		<-existing.Done
		return existing.Value
	}
	call := &Call{Done: make(chan struct{})}
	g.calls[key] = call
	g.mu.Unlock()
	call.Value = load()
	g.mu.Lock()
	delete(g.calls, key)
	close(call.Done)
	g.mu.Unlock()
	return call.Value
}
func main() {
	group := &Group{calls: map[string]*Call{}, joined: make(chan struct{}, 5)}
	started := make(chan struct{})
	release := make(chan struct{})
	results := make(chan string, 6)
	loads := 0
	for i := 0; i < 6; i++ {
		go func() {
			results <- group.Do("catalog", func() string { loads++; close(started); <-release; return "ready" })
		}()
	}
	<-started
	for i := 0; i < 5; i++ {
		<-group.joined
	}
	close(release)
	matches := 0
	for i := 0; i < 6; i++ {
		if <-results == "ready" {
			matches++
		}
	}
	fmt.Printf("loads=%d\nmatched=%d\n", loads, matches)
}
