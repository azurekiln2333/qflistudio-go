# Native debugger regression evidence

## Scope and revision identity

This record captures the historical hosted failure and the source-only review of the current local test-fixture changes. It does not claim that the current source passed hosted validation.

- Local branch: `main`
- Local `main` and `HEAD`: `2f152961df114f099969058c9d12013a722df3bd`
- The two native test files listed below are part of local `main`. Their worktree readback hashes and committed LF hashes are recorded separately; no hosted result for this revision is recorded here.

## Source-based fixture review

Source review identifies two distinct fixture/setup issues. The explanations below are source-backed interpretations, not experimentally proven failure mechanisms.

1. `TestDebugOpaqueCallbackCreatedByMainCalledByWorker` placed its worker breakpoint on `done <- pool.Get()`. The source suggests the call could enter the callback before the test observes a worker pause. The revised fixture separates the `pool.Get()` assignment from the send, places the pause before the call, and checks breakpoint positions and worker-frame identity before continuing.
2. `newNativeProvenanceDebugger` used `interp.AllBreakpointTarget()` for a fixture with multiple source nodes. The historical retained-native-argument test panicked during breakpoint traversal at a nil type. Source review suggests that targeting the fixture's exact `main.go` path avoids traversing unrelated nodes. The revised helper validates each returned source position. The main-snapshot case also targets that path and validates its result.

These are source-based fixture diagnoses. The historical run establishes the observed failure, not the proposed causal explanations or that the revised tests pass.

## Current source review

Source-only review: **PASS**, limited to the two native test files. Their reviewed contents are in local `main` commit `2f152961df114f099969058c9d12013a722df3bd`. No tests, builds, or other project checks were run locally. This review does not substitute for hosted validation.

- `native/go_runtime/debugger_test.go` — worktree source readback SHA-256 (CRLF): `3afbbbf61c26175dde266a7dfcca4fb591fb75b1b95fa941322bb4a3cbc16206`; committed LF SHA-256 (from p2 commit report): `a5c1a2381d05024fa9c6760767d943e581d5fda7ff56a7b5dbeb1ea43961df77`
- `native/go_runtime/native_callback_provenance_test.go` — worktree source readback SHA-256 (CRLF): `abb723645a389dc836bcd2f4e3bb17fc0fc12eadd888488a912178d48a5be1a1`; committed LF SHA-256 (from p2 commit report): `e742a070e30dc9d7fe033658f6b23e8ea2e900eb3a09e069ab1a69f2a4c92ed3`

## Historical hosted failure

- Workflow: `Native runtime`, run [45484027361](https://github.com/azurekiln2333/qflistudio-go/actions/runs/45484027361)
- Checkout SHA: `f279134c0525ca704f5ae8ea122ce27e76a2e24b`
- Failing job: `Native source tests`, job `138764481895`
- Outcome: failure. The native Go test step failed. `go vet` and the artifact-validation regression step passed in that historical job; those results apply only to `f279134`.

The Python helper suite in the same job reported 56 tests: **55 passed and 1 skipped**. This is historical evidence only. It does not validate the current source or a newer revision.

## Validation state

All hosted validation for the current local `main` revision remains **pending**. Required native regression tests and any later integration checks must run on GitHub-hosted Actions against an exact reviewed source SHA. Do not reuse the historical failure or helper result as a current pass, and do not claim a current SHA beyond the local `main` value recorded above.
