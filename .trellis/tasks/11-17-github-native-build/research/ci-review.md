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
