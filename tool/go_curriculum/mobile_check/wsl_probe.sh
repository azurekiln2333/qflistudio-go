#!/usr/bin/env bash
set -e
export GOROOT=/mnt/d/MyNewProjects/qfli_go/native/build/go-linux-1.27.1/go
export PATH="$GOROOT/bin:$PATH"
echo "go: $(go version)"
echo "gcc: $(command -v gcc)"
echo "CGO: $(go env CGO_ENABLED)"
