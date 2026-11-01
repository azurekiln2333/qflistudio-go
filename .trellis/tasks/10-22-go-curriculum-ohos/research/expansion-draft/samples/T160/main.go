package main

import (
	"fmt"
	"sort"
)

type Node struct {
	Children map[rune]*Node
	End      bool
}

func newNode() *Node { return &Node{Children: map[rune]*Node{}} }
func (root *Node) Insert(word string) {
	node := root
	for _, r := range word {
		if node.Children[r] == nil {
			node.Children[r] = newNode()
		}
		node = node.Children[r]
	}
	node.End = true
}
func (root *Node) Complete(prefix string, limit int) []string {
	result := []string{}
	if limit <= 0 {
		return result
	}
	node := root
	for _, r := range prefix {
		node = node.Children[r]
		if node == nil {
			return result
		}
	}
	var walk func(*Node, string)
	walk = func(at *Node, text string) {
		if len(result) >= limit {
			return
		}
		if at.End {
			result = append(result, text)
		}
		keys := []rune{}
		for r := range at.Children {
			keys = append(keys, r)
		}
		sort.Slice(keys, func(i, j int) bool { return keys[i] < keys[j] })
		for _, r := range keys {
			if len(result) >= limit {
				break
			}
			walk(at.Children[r], text+string(r))
		}
	}
	walk(node, prefix)
	return result
}
func main() {
	root := newNode()
	for _, word := range []string{"gone", "go", "gopher", "golang", "猫咪", "猫"} {
		root.Insert(word)
	}
	fmt.Printf("go=%v\n", root.Complete("go", 3))
	fmt.Printf("猫=%v\n", root.Complete("猫", 2))
	fmt.Printf("missing=%v\n", root.Complete("z", 3))
}
