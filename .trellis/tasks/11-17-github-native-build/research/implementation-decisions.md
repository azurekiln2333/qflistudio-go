# Implementation decisions (2026-11-17)

- The user approved the final plan with `快做`, then repeatedly asked to continue.
- The original request explicitly includes trying the build on GitHub. Commit and
  push this task to the existing feature branch after checks, then inspect the
  actual Actions run. Do not merge to main or publish a Release.
- Use `macos-15`. The official runner-images macOS 14 README states that macOS 14
  became unsupported on November 2, 2026. The earlier planning label was stale.
- Android and OHOS must be separate jobs so an OHOS download failure cannot
  suppress a successful Android artifact. Keep the PowerShell script's default
  five-library build compatible; add explicit per-platform selection.
- The official OHOS SDK is publicly downloadable. The earlier research statement
  that a user-supplied URL is mandatory was incorrect. Use the official 5.0.0
  release archive and published SHA-256 by default, with an override pair.
  URL: https://repo.huaweicloud.com/openharmony/os/5.0.0-Release/ohos-sdk-windows_linux-public.tar.gz
  Published digest: f06a2a8ae38a3cf01c583557f5a4bb1e6e3626df975599aa71f4a59e9af70ecc
  The archive HEAD request reports 2,666,450,421 bytes. Validate again at install.
- The official Go download JSON contains Go 1.27.1. The OHOS Go annotated tag
  resolves to the repository-pinned commit. Keep those existing versions.
- Windows/Linux use the official SDK to execute user programs, but their IDE
  diagnostics/debugger still load the project's own dynamic library. Existing
  desktop builds compile that library. Omitting their CI artifacts is the
  approved task scope, not a claim that those libraries are unnecessary.
- Remote native builds do not automatically remove local caches or make current
  Flutter/CMake/Xcode app builds consume downloaded binaries. Android/OHOS
  outputs can replace the libraries at their existing packaging locations.
  Apple build phases still compile from source unless separately adapted.
- Do not delete local artifacts or SDKs in this task. Distinguish reproducible
  caches from package/evidence archives and active toolchains in the cleanup guide.

These decisions refine provisioning and documentation without expanding the
approved four-platform artifact scope. Source tests can use Linux without
producing a Linux runtime artifact.
