package main

import (
	"encoding/json"
	"fmt"
)

type Status int

const (
	Pending Status = iota
	Ready
)

func (s Status) MarshalText() ([]byte, error) {
	switch s {
	case Pending:
		return []byte("pending"), nil
	case Ready:
		return []byte("ready"), nil
	}
	return nil, fmt.Errorf("unknown status")
}
func (s *Status) UnmarshalText(text []byte) error {
	var next Status
	switch string(text) {
	case "pending":
		next = Pending
	case "ready":
		next = Ready
	default:
		return fmt.Errorf("invalid status")
	}
	*s = next
	return nil
}
func main() {
	wire, err := json.Marshal(Ready)
	if err != nil {
		panic(err)
	}
	fmt.Printf("wire=%s\n", wire)
	var status Status
	if err = json.Unmarshal([]byte(`"ready"`), &status); err != nil {
		panic(err)
	}
	fmt.Printf("roundtrip=%t\n", status == Ready)
	err = json.Unmarshal([]byte(`"deleted"`), &status)
	fmt.Printf("invalid=%t unchanged=%t\n", err != nil, status == Ready)
}
