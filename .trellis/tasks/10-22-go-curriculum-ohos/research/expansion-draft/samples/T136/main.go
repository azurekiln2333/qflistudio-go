package main

import (
	"bytes"
	"encoding/json"
	"fmt"
)

type Profile struct{ Nickname *string }

func apply(profile *Profile, text string) error {
	var fields map[string]json.RawMessage
	if err := json.Unmarshal([]byte(text), &fields); err != nil {
		return err
	}
	raw, exists := fields["nickname"]
	if !exists {
		return nil
	}
	if bytes.Equal(bytes.TrimSpace(raw), []byte("null")) {
		profile.Nickname = nil
		return nil
	}
	var name string
	if err := json.Unmarshal(raw, &name); err != nil {
		return err
	}
	profile.Nickname = &name
	return nil
}

func display(profile Profile) string {
	if profile.Nickname == nil {
		return "<unset>"
	}
	return *profile.Nickname
}

func main() {
	initial := "Li"
	profile := Profile{&initial}
	for _, step := range []struct {
		Label string
		Patch string
	}{
		{"missing", `{}`}, {"null", `{"nickname":null}`}, {"value", `{"nickname":"Yu"}`},
	} {
		if err := apply(&profile, step.Patch); err != nil {
			panic(err)
		}
		fmt.Printf("%s=%s\n", step.Label, display(profile))
	}
	err := apply(&profile, `{"nickname":42}`)
	fmt.Printf("bad-type=%t preserved=%s\n", err != nil, display(profile))
}
