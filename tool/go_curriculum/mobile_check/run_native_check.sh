#!/usr/bin/env bash
# Host-native runtime check: drive the SHIPPED native runtime path (runGo in
# native/go_runtime) over candidate samples, using go test -overlay so no real
# native file is modified. Vendored Yaegi fixes + projectSourceFS + stdlib
# symbols are exercised, unlike a bare Yaegi probe.
#
# Usage (from repo root, or pass QFLI_ROOT):
#   bash tool/go_curriculum/mobile_check/run_native_check.sh <samples-dir> <out.json>
# Evidence level: HOST-native interpreter. NOT a device run.
set -eu

ROOT=${QFLI_ROOT:-/mnt/d/MyNewProjects/qfli_go}
GOROOT=${QFLI_GOROOT:-$ROOT/native/build/go-linux-1.27.1/go}
export GOROOT
export PATH="$GOROOT/bin:$PATH"
export GOTOOLCHAIN=local
export GOMAXPROCS=2
export GOFLAGS=-p=1
export GOCACHE=${GOCACHE:-/tmp/qfli-nativecheck-cache}

SAMPLES=$1
OUT=$2
NATIVE=$ROOT/native/go_runtime
CHECKSRC=$ROOT/tool/go_curriculum/mobile_check/native_hostcheck_test.go
OVERLAY=/tmp/qfli_overlay.json

cat > "$OVERLAY" <<EOF
{"Replace": {"$NATIVE/hostcheck_injected_test.go": "$CHECKSRC"}}
EOF

export QFLI_HOSTCHECK_DIR=$SAMPLES
export QFLI_HOSTCHECK_OUT=$OUT
cd "$NATIVE"
go test -mod=vendor -tags hostcheck -overlay "$OVERLAY" -run TestHostNativeCandidateSamples -v ./...
