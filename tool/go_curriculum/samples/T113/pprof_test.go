// pprof_test.go 为 T113 提供一个可采样的基准，供 CPU/内存剖面采集：
//   go test -bench . -cpuprofile=cpu.out .
//   go tool pprof cpu.out
package main

import "testing"

func BenchmarkHot(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = hot(1000)
	}
}
