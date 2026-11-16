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
