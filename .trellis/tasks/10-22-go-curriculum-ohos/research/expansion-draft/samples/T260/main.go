package main

import (
	"bytes"
	"fmt"
	"unicode/utf8"
)

type Decoder struct {
	Pending []byte
	Failed  bool
}

func (d *Decoder) Feed(chunk []byte, final bool) (string, error) {
	if d.Failed {
		return "", fmt.Errorf("decoder failed")
	}
	d.Pending = append(d.Pending, chunk...)
	var out bytes.Buffer
	for len(d.Pending) > 0 && utf8.FullRune(d.Pending) {
		r, size := utf8.DecodeRune(d.Pending)
		if r == utf8.RuneError && size == 1 {
			d.Failed = true
			return "", fmt.Errorf("invalid UTF8")
		}
		out.WriteRune(r)
		d.Pending = d.Pending[size:]
	}
	if final && len(d.Pending) > 0 {
		d.Failed = true
		return "", fmt.Errorf("incomplete UTF8")
	}
	return out.String(), nil
}
func main() {
	input := []byte("中😀Go")
	decoder := &Decoder{}
	text := ""
	for i, part := range [][]byte{input[:2], input[2:5], input[5:]} {
		piece, err := decoder.Feed(part, i == 2)
		if err != nil {
			panic(err)
		}
		text += piece
	}
	fmt.Printf("text=%s runes=%d\n", text, utf8.RuneCountInString(text))
	bad := &Decoder{}
	_, err := bad.Feed([]byte{0xff}, true)
	fmt.Printf("invalid=%t\n", err != nil)
	short := &Decoder{}
	_, err = short.Feed([]byte{0xe4, 0xb8}, true)
	fmt.Printf("incomplete=%t\n", err != nil)
}
