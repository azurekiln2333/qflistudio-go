package main

import (
	"encoding/binary"
	"fmt"
)

func pack(enabled bool, scale, value uint16) (uint16, error) {
	if scale > 7 || value > 4095 {
		return 0, fmt.Errorf("field overflow")
	}
	word := scale<<12 | value
	if enabled {
		word |= 1 << 15
	}
	return word, nil
}
func main() {
	word, err := pack(true, 3, 1234)
	if err != nil {
		panic(err)
	}
	var bytes [2]byte
	binary.BigEndian.PutUint16(bytes[:], word)
	restored := binary.BigEndian.Uint16(bytes[:])
	enabled := restored&(1<<15) != 0
	scale := (restored >> 12) & 7
	value := restored & 0x0fff
	again, err := pack(enabled, scale, value)
	if err != nil {
		panic(err)
	}
	fmt.Printf("enabled=%t range=%d value=%d\nwire=%x\nroundtrip=%t\n", enabled, scale, value, bytes, again == word)
	_, err = pack(false, 8, 0)
	fmt.Printf("overflow=%t\n", err != nil)
}
