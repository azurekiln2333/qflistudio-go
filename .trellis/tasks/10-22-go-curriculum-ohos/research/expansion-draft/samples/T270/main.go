package main

import (
	"encoding/binary"
	"fmt"
)

func zigzag(value int64) uint64  { return uint64(value<<1) ^ uint64(value>>63) }
func restore(value uint64) int64 { return int64(value>>1) ^ -int64(value&1) }
func main() {
	for _, value := range []int64{0, -1, 1, -2, 2, -9223372036854775808, 9223372036854775807} {
		encoded := zigzag(value)
		var buffer [10]byte
		n := binary.PutUvarint(buffer[:], encoded)
		read, size := binary.Uvarint(buffer[:n])
		fmt.Printf("%d zigzag=%d bytes=%d same=%t\n", value, encoded, n, size == n && restore(read) == value)
	}
}
