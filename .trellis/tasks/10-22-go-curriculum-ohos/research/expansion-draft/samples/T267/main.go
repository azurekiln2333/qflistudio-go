package main

import (
	"fmt"
	"math/bits"
)

type Slots struct {
	Used     uint64
	Capacity uint
}

func (s *Slots) Allocate() (int, error) {
	if s.Capacity == 0 || s.Capacity > 64 {
		return -1, fmt.Errorf("capacity")
	}
	mask := ^uint64(0)
	if s.Capacity < 64 {
		mask = (uint64(1) << s.Capacity) - 1
	}
	free := ^s.Used & mask
	if free == 0 {
		return -1, fmt.Errorf("full")
	}
	index := bits.TrailingZeros64(free)
	s.Used |= uint64(1) << uint(index)
	return index, nil
}
func (s *Slots) Release(index uint) error {
	if index >= s.Capacity || s.Used&(uint64(1)<<index) == 0 {
		return fmt.Errorf("not allocated")
	}
	s.Used &^= uint64(1) << index
	return nil
}
func main() {
	s := &Slots{Capacity: 3}
	values := []int{}
	for i := 0; i < 3; i++ {
		slot, err := s.Allocate()
		if err != nil {
			panic(err)
		}
		values = append(values, slot)
	}
	_, err := s.Allocate()
	fmt.Printf("slots=%v\nfull=%t\n", values, err != nil)
	if err = s.Release(1); err != nil {
		panic(err)
	}
	slot, err := s.Allocate()
	if err != nil {
		panic(err)
	}
	fmt.Printf("reused=%d\n", slot)
}
