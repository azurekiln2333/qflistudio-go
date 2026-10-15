#!/usr/bin/env bash
set -u
export GOMAXPROCS=2
export GOFLAGS=-p=1
export PATH=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go/bin:$PATH
cd /mnt/d/MyNewProjects/qfli_go/tool/go_curriculum/samples || exit 2
for n in $(seq -w 41 60); do
  t="T0$n"
  echo "########## $t"
  if [ -f "$t/go.mod" ]; then
    ( cd "$t" && go run . 2>&1 )
  else
    ( cd "$t" && GO111MODULE=off go run main.go 2>&1 )
  fi
done
