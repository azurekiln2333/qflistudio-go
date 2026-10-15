#!/usr/bin/env bash
# Real `go test -race` gate for concurrency topics, run inside WSL with the
# project-pinned linux Go SDK and the distro's existing gcc. No downloads.
set -u
export GOROOT=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go
export PATH="$GOROOT/bin:$PATH"
export GOMAXPROCS=2
export GOFLAGS=-p=1
export GOTOOLCHAIN=local
export GOCACHE=/tmp/qfli-race-cache
export CGO_ENABLED=1

ROOT=/mnt/d/MyNewProjects/qfli_go/tool/go_curriculum/samples
FAIL=0
for t in "$@"; do
  dir="$ROOT/$t"
  if [ ! -d "$dir" ]; then echo "MISS $t"; FAIL=1; continue; fi
  out=$(cd "$dir" && go test -race ./... 2>&1)
  rc=$?
  if [ $rc -eq 0 ]; then
    echo "RACE-OK   $t"
  else
    echo "RACE-FAIL $t (rc=$rc)"
    echo "$out" | tail -20
    FAIL=1
  fi
done
exit $FAIL
