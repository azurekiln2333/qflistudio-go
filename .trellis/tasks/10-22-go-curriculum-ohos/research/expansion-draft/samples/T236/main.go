package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type Config struct {
	Version int
	Label   string
}

func main() {
	var current atomic.Value
	current.Store(Config{1, "v1"})
	ready := make(chan struct{})
	var readers sync.WaitGroup
	var invalid int32
	for i := 0; i < 4; i++ {
		readers.Add(1)
		go func() {
			defer readers.Done()
			<-ready
			for n := 0; n < 100; n++ {
				snapshot := current.Load().(Config)
				if snapshot.Label != fmt.Sprintf("v%d", snapshot.Version) {
					atomic.AddInt32(&invalid, 1)
				}
			}
		}()
	}
	close(ready)
	for version := 2; version <= 20; version++ {
		current.Store(Config{version, fmt.Sprintf("v%d", version)})
	}
	readers.Wait()
	final := current.Load().(Config)
	fmt.Printf("invalid=%d\nfinal=%d:%s\n", invalid, final.Version, final.Label)
}
