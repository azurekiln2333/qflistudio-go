package main

import (
	"encoding/json"
	"fmt"
)

type Envelope struct {
	Kind    string          `json:"kind"`
	Payload json.RawMessage `json:"payload"`
}

func describe(text string) (string, error) {
	var event Envelope
	if err := json.Unmarshal([]byte(text), &event); err != nil {
		return "", err
	}
	switch event.Kind {
	case "user":
		var user struct {
			Name string `json:"name"`
		}
		if err := json.Unmarshal(event.Payload, &user); err != nil {
			return "", err
		}
		if user.Name == "" {
			return "", fmt.Errorf("missing name")
		}
		return "user=" + user.Name, nil
	case "quota":
		var quota struct {
			Limit int `json:"limit"`
		}
		if err := json.Unmarshal(event.Payload, &quota); err != nil {
			return "", err
		}
		if quota.Limit < 1 {
			return "", fmt.Errorf("invalid limit")
		}
		return fmt.Sprintf("limit=%d", quota.Limit), nil
	default:
		return "", fmt.Errorf("unknown kind %q", event.Kind)
	}
}

func main() {
	for _, input := range []string{`{"kind":"user","payload":{"name":"Lin"}}`, `{"kind":"quota","payload":{"limit":8}}`} {
		line, err := describe(input)
		if err != nil {
			panic(err)
		}
		fmt.Println(line)
	}
	_, err := describe(`{"kind":"future","payload":{}}`)
	fmt.Printf("unknown=%t\n", err != nil)
	_, err = describe(`{"kind":"quota","payload":{"limit":"bad"}}`)
	fmt.Printf("bad-payload=%t\n", err != nil)
}
