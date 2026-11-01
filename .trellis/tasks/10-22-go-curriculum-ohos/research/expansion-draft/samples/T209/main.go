package main

import (
	"fmt"
	"hash/crc32"
)

func main() {
	chunks := [][]byte{[]byte("sensor:"), []byte("north:"), []byte("21.5")}
	rolling := uint32(0)
	all := []byte{}
	for _, chunk := range chunks {
		rolling = crc32.Update(rolling, crc32.IEEETable, chunk)
		all = append(all, chunk...)
	}
	fmt.Printf("same=%t\n", rolling == crc32.ChecksumIEEE(all))
	all[len(all)-1] ^= 1
	fmt.Printf("changed=%t\n", rolling != crc32.ChecksumIEEE(all))
	fmt.Printf("empty=%d\n", crc32.ChecksumIEEE(nil))
}
