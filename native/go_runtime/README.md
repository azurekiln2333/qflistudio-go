# Bundled Go interpreter

The mobile runtime vendors Yaegi at the version pinned in `go.mod`. The vendored
`interp/interp.go` and `interp/run.go` include local fixes for path evaluation:

- Recover panics in the evaluation goroutine and in interpreted `go` calls,
  returning a `Panic` error to the caller instead of terminating the host.
- Transfer results through a channel so cancellation does not race with result
  assignment, and stop interpreted execution when the main task returns.

The runtime's output buffers are synchronized because interpreted goroutines
can write while a run is completing or being cancelled.

After refreshing the dependency with `go mod vendor`, reapply these fixes and
run `go test -mod=vendor ./...` before rebuilding the libraries with
`tool/build_go_runtime.ps1`. The script builds Android arm64-v8a, armeabi-v7a,
and x86_64 libraries with 16 KB ELF page alignment, plus OpenHarmony arm64-v8a
and x86_64.

## OpenHarmony Toolchain

OpenHarmony needs the `openharmony` target from the community
[OHOS Go port](https://github.com/sysit/ohos-go), pinned to release
`v1.27.1-ohos`, commit `f2cb44316b789bc12d0b5fd562d853f6fec3ab28`.
Standard upstream `GOOS=linux` libraries use initial-exec TLS relocations which
OpenHarmony's musl loader rejects during `dlopen`. The OHOS port uses dynamic
TLS for shared libraries and supports arm64 and amd64.

Build the Windows host toolchain with an official Go SDK (1.24.6 or newer):

```powershell
./tool/build_ohos_go_toolchain.ps1 -BootstrapGoExecutable <official-go.exe>
```

The script prints the resulting `go.exe` path. Pass that path separately from
the official Android build SDK:

```powershell
./tool/build_go_runtime.ps1 -GoExecutable <official-go.exe> `
  -OhosGoExecutable <ohos-go.exe> -AndroidNdk <ndk-root> -OhosSdk <sdk-root>
```

The OHOS stage sets `GOTOOLCHAIN=local` and uses a separate generated Go cache
to avoid mixing relocation definitions from different compilers. Both scripts
restore their process environment when they finish. SDK trees and caches stay
under ignored `native/build/`.

Device verification is in `integration_test/go_native_test.dart`: multi-file
execution, panic recovery, and cancellation. The OpenHarmony C smoke loader is
under `testdata/smoke/` so it is not linked into the shared runtime itself.

## iOS Archive

The Runner target invokes `tool/build_ios_go_runtime.sh` before linking. The
script uses the active Xcode SDK, deployment target, and architectures to build
this module with `GOOS=ios`, `CGO_ENABLED=1`, `-mod=vendor`, and
`-buildmode=c-archive`. It supports arm64 devices and arm64/x86_64 simulators.
Multi-architecture simulator output is combined with `lipo`; generated archives,
headers, and Go caches remain under Xcode's `DERIVED_FILE_DIR`.

Install an official Go SDK on the build Mac. The script checks the standard
installer and Homebrew locations; a custom installation can be selected with
the Xcode build setting `QFLI_GO_EXECUTABLE=/absolute/path/to/go`.

`ios/Flutter/NativeGoRuntime.xcconfig` links the archive and retains the public
`QfliGoRun`, `QfliGoCancel`, and `QfliGoFree` symbols. Debug and Release include
this configuration; Profile uses Release. Dart resolves these functions with
`DynamicLibrary.process()`. Android and OpenHarmony keep their shared-library
loader and existing signatures.

Apple compilation and device execution require a Mac with Xcode. They were
skipped on this Windows host; only source/configuration and shell syntax were
reviewed. Run `integration_test/go_native_test.dart` on an iOS device or simulator
when that environment is available.

## Platform Evidence

| Target | Verified behavior | Limits |
| --- | --- | --- |
| Windows amd64, Go 1.27.1 | Actual app toolchain tests cover run/build/test/fmt/vet/tidy, invalid code, missing SDK, and cancellation with output pipes closing; all eight native source tests and vet pass | Native source tests use CGO_ENABLED=0 because no host C compiler is available; Windows Flutter GUI packaging was not performed |
| Android x86_64, emulator-5560 | All three Flutter FFI integration cases pass: multi-file execution, main/worker panic and os.Exit handling, and infinite-loop cancellation | arm64/armv7 device execution is untested; the APK contains all three ABIs and every native LOAD segment has 16 KB alignment |
| Linux amd64, WSL qfli-java-build, Go 1.27.1 | Actual SDK command checks cover the six desktop actions, compiled output, invalid source, and module execution; all eight native source tests and vet pass with CGO_ENABLED=1 | These are backend/source checks; no Linux Flutter SDK or GUI execution was used |
| OpenHarmony x86_64 | Earlier device evidence records all three FFI cases passing with the pinned OHOS Go port | Not rerun in this session; arm64 device execution needs separate verification |
| iOS | Runner routing, process-symbol loading, archive build and link integration implemented; shell syntax passes | No Xcode build or Apple device execution on this host |
| macOS | Existing official SDK backend retained; platform routing covered by Dart tests | No macOS host available for command or GUI execution |

Desktop execution requires an installed Go SDK visible to the application.
`goRuntimeBackendFor` in `lib/go_platform.dart` is shared by the runner, profile,
and native integration eligibility. Desktop metadata is `official-go-sdk` /
`requires-sdk`; mobile metadata is `embedded-go-runtime` / `available`.
Unsupported targets use `unavailable`.
