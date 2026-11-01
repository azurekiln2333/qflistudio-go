package main

import (
	"encoding/json"
	"fmt"
)

type Event struct {
	Kind   string `json:"kind"`
	Amount int    `json:"amount"`
}
type State struct {
	Open    bool
	Balance int
}

func apply(state State, event Event) (State, error) {
	next := state
	switch event.Kind {
	case "open":
		if state.Open {
			return state, fmt.Errorf("already open")
		}
		next.Open = true
	case "credit", "debit":
		if !state.Open || event.Amount <= 0 {
			return state, fmt.Errorf("invalid amount/state")
		}
		if event.Kind == "credit" {
			next.Balance += event.Amount
		} else {
			if event.Amount > state.Balance {
				return state, fmt.Errorf("insufficient funds")
			}
			next.Balance -= event.Amount
		}
	default:
		return state, fmt.Errorf("unknown event")
	}
	return next, nil
}
func main() {
	var events []Event
	if err := json.Unmarshal([]byte(`[{"kind":"open"},{"kind":"credit","amount":100},{"kind":"debit","amount":30},{"kind":"debit","amount":90},{"kind":"other"}]`), &events); err != nil {
		panic(err)
	}
	state := State{}
	for index, event := range events {
		next, err := apply(state, event)
		if err != nil {
			fmt.Printf("event%d rejected balance=%d\n", index, state.Balance)
			continue
		}
		state = next
	}
	fmt.Printf("final=%d\n", state.Balance)
}
