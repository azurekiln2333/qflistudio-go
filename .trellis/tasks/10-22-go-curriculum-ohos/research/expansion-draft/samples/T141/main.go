package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"io"
)

func writeFrame(out *bytes.Buffer, text string) {
	var header [2]byte
	binary.BigEndian.PutUint16(header[:], uint16(len(text)))
	out.Write(header[:])
	out.WriteString(text)
}
func readFrame(reader io.Reader) ([]byte, error) {
	var header [2]byte
	if _, err := io.ReadFull(reader, header[:]); err != nil {
		return nil, err
	}
	length := int(binary.BigEndian.Uint16(header[:]))
	if length > 8 {
		return nil, fmt.Errorf("frame over budget")
	}
	payload := make([]byte, length)
	_, err := io.ReadFull(reader, payload)
	return payload, err
}
func main() {
	var wire bytes.Buffer
	writeFrame(&wire, "cat")
	writeFrame(&wire, "go")
	frames := []string{}
	for {
		payload, err := readFrame(&wire)
		if err == io.EOF {
			break
		}
		if err != nil {
			panic(err)
		}
		frames = append(frames, string(payload))
	}
	fmt.Printf("frames=%v\n", frames)
	_, err := readFrame(bytes.NewReader([]byte{0, 9}))
	fmt.Printf("oversized=%t\n", err != nil)
	_, err = readFrame(bytes.NewReader([]byte{0, 3, 'x'}))
	fmt.Printf("truncated=%t\n", err == io.ErrUnexpectedEOF)
}
