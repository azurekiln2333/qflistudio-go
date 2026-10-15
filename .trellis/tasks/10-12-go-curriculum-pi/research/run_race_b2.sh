#!/usr/bin/env bash
set -u
export GOMAXPROCS=2
export GOFLAGS=-p=1
export CGO_ENABLED=1
export PATH=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go/bin:$PATH
cd /mnt/d/MyNewProjects/qfli_go/tool/go_curriculum/samples || exit 2
# single-file concurrent topics: build with -race then run
for t in T071 T072 T073 T074 T075 T076 T079 T082 T083 T084; do
  echo "===== $t -race run ====="
  ( cd "$t" && go run -race main.go >/dev/null 2>/tmp/race_err && echo "RACE-OK" || { echo "FAIL"; cat /tmp/race_err | tail -n 20; } )
done
echo "===== T119 -race test (concurrent wordfreq) ====="
( cd T119 && go test -race . 2>&1 | tail -n 6 )
echo "===== T120 -race test ====="
( cd T120 && go test -race . 2>&1 | tail -n 6 )
