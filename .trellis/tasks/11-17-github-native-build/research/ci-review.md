# Native CI review (2026-11-17)

## Fixed

- `.github/workflows/native-runtime.yml`: independent URL/digest fallbacks could
  mix manual inputs, repository variables, and defaults. Select one complete
  pair, prefer manual input, and reject missing values before download.
- `.github/workflows/native-runtime.yml`: `bash -n a.sh b.sh` only parses `a.sh`.
  Validate the two Apple scripts in separate commands.
- `tool/ci/test_collect_native.py`: add focused coverage for Android ARM32
  program-header alignment, missing Apple slices, and an export missing only
  from the second Apple architecture.

## Verification

- actionlint 1.7.12: pass.
- PowerShell parser: build and SDK install scripts pass.
- Apple shell syntax: both scripts pass separately.
- Python compile check: collector and tests pass.
- Collector unit tests: 10 pass.
- SDK override execution: defaults, manual pair, repository pair, incomplete
  manual/repository pairs, and multiline rejection all pass in PowerShell.
- Tiny local SDK fixture: checksum verification, nested Windows native ZIP
  extraction, native SDK discovery, and GITHUB_ENV output pass. No SDK download.
- `git diff --check`: pass (existing CRLF conversion notices only).

## Limits

The hosted Windows/macOS builds and native Go test/vet still require the actual
GitHub run. These static/fixture checks do not establish a successful native
build or device execution. The review changes no native Go runtime source.

## Follow-up: first hosted source failure

Run `43938724578` exposed existing debugger test failures and a nil-pointer panic.
The native source is unchanged by this task. The parent recorded the failure in
`research/first-remote-run.md`.

- Keep source checks failing visibly. Android, OHOS and Apple jobs retain their
  dependency on source checks and use `!cancelled()` to permit compilation.
- Split Go tests, Go vet and collector tests into independent steps; vet and
  collector tests still execute after a failed Go test unless cancelled.
- Record `sourceChecksConclusion` and `sourceChecksRunURL` in every manifest.
  Summaries label artifacts as compilation-only when source checks did not pass.
- Add a staging regression that checks failure provenance, summary warning and
  manifest checksum inclusion.

Verification: actionlint, Python compilation and `git diff --check` pass.
All 11 collector tests pass. The parent independently repeated actionlint and
the 11 tests. Runtime debugger fixes remain outside this CI task.

## Follow-up: Apple deployment targets

The successful macOS build in run `43940029448` emitted linker warnings: Go's
object targets macOS 13.0 while the arm64/x86_64 links target 11.0/10.15. The
build script defaults to 10.15, matching all three existing Xcode configurations.
This is an existing application/toolchain compatibility mismatch, exposed by CI.

Official sources checked on 2026-11-17:

- https://go.dev/doc/go1.27#darwin: Go 1.27 requires macOS 13 or later.
- https://go.dev/doc/go1.27#linker: the default minimum macOS load-command version
  is 13.0.0. Lowering that metadata does not establish older-system support.
- https://go.dev/wiki/MinimumRequirements#ios: iOS 12 or later. The repository's
  iOS script and all three Xcode configurations already target iOS 13.0.

Change boundary: configure CI to use explicit macOS 13.0 and iOS 13.0 targets,
capture those values before compilation, and document the existing macOS app
configuration mismatch. The workflow owns the CI settings; the collector stores
`macosDeploymentTarget` or `iosDeploymentTarget` under manifest `build`.
Application Xcode settings and native runtime sources are outside this fix.

Verification: actionlint, all 11 collector tests, Python compilation and
`git diff --check` pass. Chinese controlled-language lint reports zero findings
for `native/go_runtime/CI.md`. A new hosted run must verify the actual link result.
