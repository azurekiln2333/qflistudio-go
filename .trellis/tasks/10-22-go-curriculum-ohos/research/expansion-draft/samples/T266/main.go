package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
)

type Unpacker struct {
	Pending []byte
	Failed  bool
}

func (u *Unpacker) Feed(chunk []byte) ([]string, error) {
	if u.Failed {
		return nil, fmt.Errorf("failed state")
	}
	u.Pending = append(u.Pending, chunk...)
	frames := []string{}
	for len(u.Pending) >= 2 {
		n := int(binary.BigEndian.Uint16(u.Pending[:2]))
		if n > 32 {
			u.Failed = true
			return nil, fmt.Errorf("frame budget")
		}
		if len(u.Pending) < 2+n {
			break
		}
		frames = append(frames, string(u.Pending[2:2+n]))
		u.Pending = u.Pending[2+n:]
	}
	return frames, nil
}
func main() {
	var wire bytes.Buffer
	for _, text := range []string{"cat", "go"} {
		var header [2]byte
		binary.BigEndian.PutUint16(header[:], uint16(len(text)))
		wire.Write(header[:])
		wire.WriteString(text)
	}
	all := wire.Bytes()
	u := &Unpacker{}
	result := []string{}
	for _, part := range [][]byte{all[:1], all[1:4], all[4:6], all[6:]} {
		frames, err := u.Feed(part)
		if err != nil {
			panic(err)
		}
		result = append(result, frames...)
	}
	fmt.Printf("frames=%v\npending=%d\n", result, len(u.Pending))
	_, err := u.Feed([]byte{0, 33})
	fmt.Printf("oversize=%t\n", err != nil)
}
