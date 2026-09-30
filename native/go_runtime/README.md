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

Verified on an OpenHarmony x86_64 target with the pinned OHOS compiler: all three
Flutter FFI integration tests pass. Android APK packaging covers all three ABIs;
Android device execution and OpenHarmony arm64 execution require separate device
verification.
