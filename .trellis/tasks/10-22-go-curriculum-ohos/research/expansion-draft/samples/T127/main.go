package main

import (
	"bufio"
	"fmt"
	"strings"
)

func lines(text string) []string {
	result := []string{}
	scan := bufio.NewScanner(strings.NewReader(text))
	for scan.Scan() {
		result = append(result, scan.Text())
	}
	if err := scan.Err(); err != nil {
		panic(err)
	}
	return result
}

type Edit struct {
	Kind string
	Old  int
	New  int
	Text string
}

func diff(a, b []string) []Edit {
	table := make([][]int, len(a)+1)
	for i := range table {
		table[i] = make([]int, len(b)+1)
	}
	for i := len(a) - 1; i >= 0; i-- {
		for j := len(b) - 1; j >= 0; j-- {
			if a[i] == b[j] {
				table[i][j] = table[i+1][j+1] + 1
			} else if table[i+1][j] >= table[i][j+1] {
				table[i][j] = table[i+1][j]
			} else {
				table[i][j] = table[i][j+1]
			}
		}
	}
	edits := []Edit{}
	i, j := 0, 0
	for i < len(a) || j < len(b) {
		if i < len(a) && j < len(b) && a[i] == b[j] {
			i++
			j++
			continue
		}
		if i < len(a) && (j == len(b) || table[i+1][j] >= table[i][j+1]) {
			edits = append(edits, Edit{"delete", i + 1, j + 1, a[i]})
			i++
		} else {
			edits = append(edits, Edit{"add", i + 1, j + 1, b[j]})
			j++
		}
	}
	return edits
}

func main() {
	edits := diff(lines("alpha\nbeta\ngamma\ndelta\nobsolete"), lines("alpha\nBETA\ngamma\nomega\ndelta"))
	for i := 0; i < len(edits); i++ {
		edit := edits[i]
		if edit.Kind == "delete" && i+1 < len(edits) && edits[i+1].Kind == "add" {
			next := edits[i+1]
			fmt.Printf("change old:%d new:%d %s -> %s\n", edit.Old, next.New, edit.Text, next.Text)
			i++
		} else if edit.Kind == "delete" {
			fmt.Printf("delete old:%d %s\n", edit.Old, edit.Text)
		} else {
			fmt.Printf("add new:%d %s\n", edit.New, edit.Text)
		}
	}
}
