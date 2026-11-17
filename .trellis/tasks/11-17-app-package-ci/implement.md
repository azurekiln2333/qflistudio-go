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

(filled in after the remote run)
