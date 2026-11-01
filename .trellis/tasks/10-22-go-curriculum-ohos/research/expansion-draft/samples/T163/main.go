package main

import (
	"fmt"
	"math/big"
)

func choose(n, k int) (*big.Int, error) {
	if n < 0 || k < 0 || k > n {
		return nil, fmt.Errorf("invalid combination")
	}
	if k > n-k {
		k = n - k
	}
	result := big.NewInt(1)
	for i := 1; i <= k; i++ {
		result.Mul(result, big.NewInt(int64(n-k+i)))
		result.Quo(result, big.NewInt(int64(i)))
	}
	return result, nil
}
func main() {
	value, err := choose(70, 35)
	if err != nil {
		panic(err)
	}
	fmt.Printf("C70,35=%s\n", value.String())
	fmt.Printf("fits-int64=%t\n", value.IsInt64())
	boundary, err := choose(0, 0)
	if err != nil {
		panic(err)
	}
	fmt.Printf("C0,0=%s\n", boundary.String())
	_, err = choose(3, 4)
	fmt.Printf("invalid=%t\n", err != nil)
}
