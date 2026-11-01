package main

import (
	"fmt"
	"math/big"
)

func main() {
	share := big.NewRat(10, 3)
	sum := new(big.Rat)
	for i := 0; i < 3; i++ {
		sum.Add(sum, share)
	}
	fmt.Printf("share=%s displayed=%s\n", share.RatString(), share.FloatString(2))
	fmt.Printf("exact-total=%s preserved=%t\n", sum.RatString(), sum.Cmp(big.NewRat(10, 1)) == 0)
	fmt.Printf("displayed-total=%d.%02d\n", (333*3)/100, (333*3)%100)
}
