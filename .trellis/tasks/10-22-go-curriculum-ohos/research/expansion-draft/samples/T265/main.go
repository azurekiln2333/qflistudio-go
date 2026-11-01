package main

import (
	"bytes"
	"fmt"
	"strings"
)

func encode(name string) ([]byte, error) {
	var out bytes.Buffer
	for _, label := range strings.Split(name, ".") {
		if len(label) < 1 || len(label) > 63 {
			return nil, fmt.Errorf("label length")
		}
		for _, c := range label {
			if c > 127 {
				return nil, fmt.Errorf("ASCII labels only")
			}
		}
		out.WriteByte(byte(len(label)))
		out.WriteString(label)
	}
	out.WriteByte(0)
	if out.Len() > 255 {
		return nil, fmt.Errorf("name too long")
	}
	return out.Bytes(), nil
}
func decode(wire []byte) (string, error) {
	labels := []string{}
	for len(wire) > 0 {
		n := int(wire[0])
		wire = wire[1:]
		if n == 0 {
			if len(wire) != 0 {
				return "", fmt.Errorf("trailing data")
			}
			return strings.Join(labels, "."), nil
		}
		if n > 63 || len(wire) < n {
			return "", fmt.Errorf("bad label")
		}
		labels = append(labels, string(wire[:n]))
		wire = wire[n:]
	}
	return "", fmt.Errorf("missing root label")
}
func main() {
	wire, err := encode("www.example.test")
	if err != nil {
		panic(err)
	}
	name, err := decode(wire)
	if err != nil {
		panic(err)
	}
	fmt.Printf("name=%s\nbytes=%d\n", name, len(wire))
	_, err = encode(strings.Repeat("a", 64) + ".test")
	fmt.Printf("long-label=%t\n", err != nil)
	_, err = decode(wire[:len(wire)-1])
	fmt.Printf("missing-root=%t\n", err != nil)
}
