# Execution plan

- [ ] Verify Herdr w8 Pi identities and cwd; dispatch three disjoint assignments.
- [ ] Pi 1: audit standalone/editor terminal flow and Go delegate; fix missing Go
  actions and focused runtime regressions, preserving old entry-selection changes.
- [ ] Pi 2: review all 120 tutorials/examples, compile/run and dedup, fix actual
  content defects, emit a Go-only patch and record semantic-review evidence.
- [ ] Pi 3: audit offline account/Git/cloud entry points, startup/platform manifests
  and outstanding startup work; add meaningful profile regressions as needed.
- [ ] Main: inspect each change set, run targeted validation and commit it promptly
  using explicit paths and Conventional Commit subjects. Do not share Git staging.
- [ ] Main: integrate only the validated Go content slice in the shared core;
  preserve other languages and commit the precise shared paths separately.
- [ ] Run flutter analyze and flutter test with concurrency 1 and a pinned Go SDK.
- [ ] Run shared terminal/editor/offline/content tests from the Go dependency graph.
- [ ] Run native go test -mod=vendor ./... and go vet -mod=vendor ./....
- [ ] Rebuild modified native runtime libraries for all bundled ABIs if necessary.
- [ ] Build Android APK and OHOS HAP; inspect native library packaging and alignment.
- [ ] Run device integration tests on explicit adb/hdc targets where possible;
  restore the normal product build after integration-test packages.
- [ ] Complete final review, record artifacts/blockers, commit remaining reviewed
  work and close linked Trellis tasks only when their acceptance criteria pass.

Build/device operations are serialized by main because other language workspaces
may use the same toolchains/devices. Logs go under .artifacts/release-integrity;
durable concise evidence goes under this task's research directory.
