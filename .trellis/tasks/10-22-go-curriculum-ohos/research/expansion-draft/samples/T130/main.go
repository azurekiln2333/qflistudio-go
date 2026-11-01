package main

import (
	"fmt"
	"sort"
	"strings"
	"unicode"
)

type Index map[string]map[int]bool

func build(documents []string) Index {
	index := Index{}
	for i, document := range documents {
		words := strings.FieldsFunc(strings.ToLower(document), func(r rune) bool {
			return !unicode.IsLetter(r) && !unicode.IsNumber(r)
		})
		for _, word := range words {
			if index[word] == nil {
				index[word] = map[int]bool{}
			}
			index[word][i+1] = true
		}
	}
	return index
}

func query(index Index, words ...string) []int {
	result := []int{}
	if len(words) == 0 {
		return result
	}
	for id := range index[strings.ToLower(words[0])] {
		found := true
		for _, word := range words[1:] {
			if !index[strings.ToLower(word)][id] {
				found = false
				break
			}
		}
		if found {
			result = append(result, id)
		}
	}
	sort.Ints(result)
	return result
}

func main() {
	index := build([]string{"Go local tools go", "Go offline docs", "local offline data"})
	fmt.Printf("go=%v\n", query(index, "go"))
	fmt.Printf("go+local=%v\n", query(index, "go", "local"))
	fmt.Printf("local+offline=%v\n", query(index, "local", "offline"))
	fmt.Printf("missing=%v\n", query(index, "absent"))
}
