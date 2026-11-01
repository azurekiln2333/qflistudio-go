#!/bin/bash
# Invoked after Flutter embedding and before Xcode signs the enclosing app.
set -euo pipefail

: "${SRCROOT:?Build the macOS Runner from Xcode or flutter build macos}"
: "${DERIVED_FILE_DIR:?Xcode must provide DERIVED_FILE_DIR}"
: "${TARGET_BUILD_DIR:?Xcode must provide TARGET_BUILD_DIR}"
: "${FRAMEWORKS_FOLDER_PATH:?Xcode must provide FRAMEWORKS_FOLDER_PATH}"
project_root="$(cd "$SRCROOT/.." && pwd)"
runtime_dir="$project_root/native/go_runtime"
output_dir="$DERIVED_FILE_DIR/qfli_go_runtime"
export PATH="/opt/homebrew/bin:/usr/local/go/bin:/usr/local/bin:$PATH"
go_bin="${QFLI_GO_EXECUTABLE:-go}"
if ! go_bin="$(command -v "$go_bin")"; then
  echo "error: Install the official Go SDK on this Mac or set QFLI_GO_EXECUTABLE to its go executable." >&2
  exit 1
fi
architectures="${ARCHS:-${CURRENT_ARCH:-}}"
if [[ -z "$architectures" ]]; then
  echo "error: Xcode must provide ARCHS for the Go runtime." >&2
  exit 1
fi
sdk_path="$(xcrun --sdk macosx --show-sdk-path)"
clang="$(xcrun --sdk macosx --find clang)"
export GOOS=darwin CGO_ENABLED=1 GOTOOLCHAIN=local GOWORK=off GOENV=off GOPROXY=off GOSUMDB=off
export GO_TELEMETRY_CHILD=2
export GOCACHE="$output_dir/cache" GOPATH="$output_dir/gopath"
mkdir -p "$output_dir"
libraries=()
for architecture in $architectures; do
  case "$architecture" in
    arm64) export GOARCH=arm64 ;;
    x86_64) export GOARCH=amd64 ;;
    *) echo "error: Unsupported macOS Go runtime architecture: $architecture" >&2; exit 1 ;;
  esac
  architecture_dir="$output_dir/$architecture"
  mkdir -p "$architecture_dir"
  export CC="\"$clang\" -arch $architecture -isysroot \"$sdk_path\" -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET:-10.15}"
  library="$architecture_dir/libqfli_go_runtime.dylib"
  (cd "$runtime_dir" && "$go_bin" build -mod=vendor -trimpath -buildmode=c-shared -o "$library" .)
  libraries+=("$library")
done
universal_library="$output_dir/libqfli_go_runtime.dylib"
xcrun --sdk macosx lipo -create "${libraries[@]}" -output "$universal_library"
xcrun --sdk macosx install_name_tool -id '@rpath/libqfli_go_runtime.dylib' "$universal_library"
bundle_directory="$TARGET_BUILD_DIR/$FRAMEWORKS_FOLDER_PATH"
mkdir -p "$bundle_directory"
bundled_library="$bundle_directory/libqfli_go_runtime.dylib"
cp "$universal_library" "$bundled_library"
if [[ "${CODE_SIGNING_ALLOWED:-YES}" == YES ]]; then
  signing_identity="${EXPANDED_CODE_SIGN_IDENTITY:--}"
  if [[ -z "$signing_identity" ]]; then signing_identity=-; fi
  /usr/bin/codesign --force --sign "$signing_identity" --timestamp=none "$bundled_library"
fi
echo "Bundled Go IDE runtime: $bundled_library"
