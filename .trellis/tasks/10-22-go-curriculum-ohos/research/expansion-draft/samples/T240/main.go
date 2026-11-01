package main

import (
	"fmt"
	"sync"
)

type Service struct {
	once     sync.Once
	value    string
	err      error
	attempts int
}

func (s *Service) Get() (string, error) {
	s.once.Do(func() { s.attempts++; s.err = fmt.Errorf("local config missing") })
	return s.value, s.err
}
func main() {
	service := &Service{}
	var callers sync.WaitGroup
	errors := make(chan string, 4)
	for i := 0; i < 4; i++ {
		callers.Add(1)
		go func() {
			defer callers.Done()
			_, err := service.Get()
			if err != nil {
				errors <- err.Error()
			}
		}()
	}
	callers.Wait()
	close(errors)
	count := 0
	same := true
	for message := range errors {
		count++
		same = same && message == "local config missing"
	}
	fmt.Printf("attempts=%d\nerrors=%d\nsame=%t\n", service.attempts, count, same)
}
