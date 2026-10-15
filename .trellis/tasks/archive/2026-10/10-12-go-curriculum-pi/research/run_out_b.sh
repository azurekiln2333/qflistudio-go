#!/usr/bin/env bash
set -u
export GOMAXPROCS=2
export GOFLAGS=-p=1
export PATH=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go/bin:$PATH
cd /mnt/d/MyNewProjects/qfli_go/tool/go_curriculum/samples || exit 2
echo "=== tests: -v -run . (first lines) ==="
for t in T077 T078 T080 T081 T099 T100 T101 T102 T103 T104 T105 T106 T107 T108 T109 T110 T111 T114; do
  echo "##### $t"
  ( cd "$t" && go test -v . 2>&1 | grep -E '^(=== RUN|--- PASS|--- FAIL|PASS|FAIL|ok)' | head -n 8 )
done
echo "=== T080 bench summary ==="
( cd T080 && go test -bench . -benchmem -run '^$' . 2>&1 | grep -E '^Benchmark' )
echo "=== T108 bench summary ==="
( cd T108 && go test -bench . -benchmem -run '^$' . 2>&1 | grep -E '^Benchmark' )
echo "=== T114 bench summary ==="
( cd T114 && go test -bench . -benchmem -run '^$' . 2>&1 | grep -E '^Benchmark' )
