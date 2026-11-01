package main

import (
	"encoding/binary"
	"fmt"
)

func encode(ids []uint64) []byte {
	out := []byte{}
	previous := uint64(0)
	for _, id := range ids {
		if id < previous {
			panic("IDs not ordered")
		}
		var buffer [10]byte
		n := binary.PutUvarint(buffer[:], id-previous)
		out = append(out, buffer[:n]...)
		previous = id
	}
	return out
}
func decode(wire []byte) ([]uint64, error) {
	ids := []uint64{}
	previous := uint64(0)
	for len(wire) > 0 {
		delta, n := binary.Uvarint(wire)
		if n <= 0 {
			return nil, fmt.Errorf("truncated or overflow varint")
		}
		if delta > ^uint64(0)-previous {
			return nil, fmt.Errorf("ID overflow")
		}
		previous += delta
		ids = append(ids, previous)
		wire = wire[n:]
	}
	return ids, nil
}
func main() {
	wire := encode([]uint64{100, 101, 130, 500})
	ids, err := decode(wire)
	if err != nil {
		panic(err)
	}
	fmt.Printf("ids=%v\nbytes=%d\n", ids, len(wire))
	_, err = decode(wire[:len(wire)-1])
	fmt.Printf("truncated=%t\n", err != nil)
}
