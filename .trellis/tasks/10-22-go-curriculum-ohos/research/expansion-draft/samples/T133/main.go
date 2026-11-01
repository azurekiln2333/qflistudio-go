package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
)

type Cursor struct {
	Offset int `json:"offset"`
	Limit  int `json:"limit"`
}

func encode(cursor Cursor) string {
	data, err := json.Marshal(cursor)
	if err != nil {
		panic(err)
	}
	return base64.RawURLEncoding.EncodeToString(data)
}

func decode(text string) (Cursor, error) {
	var cursor Cursor
	data, err := base64.RawURLEncoding.DecodeString(text)
	if err != nil {
		return cursor, err
	}
	if err := json.Unmarshal(data, &cursor); err != nil {
		return cursor, err
	}
	if cursor.Offset < 0 || cursor.Limit < 1 || cursor.Limit > 50 {
		return cursor, fmt.Errorf("invalid cursor bounds")
	}
	return cursor, nil
}

func page(items []string, cursor Cursor) ([]string, string, error) {
	if cursor.Offset < 0 || cursor.Offset > len(items) || cursor.Limit < 1 || cursor.Limit > 50 {
		return nil, "", fmt.Errorf("invalid page bounds")
	}
	count := len(items) - cursor.Offset
	if count > cursor.Limit {
		count = cursor.Limit
	}
	end := cursor.Offset + count
	next := ""
	if end < len(items) {
		next = encode(Cursor{end, cursor.Limit})
	}
	return items[cursor.Offset:end], next, nil
}

func main() {
	cursor, err := decode(encode(Cursor{2, 2}))
	if err != nil {
		panic(err)
	}
	items, next, err := page([]string{"a", "b", "c", "d", "e"}, cursor)
	if err != nil {
		panic(err)
	}
	nextCursor, err := decode(next)
	if err != nil {
		panic(err)
	}
	fmt.Printf("page=%v next=%d\n", items, nextCursor.Offset)
	_, err = decode("*")
	fmt.Printf("invalid=%t\n", err != nil)
	_, err = decode(encode(Cursor{-1, 2}))
	fmt.Printf("negative=%t\n", err != nil)
}
