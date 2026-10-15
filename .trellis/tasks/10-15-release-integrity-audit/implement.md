# Execution plan

- [x] Verify Herdr w8 Pi identities and cwd; dispatch three disjoint assignments.
- [x] Pi 1: audit standalone/editor terminal flow and Go delegate; fix missing Go
  actions and focused runtime regressions, preserving old entry-selection changes.
- [x] Pi 2: review all 120 tutorials/examples, compile/run and dedup, fix actual
  content defects, emit a Go-only patch and record semantic-review evidence.
- [x] Pi 3: audit offline account/Git/cloud entry points, startup/platform manifests
  and outstanding startup work; add meaningful profile regressions as needed.
- [x] Main: inspect each change set, run targeted validation and commit it promptly
  using explicit paths and Conventional Commit subjects. Do not share Git staging.
- [x] Main: integrate only the validated Go content slice in the shared core;
  preserve other languages and commit the precise shared paths separately.
- [x] Run flutter analyze and flutter test with concurrency 1 and a pinned Go SDK.
- [x] Run shared terminal/editor/offline/content tests from the Go dependency graph.
- [x] Run native go test -mod=vendor ./... and go vet -mod=vendor ./....
- [x] Rebuild modified native runtime libraries for all bundled ABIs if necessary.
- [x] Build Android APK and OHOS HAP; inspect native library packaging and alignment.
- [x] Run device integration tests on explicit adb/hdc targets where possible;
  restore the normal product build after integration-test packages.
- [x] Complete final review, record artifacts/blockers, commit remaining reviewed
  work and close linked Trellis tasks only when their acceptance criteria pass.

Closure evidence: research/release-validation.md records five passing Android
API37/x86_64/16KB emulator cases and normal release restoration. Android arm64
real-device execution, Android production signing and current signed OHOS
install/FFI execution are explicitly unverified or blocked; those release gates
are not checked off as successful by completing this audit under PRD AC5.

Build/device operations are serialized by main because other language workspaces
may use the same toolchains/devices. Logs go under .artifacts/release-integrity;
durable concise evidence goes under this task's research directory.
