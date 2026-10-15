#!/usr/bin/env bash
set -u
export GOMAXPROCS=2
export GOFLAGS=-p=1
export CGO_ENABLED=1
export PATH=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go/bin:$PATH
cd /mnt/d/MyNewProjects/qfli_go/tool/go_curriculum/samples || exit 2
echo "== -race runs for concurrent/error topics =="
for t in T058; do
  ( cd "$t" && go run -race main.go >/dev/null 2>/tmp/e && echo "$t RACE-OK" || { echo "$t FAIL"; tail -n 15 /tmp/e; } )
done
echo "== vet all T041-T060 =="
for n in $(seq -w 41 60); do
  t="T0$n"
  if [ -f "$t/go.mod" ]; then
    ( cd "$t" && go vet ./... >/dev/null 2>/tmp/e && echo "$t vet-ok" || { echo "$t vet-FAIL"; tail -n 5 /tmp/e; } )
  else
    ( cd "$t" && GO111MODULE=off go vet main.go >/dev/null 2>/tmp/e && echo "$t vet-ok" || { echo "$t vet-FAIL"; tail -n 5 /tmp/e; } )
  fi
done
