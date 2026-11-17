# Implementation plan

1. Update `prd.md` with the corrected platform scope and acceptance criteria.
2. Add `.github/workflows/native-runtime.yml` with:
   - Independent Windows Android and OpenHarmony jobs.
   - macOS native job for macOS universal dylib.
   - iOS device job and iOS simulator job.
   - manual dispatch inputs for OHOS SDK URL and SHA-256.
   - path filters for native sources, build scripts and workflow files.
3. Add a small repository documentation section describing triggers, artifact names, download location and local cleanup targets.
4. Run YAML parsing or equivalent static validation available in the workspace.
5. Run `bash -n` on Apple build scripts and the workflow's shell fragments where possible.
6. Run native Go tests/vet with vendor mode when the local environment permits. Do not treat a missing cross SDK as a successful build.
7. Review the generated workflow against `.trellis/spec/backend/native-go-runtime.md`, especially vendor mode, offline flags, pinned OHOS toolchain, Apple output slices, and artifact provenance.
8. Run the Chinese controlled-language linter on any Chinese documentation changed in this task.

Risk and rollback points:

- Download the default official OHOS SDK with its published digest. Fail visibly on download or checksum errors.
- Hosted macOS Xcode versions can change. Keep Apple jobs limited to direct script builds and report the Xcode version in the manifest.
- The first workflow run may expose action or SDK installation incompatibilities. Fix the workflow without committing generated SDKs or caches.
- Revert only the workflow and documentation files if the remote run proves a platform path unavailable.

9. Commit this task, push the feature branch to the GitHub remote, inspect actual runs, fix CI failures, and report artifact links.

## Execution evidence

- Workflow and collection implementation: `0cb91fd`.
- GPL v3 README alignment with the main project: `b324c92`.
- Preserve source test failure while allowing compilation: `3fabba8`.
- Explicit macOS/iOS deployment targets and manifest fields: `9f815ba`.
- All four commits were pushed to GitHub branch `feat/go-offline-ide`.
- Latest run: `43942972002`. Android, OHOS and iOS device jobs succeeded.
- All five platform jobs in run `43942972002` have now succeeded. Source tests
  still fail. The previous macOS deployment warning was fixed in `9f815ba`.
- Actionlint, parser checks, Chinese lint and 11 collector tests passed.
- Hosted Go vet passed; existing debugger tests failed. Do not archive this
  task as fully accepted or report source checks as passing.
- Exact job/artifact evidence lives in `research/remote-validation.json`.
- Additional disk accounting lives in `research/local-storage.md`.

## Main branch merge

The user explicitly requested merging the pushed feature branch into main.
After fetching both GitHub branches and checking ancestry, main was fast-forwarded
from `82e17af` to `9b7248a` and pushed with a normal `git push github main`.
Remote verification confirmed the same SHA on main and feat/go-offline-ide.
The old `fix/go-release-integrity` branch remains at `82e17af`; it has zero
commits absent from main and requires no separate merge.
