# Research: GitHub Actions native runtime build

- Query: Determine a practical GitHub Actions workflow for this repository's native Go runtime on a Windows runner, including Android NDK, OpenHarmony SDK/toolchain, and artifact download behavior.
- Scope: mixed (internal repository plus GitHub Actions documentation)
- Date: 2026-11-17

## Findings

### Internal build contract

- `tool/build_go_runtime.ps1:1-6` accepts an official Go executable, an OHOS Go executable, an Android NDK root, and an OpenHarmony SDK root.
- `tool/build_go_runtime.ps1:48-53` fails immediately when `ANDROID_NDK_HOME` or `OHOS_SDK_HOME` is missing.
- `tool/build_go_runtime.ps1:71-95` builds Android `arm64-v8a`, `armeabi-v7a`, and `x86_64` using the NDK clang wrappers and `-Wl,-z,max-page-size=16384`, then strips each shared library.
- `tool/build_go_runtime.ps1:97-126` builds OpenHarmony `arm64-v8a` and `x86_64` with the OHOS Go port and OpenHarmony SDK clang/sysroot, then strips each library.
- `tool/build_go_runtime.ps1:128-139` writes `native/build/bundled-go-runtime-build.json` with source hash, build-input hashes, toolchain hashes, offline settings, library hashes, and byte sizes.
- `tool/build_ohos_go_toolchain.ps1:5-17` clones `https://github.com/sysit/ohos-go.git` at tag `v1.27.1-ohos` and verifies commit `f2cb44316b789bc12d0b5fd562d853f6fec3ab28`.
- `tool/build_ohos_go_toolchain.ps1:19-45` bootstraps the OHOS Go host toolchain with the official Go SDK and checks that `openharmony/amd64` and `openharmony/arm64` are available.
- `native/go_runtime/android-cc.cmd:1-3` hard-codes the Windows NDK layout under `toolchains\\llvm\\prebuilt\\windows-x86_64\\bin`.
- `native/go_runtime/ohos-cc.cmd:1-3` requires an OpenHarmony SDK with `native/llvm/bin/clang.exe` and `native/sysroot`.
- `.trellis/spec/backend/native-go-runtime.md:25-50` requires Go 1.24+, official Go 1.27.1 for release builds, `-mod=vendor`, `GOTOOLCHAIN=local`, offline module settings, and the pinned OHOS port. `.trellis/spec/backend/native-go-runtime.md:100-117` requires native Go tests/vet plus alignment and packaging checks; a successful build alone does not prove device execution.

### Windows runner setup

- A `windows-2022` runner is the right host for the current PowerShell scripts because the Android compiler wrapper and OHOS compiler wrapper expect Windows executable paths.
- `actions/setup-go@v5` can install a pinned official Go SDK and supports a `go-version` input. The action documentation recommends `permissions: contents: read` and warns that setup-go's cache defaults target module files; this repository's native build is vendor/offline, so workflow caching should be disabled or explicitly isolated.
- `android-actions/setup-android@v4` installs command-line tools, accepts licenses, and can install additional SDK packages. It is useful for the Android SDK but does not itself install the NDK. The workflow must install the exact NDK package separately with `sdkmanager` or use a runner-provided NDK path.
- The build script expects the NDK root itself, not the Android SDK root. The workflow must resolve the installed NDK directory and set `ANDROID_NDK_HOME` to that path.

### OpenHarmony dependency

- No repository file provides a reproducible public OpenHarmony SDK download URL. The local build depends on a DevEco/OpenHarmony SDK tree with `native/llvm` and `native/sysroot`; this is separate from the OHOS Go source toolchain.
- The OHOS Go source is reproducible from GitHub by commit, but `tool/build_ohos_go_toolchain.ps1` still compiles it on the runner and can take significant time and disk space.
- A workflow that unconditionally calls `tool/build_go_runtime.ps1` cannot succeed on a clean hosted runner unless the OpenHarmony SDK is provisioned first. The workflow therefore needs one of these explicit contracts:
  1. a repository/org secret or variable containing a downloadable SDK archive URL plus optional SHA-256, or
  2. a checked-in/private release asset fetched with a token, or
  3. an Android/Windows-only default job with a separately gated OHOS job.
- Recommended MVP: make the workflow manually dispatchable and require `OHOS_SDK_ARCHIVE_URL` (and preferably `OHOS_SDK_SHA256`) for the full Android+OHOS build. Keep a fast Android+Windows path available when the OHOS URL is not configured, with a clear skipped/blocked summary. Do not commit the SDK or its credentials.

### Artifact behavior and download UX

- `actions/upload-artifact@v4` creates immutable artifacts. The same artifact name cannot be uploaded more than once in a job or across matrix jobs; names must include platform/ABI or use one final upload step.
- `upload-artifact@v4` excludes hidden files by default, but the runtime outputs are ordinary files. Use `if-no-files-found: error` so a missing ABI fails the run instead of producing a misleading successful artifact.
- Large shared libraries are already compressed binaries; `compression-level: 0` is appropriate for faster upload. The build JSON and text manifest can be uploaded with the binaries in one artifact, or in a separate small provenance artifact.
- Artifacts are downloaded from the workflow run summary page under the Artifacts section. GitHub downloads a ZIP archive; users cannot download individual files directly from the artifact UI. The action exposes an `artifact-url` output, but the URL requires GitHub login and remains valid only while the run/artifact exists.
- Set `retention-days` explicitly (for example 14 or 30) to limit storage. The documented maximum is 90 days unless repository policy changes.
- Separate artifact names are clearer for this project: `native-runtime-android`, `native-runtime-ohos`, `native-runtime-windows`, and `native-runtime-provenance`. A single `native-runtime-bundle` ZIP is easier for users who want all outputs; if both are uploaded, avoid duplicate uploads of the same path.

### Suggested workflow shape

1. Trigger on `workflow_dispatch` and `push` to the feature branch (or `main` after merge).
2. Run on `windows-2022`.
3. Checkout with `actions/checkout@v4`.
4. Install official Go 1.27.1 with `actions/setup-go@v5`, disable cache for this offline/vendor build.
5. Install Android command-line tools/NDK, set `ANDROID_NDK_HOME` to the exact NDK directory, and verify the expected clang wrapper and `llvm-strip.exe` exist.
6. If an OHOS SDK archive URL is supplied, download and extract it to a short path, verify `native/llvm/bin/clang.exe` and `native/sysroot`, and set `OHOS_SDK_HOME`.
7. Run `tool/build_ohos_go_toolchain.ps1` with the official `go.exe` to produce the pinned OHOS Go executable.
8. Run `tool/build_go_runtime.ps1` with explicit `-GoExecutable`, `-OhosGoExecutable`, `-AndroidNdk`, and `-OhosSdk` arguments.
9. Run `go test -mod=vendor ./...` and `go vet -mod=vendor ./...` in `native/go_runtime` before or after packaging. Keep runtime build output and test output separate in the artifact.
10. Copy only the five `.so` files, Windows DLL, and provenance JSON into a clean `artifacts/native-runtime` staging directory. Upload with `actions/upload-artifact@v4` using unique names and `if-no-files-found: error`.
11. Add a workflow summary showing exact paths, artifact names, and the run URL. This directly answers where users download the result.

## External references

- GitHub Actions artifact storage: https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts
- `actions/upload-artifact@v4` README: https://github.com/actions/upload-artifact
  - v4 artifacts are immutable; artifact names must be unique.
  - Hidden files are excluded by default from v4.4+.
  - `if-no-files-found`, `compression-level`, `retention-days`, and `artifact-url` are supported inputs/outputs.
  - Artifacts appear in the run summary and download as ZIP archives.
- `actions/download-artifact@v4` README: https://github.com/actions/download-artifact
- `actions/setup-go@v5` README: https://github.com/actions/setup-go
- `android-actions/setup-android@v4` README: https://github.com/android-actions/setup-android
- OHOS Go port used by this repository: https://github.com/sysit/ohos-go

## Related specs

- `.trellis/spec/backend/native-go-runtime.md`
- `.trellis/spec/backend/quality-guidelines.md`
- `native/go_runtime/README.md`

## Caveats / Not Found

- GitHub's hosted Windows runner does not provide a standard public OpenHarmony SDK path. The workflow cannot build OpenHarmony from a clean runner until the SDK is supplied by URL, secret-backed asset, or a self-hosted runner image.
- The research did not identify a stable official OpenHarmony SDK archive URL suitable for hard-coding into a public workflow. Avoid scraping DevEco Studio or committing proprietary SDK archives.
- iOS/macOS remain outside this Windows workflow because they require macOS/Xcode; their existing shell scripts need a separate macOS job.
- Building the pinned OHOS Go toolchain on every run increases duration and disk use. A future optimization is a versioned prebuilt toolchain artifact/cache keyed by the pinned commit, but the first workflow should keep source provenance explicit.
