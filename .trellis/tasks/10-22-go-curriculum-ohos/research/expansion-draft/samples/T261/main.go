package main

import (
	"encoding/binary"
	"fmt"
	"hash/crc32"
)

func encode(payload []byte) []byte {
	if len(payload) > 1024 {
		panic("payload budget")
	}
	frame := make([]byte, 3+len(payload)+4)
	frame[0] = 1
	binary.BigEndian.PutUint16(frame[1:3], uint16(len(payload)))
	copy(frame[3:], payload)
	binary.BigEndian.PutUint32(frame[len(frame)-4:], crc32.ChecksumIEEE(frame[:len(frame)-4]))
	return frame
}
func decode(frame []byte) (string, error) {
	if len(frame) < 7 || frame[0] != 1 {
		return "", fmt.Errorf("version/header")
	}
	size := int(binary.BigEndian.Uint16(frame[1:3]))
	if size > 1024 || len(frame) != 3+size+4 {
		return "", fmt.Errorf("size")
	}
	want := binary.BigEndian.Uint32(frame[len(frame)-4:])
	if crc32.ChecksumIEEE(frame[:len(frame)-4]) != want {
		return "", fmt.Errorf("checksum")
	}
	return string(frame[3 : 3+size]), nil
}
func main() {
	wire := encode([]byte("hello"))
	text, err := decode(wire)
	if err != nil {
		panic(err)
	}
	fmt.Printf("payload=%s\n", text)
	bad := append([]byte(nil), wire...)
	bad[0] = 2
	_, err = decode(bad)
	fmt.Printf("version-rejected=%t\n", err != nil)
	wire[3] ^= 1
	_, err = decode(wire)
	fmt.Printf("tampered=%t\n", err != nil)
}
