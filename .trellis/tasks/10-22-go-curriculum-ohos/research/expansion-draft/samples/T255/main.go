package main

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
)

type Version struct {
	Raw   string
	Parts [3]int
	Pre   []string
}

func number(text string) (int, error) {
	if text == "" || len(text) > 1 && text[0] == '0' {
		return 0, fmt.Errorf("bad number")
	}
	for _, c := range text {
		if c < '0' || c > '9' {
			return 0, fmt.Errorf("bad digit")
		}
	}
	return strconv.Atoi(text)
}
func parse(text string) (Version, error) {
	v := Version{Raw: text}
	parts := strings.SplitN(text, "-", 2)
	core := strings.Split(parts[0], ".")
	if len(core) != 3 {
		return v, fmt.Errorf("need three parts")
	}
	for i, part := range core {
		n, err := number(part)
		if err != nil {
			return v, err
		}
		v.Parts[i] = n
	}
	if len(parts) == 2 {
		v.Pre = strings.Split(parts[1], ".")
		for _, id := range v.Pre {
			if id == "" {
				return v, fmt.Errorf("empty prerelease")
			}
			numeric := true
			for _, c := range id {
				if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c == '-') {
					return v, fmt.Errorf("bad prerelease")
				}
				if c < '0' || c > '9' {
					numeric = false
				}
			}
			if numeric {
				if _, err := number(id); err != nil {
					return v, err
				}
			}
		}
	}
	return v, nil
}
func less(a, b Version) bool {
	for i := 0; i < 3; i++ {
		if a.Parts[i] != b.Parts[i] {
			return a.Parts[i] < b.Parts[i]
		}
	}
	if len(a.Pre) == 0 {
		return false
	}
	if len(b.Pre) == 0 {
		return true
	}
	for i := 0; i < len(a.Pre) && i < len(b.Pre); i++ {
		x, y := a.Pre[i], b.Pre[i]
		if x == y {
			continue
		}
		nx, ex := strconv.Atoi(x)
		ny, ey := strconv.Atoi(y)
		if ex == nil && ey == nil {
			return nx < ny
		}
		if ex == nil {
			return true
		}
		if ey == nil {
			return false
		}
		return x < y
	}
	return len(a.Pre) < len(b.Pre)
}
func main() {
	versions := []Version{}
	for _, text := range []string{"2.0.0", "2.0.0-rc.10", "1.9.0", "2.0.0-alpha.1", "2.0.0-rc.2"} {
		v, err := parse(text)
		if err != nil {
			panic(err)
		}
		versions = append(versions, v)
	}
	sort.SliceStable(versions, func(i, j int) bool { return less(versions[i], versions[j]) })
	for _, v := range versions {
		fmt.Println(v.Raw)
	}
	_, err := parse("1.02.0")
	fmt.Printf("invalid=%t\n", err != nil)
}
