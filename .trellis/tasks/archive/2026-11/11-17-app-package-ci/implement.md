# Implementation plan

1. Add `tool/ci/app_build.py` adapted from `qfli_lua/tools/ci_app_build.py`
   (see `design.md` for commands, checks and manifest keys).
2. Add `tool/ci/test_app_build.py`. Cover: failure annotation escaping and
   redaction, init refusal, SDK tag checkout, SDK version validation, ELF
   machine and alignment rejection, ELF and PE export parsing, mobile package
   ABI and library rejection, asset mismatch, OHOS profile sanitizing and its
   refusals, macOS signing environment, failed-job package invalidation.
3. Add `.github/workflows/app-packages.yml` with the seven-entry matrix.
4. Add `docs/app-packages-ci.md` (controlled Chinese). Update the three README
   files and add one pointer to `native/go_runtime/CI.md`.
5. Validate locally:
   - `python -m unittest discover -s tool/ci -p "test_*.py" -v`
   - `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/app-packages.yml', encoding='utf-8'))"`
   - `python scripts/ste-lint-zh.py docs/app-packages-ci.md README.md native/go_runtime/CI.md`
6. Run `trellis-check` on the full change set.
7. Commit with a conventional message and no assistant attribution. Verify
   `git log -1 --format=%B` before pushing.
8. Create branch `ci/app-packages` from `main`, push it to the `github` remote.
9. Poll the run through the GitHub REST API. Fix failures with follow-up
   commits on the same branch. Record job results here.

Parallel split: the documentation step (4) runs in a sub-agent while the
helper, tests and workflow are written in the main session.

Risks:

- Hosted runner images change (Xcode, MinGW, NDK). Fix forward on the branch.
- The gitcode Flutter-OH remote or the OHOS SDK mirror can be unavailable. The
  job fails visibly; rerun later.
- `nm -gU` may not list exports of a stripped iOS executable. If so, switch the
  check to `dyld_info -exports`.
- The first push also starts `Native runtime` (path `tool/ci/**`). Its source
  tests already failed before this task; do not report them as passing.

## Execution evidence

Local, before the first push: `python -m unittest discover -s tool/ci -p
test_app_build.py` ran 44 tests, all passed.

### Run 44053707458 (`App packages`, commit `ca8b5a4`)

| Job | Result |
| --- | --- |
| linux / x86_64 | success |
| ohos / arm64-v8a | success |
| windows / x86_64 | success |
| macos / arm64 | success |
| ios / arm64 | success |
| macos / x86_64 | failure |
| android / universal | failure |

- macos / x86_64 failed in `setup-flutter`. The Dart SDK download reported
  `curl: (6) Could not resolve host: flutter-ohos.obs.cn-south-1.myhuaweicloud.com`.
  Every job downloads the Dart SDK from this host, and the ios job passed on
  the same runner image. The failure is therefore a DNS failure on one runner,
  not an unreachable mirror. Fix: retry the first Flutter command and precache.
- android / universal failed in `build`. `javac` reported `package
  dev.flutter.plugins.integration_test does not exist` in
  `GeneratedPluginRegistrant.java`. The file is not tracked; `flutter pub get`
  generates it with dev-only plugins. Fix: build the APK without `--no-pub`.
- The same log warns that `integration_test` requires NDK 28.2.13676358 while
  the project sets 27.0.12077973. The warning is not fatal. The project file
  stays unchanged.

### Run 45484027345 (`App packages`, commit `f279134`)

All seven jobs passed. The workflow finished with `conclusion: success`.

| Job | Result | Job id |
| --- | --- | --- |
| App / linux / x86_64 | success | 138764482355 |
| App / ohos / arm64-v8a | success | 138764482681 |
| App / android / universal | success | 138764482749 |
| App / ios / arm64 | success | 138764482821 |
| App / windows / x86_64 | success | 138764482857 |
| App / macos / arm64 | success | 138764482914 |
| App / macos / x86_64 | success | 138764482957 |

Both failures of run 44053707458 are gone:

- `macos / x86_64`: the Dart SDK download now retries. `run_with_retries`
  repeats the Flutter config and precache commands (`tool/ci/app_build.py:126`).
- `android / universal`: the APK build drops `--no-pub`, so Flutter regenerates
  the release plugin registrant (`tool/ci/app_build.py:814`).

Seven artifacts were uploaded. Sizes in bytes:

| Artifact | Size |
| --- | --- |
| `app-android-universal` | 145571224 |
| `app-ohos-arm64-v8a` | 62790840 |
| `app-linux-x86_64` | 43001776 |
| `app-windows-x86_64` | 36461904 |
| `app-macos-x86_64` | 23075224 |
| `app-macos-arm64` | 21111652 |
| `app-ios-arm64` | 19885100 |

Status of the acceptance criteria:

- Not met: the helper unit test ran locally only. This round forbids local test
  runs, so that item stays as a recorded local result, not a fresh one.
- Met through run 45484027345: the YAML parses, seven jobs run, every artifact
  carries its platform name, and the successful artifacts include `packages/`,
  `manifest.json` and `SHA256SUMS`.
- Not verified: package installation and interface tests on real devices.

Evidence: `gh run view 45484027345 -R azurekiln2333/qflistudio-go --json jobs`
and `gh api repos/azurekiln2333/qflistudio-go/actions/runs/45484027345/artifacts`.
