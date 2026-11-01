package main

import (
	"encoding/binary"
	"fmt"
	"math"
)

func roundtrip(value float64) (float64, []byte) {
	wire := make([]byte, 8)
	binary.BigEndian.PutUint64(wire, math.Float64bits(value))
	return math.Float64frombits(binary.BigEndian.Uint64(wire)), wire
}
func main() {
	for _, value := range []float64{1.5, math.Copysign(0, -1)} {
		restored, wire := roundtrip(value)
		fmt.Printf("wire=%x same-bits=%t negative=%t\n", wire, math.Float64bits(value) == math.Float64bits(restored), math.Signbit(restored))
	}
}
