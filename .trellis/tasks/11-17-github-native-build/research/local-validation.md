# Local validation before the first remote run

- actionlint 1.7.12 passed for `.github/workflows/native-runtime.yml`.
- PowerShell parser accepted the mobile build and OHOS installer scripts.
- Git Bash accepted both Apple scripts with `bash -n`.
- Seven initial Python collector regression tests passed.
- Chinese controlled-language lint passed for README, CI guide and task PRD.
- All four GitHub Action SHA pins matched their official release tags via API.
- GitHub Actions is enabled on the repository; current credentials have push access.
- The pre-existing GitHub feature branch is at e5eb5d631639; local work includes
  nine existing commits beyond the original tracking ref. Preserve those commits
  and use a normal fast-forward push, never a force push.
- SDK downloads and cross compilation will be validated in actual hosted jobs.
- No local SDK, native library, package, screenshot or evidence directory was deleted.
