# OHOS release signing and device boundary

## Current build results

- `flutter build hap --release --pub` compiled and packaged current sources,
  then failed at `:entry:default@SignHap` because the configured local `.p12`
  does not exist. This command is a failed signed build, not a successful release.
- A separate fresh `flutter build hap --release --pub --no-codesign` succeeded
  with temporary **typed** `properties.enableSignTask=false` in
  `ohos/hvigor/hvigor-config.json5`. A `finally` block restored the exact original
  file bytes and verified their SHA256. `--no-codesign` alone does not prevent
  Hvigor's signing task in this SDK; neither does an untyped `-p` equivalent.
- Current unsigned artifact: `build/ohos/hap/entry-default-unsigned.hap`, also
  retained at `.artifacts/release-integrity/packages/qfli-go-1.0.0-ohos-unsigned.hap`.
  Both runtime ABIs are present; all 31 allocated ELF sections per library match
  the rebuilt source libraries after package-tool stripping.

## Existing signing materials (read-only investigation)

The configured Go debug keystore, certificate and profile paths are absent.
The three currently present signing-profile sets authorize JVMX, CloudTerminal
and Forge products, respectively, rather than `com.azurekiln.qfli.goshift`.
They cannot safely be substituted by changing file paths.

The old signed Go HAP from 2026-10-09 embeds a Go-authorized profile valid through
2027-09-30, but its public key differs from all currently available signing-set
keys. An old public profile cannot reconstruct the missing private key. No
matching Go keystore backup was found in the Go workspace, `.ohos` directory or
inspected local DevEco caches. No password/profile payload was printed, and no
credential or bundle identity was changed.

The workstation's pre-existing `ohos/build-profile.json5` edits are preserved and
excluded from this task's commits. A new matching Go signing configuration must
be supplied/generated through the user's authorized DevEco signing account before
a fresh signed installable HAP can be produced. Store signing remains external
to the code/build audit.

## Device attempt and limits

Target: `192.168.68.207:46551`, OpenHarmony 7.0 / API 26 / arm64.

To check whether native interpreter tests could run without a signed Flutter app,
the current Go native suite was successfully cross-compiled with the pinned OHOS
Go toolchain into an arm64 test executable. Transfer via HDC succeeded, but the
target rejected execution with `Permission denied` and remote status 126. The
exact temporary remote test file was removed. No HAP/app was installed, no
production app/data was changed, and no attempt was made to bypass target policy.

Consequently this round **does not claim OHOS Flutter/FFI device test success**.
The old signed HAP, old task's device scores, successful cross-compilation and
current unsigned package verification are not substitutes for that missing gate.

Raw logs are under `.artifacts/release-integrity/`: `ohos-release-build.log`,
`ohos-unsigned-release-build.log`, `ohos-native-test-build.log`,
`ohos-native-device-tests.log`, and `final-package-verify.log`.
