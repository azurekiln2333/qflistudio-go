package main

import (
	"bufio"
	"fmt"
	"sort"
	"strings"
)

type Word struct {
	Text  string
	Count int
}

func top(text string, n int) []Word {
	counts := map[string]int{}
	scanner := bufio.NewScanner(strings.NewReader(text))
	scanner.Split(bufio.ScanWords)
	for scanner.Scan() {
		counts[strings.ToLower(scanner.Text())]++
	}
	if err := scanner.Err(); err != nil {
		panic(err)
	}
	words := make([]Word, 0, len(counts))
	for word, count := range counts {
		words = append(words, Word{word, count})
	}
	sort.Slice(words, func(i, j int) bool {
		if words[i].Count != words[j].Count {
			return words[i].Count > words[j].Count
		}
		return words[i].Text < words[j].Text
	})
	if n > len(words) {
		n = len(words)
	}
	return words[:n]
}

func main() {
	text := "Beta alpha beta\ngamma ALPHA gamma beta delta"
	for _, word := range top(text, 3) {
		fmt.Printf("%s=%d\n", word.Text, word.Count)
	}
	fmt.Printf("zero=%d all=%d\n", len(top(text, 0)), len(top(text, 99)))
}
