#!/bin/bash
# Invoked by the Runner build phase on macOS; use the active Xcode SDK.
set -euo pipefail

: "${SRCROOT:?Build the iOS Runner from Xcode or flutter build ios}"
: "${DERIVED_FILE_DIR:?Xcode must provide DERIVED_FILE_DIR}"
project_root="$(cd "$SRCROOT/.." && pwd)"
runtime_dir="$project_root/native/go_runtime"
output_dir="$DERIVED_FILE_DIR/qfli_go_runtime"
export PATH="/opt/homebrew/bin:/usr/local/go/bin:/usr/local/bin:$PATH"
go_bin="${QFLI_GO_EXECUTABLE:-go}"
if ! go_bin="$(command -v "$go_bin")"; then
  echo "error: Install the official Go SDK on this Mac or set QFLI_GO_EXECUTABLE to its go executable." >&2
  exit 1
fi

platform="${PLATFORM_NAME:?Xcode must provide PLATFORM_NAME}"
case "$platform" in
  iphoneos) minimum_flag="-mios-version-min=${IPHONEOS_DEPLOYMENT_TARGET:-13.0}" ;;
  iphonesimulator) minimum_flag="-mios-simulator-version-min=${IPHONEOS_DEPLOYMENT_TARGET:-13.0}" ;;
  *) echo "error: Unsupported Go runtime platform: $platform" >&2; exit 1 ;;
esac
sdk="${SDKROOT:-$platform}"
sdk_path="$(xcrun --sdk "$sdk" --show-sdk-path)"
clang="$(xcrun --sdk "$sdk" --find clang)"
architectures="${ARCHS:-${CURRENT_ARCH:-}}"
if [[ -z "$architectures" ]]; then
  echo "error: Xcode must provide ARCHS for the Go runtime." >&2
  exit 1
fi

export GOOS=ios CGO_ENABLED=1 GOTOOLCHAIN=local GOWORK=off
# Keep generated dependencies and caches inside Xcode's derived output.
export GOCACHE="$output_dir/cache" GOPATH="$output_dir/gopath"
mkdir -p "$output_dir"
archives=()
headers=()
for architecture in $architectures; do
  case "$platform/$architecture" in
    iphoneos/arm64|iphonesimulator/arm64) export GOARCH=arm64 ;;
    iphonesimulator/x86_64) export GOARCH=amd64 ;;
    *) echo "error: Unsupported Go runtime architecture: $platform/$architecture" >&2; exit 1 ;;
  esac
  architecture_dir="$output_dir/$platform-$architecture"
  mkdir -p "$architecture_dir"
  # Go parses CC as a command line. Including the SDK/target arguments here
  # also invalidates its cgo cache when Xcode changes SDK or deployment target.
  export CC="\"$clang\" -arch $architecture -isysroot \"$sdk_path\" $minimum_flag"
  archive="$architecture_dir/libqfli_go_runtime.a"
  echo "Building the bundled Go interpreter for $platform/$architecture"
  (cd "$runtime_dir" && "$go_bin" build -mod=vendor -trimpath -buildmode=c-archive -o "$archive" .)
  archives+=("$archive")
  headers+=("$architecture_dir/libqfli_go_runtime.h")
done

xcrun --sdk "$sdk" lipo -create "${archives[@]}" -output "$output_dir/libqfli_go_runtime.a"
cp "${headers[0]}" "$output_dir/libqfli_go_runtime.h"
echo "Bundled Go interpreter: $output_dir/libqfli_go_runtime.a"
