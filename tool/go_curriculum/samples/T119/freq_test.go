// freq_test.go 是 T119 的端到端测试：并发统计必须与串行一致。
package main

import "testing"

func TestParallelMatchesSerial(t *testing.T) {
	texts := []string{
		"a b c",
		"b c d",
		"c d e",
		"a a a",
	}
	serial := make(map[string]int)
	for _, tx := range texts {
		merge(serial, countWords(tx))
	}
	for workers := 1; workers <= 4; workers++ {
		got := CountParallel(texts, workers)
		if !sameCounts(serial, got) {
			t.Fatalf("workers=%d: parallel %v != serial %v", workers, got, serial)
		}
	}
}

func TestSortedKeysDeterministic(t *testing.T) {
	m := map[string]int{"b": 1, "a": 2, "c": 3}
	keys := sortedKeys(m)
	want := []string{"a", "b", "c"}
	for i := range want {
		if keys[i] != want[i] {
			t.Fatalf("keys = %v, want %v", keys, want)
		}
	}
}
