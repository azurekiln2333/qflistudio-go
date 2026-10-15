#!/usr/bin/env bash
set -u
export GOMAXPROCS=2
export GOFLAGS=-p=1
export CGO_ENABLED=1
export PATH=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go/bin:$PATH
cd /mnt/d/MyNewProjects/qfli_go/tool/go_curriculum/samples || exit 2
echo "go: $(go version)"
for t in T077 T078 T080 T081; do
  echo "===== $t -race ====="
  ( cd "$t" && go test -race . 2>&1 | tail -n 6 )
done
echo "===== T080 bench ====="
( cd T080 && go test -bench . -benchmem -run '^$' . 2>&1 | tail -n 8 )
echo "===== T108 bench ====="
( cd T108 && go test -bench . -benchmem -run '^$' . 2>&1 | tail -n 8 )
echo "===== T114 bench ====="
( cd T114 && go test -bench . -benchmem -run '^$' . 2>&1 | tail -n 8 )
