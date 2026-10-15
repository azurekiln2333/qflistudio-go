#!/usr/bin/env bash
set -u
export GOMAXPROCS=2
export GOFLAGS=-p=1
export PATH=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go/bin:$PATH
cd /mnt/d/MyNewProjects/qfli_go/tool/go_curriculum/samples || exit 2
for t in T061 T062 T063 T064 T065 T068 T069 T070; do
  echo "##### $t go run ."
  ( cd "$t" && go run . 2>&1 | head -n 12 )
done
echo "##### T070 generate"
( cd T070 && go generate ./... 2>&1 && echo "GEN-OK" )
echo "##### T069 tags special"
( cd T069 && go run -tags special . 2>&1 )
echo "##### go vet on module topics"
for t in T061 T062 T063 T064 T065 T068 T069 T070; do
  ( cd "$t" && go vet ./... 2>&1 && echo "$t vet-ok" )
done
