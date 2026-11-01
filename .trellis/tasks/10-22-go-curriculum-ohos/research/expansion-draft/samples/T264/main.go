package main

import (
	"fmt"
	"strconv"
	"strings"
)

func parse(wire string) ([]string, error) {
	frames := []string{}
	for wire != "" {
		colon := strings.IndexByte(wire, ':')
		if colon <= 0 {
			return nil, fmt.Errorf("missing length")
		}
		prefix := wire[:colon]
		if len(prefix) > 1 && prefix[0] == '0' {
			return nil, fmt.Errorf("leading zero")
		}
		for _, c := range prefix {
			if c < '0' || c > '9' {
				return nil, fmt.Errorf("bad length")
			}
		}
		n, err := strconv.Atoi(prefix)
		if err != nil || n > 64 {
			return nil, fmt.Errorf("length budget")
		}
		start := colon + 1
		if n >= len(wire)-start || wire[start+n] != ',' {
			return nil, fmt.Errorf("truncated or missing comma")
		}
		frames = append(frames, wire[start:start+n])
		wire = wire[start+n+1:]
	}
	return frames, nil
}
func main() {
	frames, err := parse("3:cat,0:,6:中文,")
	if err != nil {
		panic(err)
	}
	fmt.Printf("frames=%q\n", frames)
	for _, bad := range []string{"4:cat,", "3:cat;", "03:cat,"} {
		_, err := parse(bad)
		fmt.Printf("bad=%t\n", err != nil)
	}
}
