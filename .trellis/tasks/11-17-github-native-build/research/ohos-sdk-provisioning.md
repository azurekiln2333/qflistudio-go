# OpenHarmony provisioning evidence

The official OpenHarmony 5.0.0 release notes list the public Windows/Linux SDK:
https://github.com/openharmony/docs/blob/master/en/release-notes/OpenHarmony-v5.0.0-release.md

- SDK version: 5.0.0.71 (API 12).
- Archive: https://repo.huaweicloud.com/openharmony/os/5.0.0-Release/ohos-sdk-windows_linux-public.tar.gz
- Published checksum: same URL with `.sha256` suffix.
- HEAD returned HTTP 200 and Content-Length 2666450421.
- GET of the checksum returned `f06a2a8ae38a3cf01c583557f5a4bb1e6e3626df975599aa71f4a59e9af70ecc`.
- Requests without a User-Agent intermittently returned 403; curl-style requests succeeded.
- The workflow uses curl with retries and verifies the complete archive hash.
- The public archive contains host/component packages; extract only the Windows
  native ZIP, then verify native/llvm/bin/clang.exe and native/sysroot.
- No large SDK archive was downloaded to the user's workspace during research.

The GitHub API confirms the OHOS Go v1.27.1-ohos annotated tag resolves to
f2cb44316b789bc12d0b5fd562d853f6fec3ab28. Keep that fixed revision.
The official Go download JSON includes Go 1.27.1 for runner host platforms.

Public availability is established; actual compiler/SDK compatibility still
requires the hosted build. It is not a device execution result.
