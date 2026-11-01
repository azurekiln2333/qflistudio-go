# Execution plan

## Planning and coordination gate

- [x] Read the full attachment, Trellis session/phase indexes and applicable indexes/contracts.
- [x] Inspect live Git/worktree state and identify all sibling product repositories.
- [x] Record full R1–R10 scope and concrete Go/OHOS gaps without shrinking the umbrella.
- [x] Finish baseline inventory and official-source research; initiate owner/API coordination. Python reports C shared-core ownership; obtain the exact owner-published interface before adapter integration.
- [x] Create independently verifiable child tasks and curate real spec/research JSONL entries (nine per manifest).
- [ ] Present the final plan for user review as required by the current runtime workflow; only after the subsequent approval run `task.py start` on the implementation-owning child.

## Phase A — exhaustive current-content validation

1. Freeze catalog/source/backend hashes and initial worktree changes. Inventory all Go tutorial/example variants and supporting project files; obtain the other coordinators' inventories.
2. Run existing official-Go verifier and the real shipped host-native runtime harness over every applicable item. Capture failures with IDs, stderr, assertions and exact backend identity.

   Fresh planning baseline: official verifier completed with exit 0, 120 topics passed/0 failed; log in `research/baseline-official-go.log`. This does not cover actual OHOS execution. The inventory identifies all 240 Go catalog code blocks and topic/source hashes in `research/baseline-inventory.json`.
3. Repair the runtime/content causes of failures with focused native regressions. Keep all original concepts and IDs.
4. Extend OHOS integration harness to execute that same full inventory using the packaged FFI runtime. Reconnect/detect a real target before install/drive. Without one, keep device acceptance open and continue independent host work.
5. Validate C/C++ headers and Python module support through their repository owners' current reports.

## Phase B — shared IDE contracts and Go implementation

1. Agree shared-core owner and optional analysis/debug/workspace interfaces before any shared edit; add a task/spec entry for those contracts.
2. Shared owner implements catalog chips/title badges, missing highlight modes and sidebar restore regression, then persisted multi-root state and correct file ownership.
3. Shared owner implements genuine diagnostics ranges/underlines/Problems and bounded Output panel, then connects runtime adapters. Go owner supplies non-executing Go analysis/formatting hooks with native tests where mobile support requires it.
4. Replace Go's generic tool detour with useful direct offline tools, using the current project and typed result/errors. Other products do equivalent work under their owners.
5. Implement actual debugger and local Ports capabilities where supported. Test pause/step/continue/stop; do not substitute a visual breakpoint toggle for backend behavior.

## Phase C — new curriculum

1. Only after the existing baseline is understood and repaired, author 160 substantive new Go examples with explanatory lessons and expected behavior; independently review the topic map and dedup.
2. Run source/aggregate/import/schema checks, official compiler verification and the actual native interpreter over all existing and new content.
3. Integrator applies the Go slice with backups/digest checks while preserving every non-Go entry.
4. Run the complete OHOS catalog suite and record the exact packaged content/runtime hashes. Newly added content is not accepted based on desktop-only passes.

## Validation commands and evidence

Use the pinned SDK `native/build/go-sdk-1.27.1/go/bin/go.exe`, not an assumed PATH `go`. Keep verification-only `GOMAXPROCS=2`, `GOFLAGS=-p=1`, `GOTOOLCHAIN=local` when required.

- `python tool/go_curriculum/assemble.py`
- `python tool/go_curriculum/verify.py --go native/build/go-sdk-1.27.1/go/bin/go.exe`
- `python tool/go_curriculum/dedup.py`
- `python -m unittest discover -s tool/go_curriculum -p test_verify_race.py`
- Host-native curriculum: inspect and extend `tool/go_curriculum/mobile_check/native_hostcheck_test.go`; use test-only overlay, exact shipped `runGo`, bounded per-item assertions and exhaustive inventory.
- Native module: pinned `go test -mod=vendor -count=1 ./...` and `go vet -mod=vendor ./...` from `native/go_runtime`.
- `flutter analyze --no-pub`
- `flutter test --no-pub --concurrency 1` with `QFLI_GO_TEST_EXECUTABLE` set to the pinned SDK so official toolchain tests run.
- Shared-core `dart analyze lib test` / full `flutter test` and affected standalone product suites after shared APIs/assets change.
- `flutter build hap --release --no-codesign` using existing build/signing conventions; inspect actual HAP runtime/asset hashes.
- `hdc list targets`, then the repository's real OHOS `flutter drive` integration path on a connected target. Never run device commands against a guessed target or claim HAP assembly proves execution.
- Visual/widget checks for phone/desktop, long names, large text, diagnostics ranges, popup lifecycles, minimized editor, multi-root and language filtering.

## Final review and publication

- Independently check task diffs against every R1–R10 row and all product inventories. Missing device evidence remains open.
- Update executable specs with discovered contracts; run the Trellis check and finish skills.
- Stage only audited task files; review staged diff and conventional commit messages. Preserve user signing/icons and unrelated generated files.
- Commit requested work, attempt configured normal pushes, verify remote SHAs or record exact failures.
- Archive completed children only after their requirements pass. Keep this parent and the thread goal active until all products and requirements have authoritative completion evidence.
