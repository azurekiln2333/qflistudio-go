package main

import (
	"bytes"
	"encoding/gob"
	"fmt"
)

type OldState struct {
	Name  string
	Count int
}
type NewState struct {
	Name  string
	Count int
	Note  string
}

func main() {
	var buffer bytes.Buffer
	if err := gob.NewEncoder(&buffer).Encode(OldState{"queue", 3}); err != nil {
		panic(err)
	}
	snapshot := append([]byte(nil), buffer.Bytes()...)
	var restored NewState
	if err := gob.NewDecoder(bytes.NewReader(snapshot)).Decode(&restored); err != nil {
		panic(err)
	}
	fmt.Printf("name=%s count=%d\n", restored.Name, restored.Count)
	fmt.Printf("new-field-empty=%t\n", restored.Note == "")
	var damaged NewState
	err := gob.NewDecoder(bytes.NewReader(snapshot[:len(snapshot)/2])).Decode(&damaged)
	fmt.Printf("truncated=%t\n", err != nil)
}
