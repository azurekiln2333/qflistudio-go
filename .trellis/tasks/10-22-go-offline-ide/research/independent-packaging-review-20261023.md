# Independent packaging and SDK process review

Date: 2026-10-23, Asia/Shanghai. Reviewer: `go_independent_check`.

This is a bounded static review requested by the Go coordinator. No native,
Dart, shared-core, signing, profile or package file was edited by the reviewer.
Heavy verification remains serialized by the coordinator. The coordinator has
accepted the tooling findings below and is implementing repairs; this report
records the pre-repair evidence and does not claim those repairs have passed.

## Findings (fixed)

None. The coordinator owns the relevant tooling edits.

## Findings (not fixed)

### P1: HAP inspection rejects the SDK's real native-library transform

- File: `tool/inspect_go_catalog_hap.py:60-63` (pre-repair implementation).
- Issue: inspection requires the packaged Go SO to equal the staged SO exactly.
  `tool/build_go_runtime.ps1` already applies `--strip-unneeded`, but this does
  not make that equality valid for the installed Hvigor packaging pipeline.
- Primary implementation inspected:
  `D:/ProgramFiles/Huawei/DevEco Studio/tools/hvigor/hvigor-ohos-plugin/src/utils/so-strip-util.js`
  defines `needStrip(undefined)` as true, and
  `src/tasks/worker/native-strip.js` constructs
  `llvm-strip --keep-section=.permission <input> -o<output>`.
  The Go entry profile has no `nativeLib.debugSymbol` override. The worker
  copies the original only when stripping is disabled/excluded, the input is
  a symlink, or stripping fails; it otherwise packages the transformed result.
- Lightweight reproduction: applied the exact SDK command to separate temporary
  copies of both currently staged Go libraries. Both staged files remained
  byte-identical before/after the reproduction. No rebuild or HAP build ran.

| ABI | Staged bytes / SHA256 | Transformed bytes / SHA256 |
| --- | --- | --- |
| x86_64 | 23057648 / `d29165b6d91fd22ff8c41a8b98344bb324585c9889f08206fece98d53f69003a` | 23057464 / `3ccd51e622ac3d8231e3c368ed2036fa058d1e06874daa3640159b54a918577b` |
| arm64-v8a | 21433104 / `c360012403c6b785a898495dc18f33cb5e581629dca6ce2d5478c95b1ddaaee9` | 21432920 / `9b38a1481edb1762704e086e38c28599a620f33c12029aae0dc95b65b0ce1173` |

- Tool:
  `D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/native/llvm/bin/llvm-strip.exe`,
  SHA256 `7092b2a07041635687d30d54f1e60b9cc440bc914d50cf0e2f3a21c348c97967`.
- Recommendation: bind the staged input to its source/build evidence, then
  accept either exact identity or exact bytes produced by this explicitly
  selected, recorded SDK transform on a temporary copy. Record staged,
  transformed and packaged hashes, command arguments, tool identity and exit
  status. Do not replace exact binding with matching symbols, version strings
  or a similarity check. Verify exports and ELF identity on the packaged bytes.
- Not fixed here because the coordinator is editing this tool concurrently.

### P2: Temporary entry-profile mutation is not fully protected

- File: `tool/build_go_catalog_audit.ps1:16-17,32-37,60-68`
  (pre-repair implementation).
- Issue: initial temporary write, hash capture and location setup precede the
  `try/finally`. A failure after mutation but before entering `try` leaves the
  ABI-specific profile installed. The fixed backup filename is also overwritten
  by another invocation.
- Concurrency: the original byte read and hash read are separate operations;
  the initial read-to-write and restore hash-check-to-write windows can overwrite
  a concurrent edit. Two audit invocations also share the profile and fixed
  Flutter/Hvigor build outputs, so the final hash guard alone is insufficient.
- Recommendation: enter the recovery scope before the first mutation; derive
  the original hash from the captured bytes; use unique durable recovery files;
  serialize this tool's full profile/build/preserve/restore operation. An
  advisory claim only protects cooperating invocations. If retaining the
  stronger promise to preserve arbitrary concurrent editors, use actual file
  sharing/exclusive access that still permits the builder's reads. Preserve a
  changed profile rather than restoring blindly.
- Not fixed here because these lifecycle/tooling repairs belong to the
  coordinator, who has accepted the finding.

### P2: Archive evidence does not yet bind the original inventory or native source

- File: `tool/inspect_go_catalog_hap.py:38-50,60-63,89-96` and
  `tool/build_go_catalog_audit.ps1:48-58` (pre-repair implementations).
- Issue: a nonempty unique case list with internally matching current catalog
  hashes can pass without establishing the original 120 topics / 364 imported
  operations. Matching the current staged SO also does not establish that it
  was built from the current native source; the diagnostic's phrase "freshly
  built" exceeds the available evidence.
- Actual content check: current and captured baseline case ID sets are exactly
  equal, with 120 topics and 364 cases: 240 displayed imports, 120 canonical
  samples and four canonical support tests. This is an evidence-gate gap, not
  a finding of currently missing content.
- The device harness independently validates current displayed bytes, imported
  files, outputs, canonical/support coverage and result uniqueness. It hashes
  the Go SO actually found in `/proc/self/maps`, which is useful runtime
  identity. It derives coverage from current catalogs and copies
  `inventorySha256`; it does not independently establish the historical ID set
  or native source-to-library build provenance.
- Recommendation: recompute/compare the complete expected manifest using the
  existing manifest builder and enforce the declared original inventory gate.
  Bind the library to a per-ABI build manifest containing source digest, build
  script/toolchain identity and output digest; capture source before/after
  compilation and reject drift. Keep packaged runtime identity, signature
  verification and actual device execution as separate evidence.
- Not fixed here because the coordinator is implementing the manifest/gate
  changes. Expansion must deliberately update the expected gate after the
  complete expanded corpus is available.

## SDK process changes re-reviewed

The current `lib/go_runner.dart` consumes `ProcessSupervisor` through
`_GoSdkProcess`. Its constructor synchronously attaches both managed stream
listeners before terminal stdin closure or any later await. Single-subscription
controllers retain output for late consumers, while managed streams continue
to drain. No new local defect was found in this adapter during this review.

`test/go_toolchain_test.dart` adds meaningful actual-SDK regressions:

- Run and terminal `go run` exit before stdout/stderr are subscribed, then both
  complete Unicode lines must remain available.
- Run, terminal `go run` and terminal `go test` create an executable child which
  ignores TERM/INT, inherits pipes and owns a private loopback listener. Two
  concurrent cancels must finish, process status must be nonzero, both pipes
  must close and the listener must be unreachable. Fixture-local shutdown
  provides cleanup for a surviving child whose port was observed.

These are static findings; they do not substitute for running those regressions.
The shared supervisor's macOS fallback still only signals the parent. The
coordinator's `sdk-process-ownership-20261023.md` correctly keeps that platform
acceptance open and defers shared changes to C.

## macOS and offline build observations

No concrete new defect was found in the inspected macOS build flow.
`tool/build_macos_go_runtime.sh` selects the active Xcode architectures/SDK,
builds vendor-mode c-shared libraries for arm64/amd64, combines them with lipo,
sets an `@rpath` install name, copies to the app Frameworks directory and signs
the nested dylib when signing is enabled. The Xcode phase runs after Flutter
embedding and before signing the enclosing app. The Runner runpath includes
Frameworks and build-script sandboxing is disabled in the project configs.
Actual Xcode builds, slices, exported symbols and code-sign verification still
require a Mac and were not run here.

Reviewed native build scripts/CMake use vendor mode, local toolchains and
offline module settings; PowerShell mutations to environment variables are
restored in finally, and shell exports remain in child builds. No new offline
build-environment defect was identified in the reviewed paths.

The HAP inspector correctly labels archive-byte/ELF evidence separately from
signature verification and device execution. A signed filename or audit kernel
marker is not represented as device execution.

## Verification

- Focused `git diff --check`: pass for runner, SDK tests, audit wrapper,
  inspector, macOS script and Xcode project (only line-ending conversion notices).
- Audit wrapper PowerShell parser: zero errors at the reviewed checkpoint.
- Inspector Python AST parse: pass at the reviewed checkpoint.
- Both-ABI exact SDK strip reproduction on temporary copies: pass; both staged
  inputs unchanged, transformed bytes differ as documented above.
- Original/current case ID comparison: pass, 364 / 364 with no missing or added IDs.
- Lint: not run, per coordinator's read-only/resource-queue instruction.
- TypeCheck: not run, per the same instruction.
- Tests: not run, per the same instruction.
- Native rebuild, HAP build, signature verification, device execution and actual
  macOS build: not run. No full-task completion is implied.

## Repair re-review and isolated fixtures

The coordinator requested a follow-up after repairing the three tooling issues.
The observations above remain the historical pre-repair record; the following
results supersede their source-fix status at these checkpoints:

| Reviewed source | SHA256 |
| --- | --- |
| `tool/build_go_catalog_audit.ps1` | `462894fc2f90b81a7df13536d6ee330df8a06b8ad6786225a6bf495e71d9c40f` |
| `tool/build_go_runtime.ps1` | `b2e54fdfc387271b6e7b31b52e8b09fe3e834dcfd1e418ef3f91c992fbd1f1ee` |
| `tool/inspect_go_catalog_hap.py` | `fd8837c04163803d07a26c9404d85d25a636c66597d7ee704813f5a5aa8b655c` |
| `lib/go_runner.dart` | `83f8f60f68d813f45f7556395a48d22723b6729993c4b3bcecb5b044cbd016fe` |
| `test/go_toolchain_test.dart` | `cd1a5a502b507776e3d1c077b425eedd48b8c65e177383a6680393965f932871` |

### Findings (fixed by coordinator, re-reviewed)

- The audit wrapper now opens the profile once with ReadWrite access and
  `FileShare.Read`, retains that handle across mutation/build/restoration,
  hashes captured original bytes, creates unique recovery backups and enters
  finally before any mutation. Its recovery flag precedes the first write.
- The native build script captures the native source digest and build-input
  hashes before compilation, rechecks them around every ABI build and before
  publishing provenance, records all five ABI output hashes/sizes and records
  the selected Go/OHOS Go executable identities. The inspector consumes that
  source/build evidence and checks all five recorded outputs.
- The inspector compares the complete regenerated source inventory, enforces
  the default 120-topic / 364-case gate and binds either exact staged bytes or
  the SDK's exact known strip transformation. During this re-review the
  reviewer identified that transforming the live staged path could race with a
  rebuild after capturing its bytes. The coordinator changed it to strip a
  temporary copy of the captured bytes and added strip-tool before/after hash
  checks. Packaged bytes remain the input to the ELF/export checks.

### Profile reader, writer and recovery fixture

Reusable fixture: `research/fixtures/profile_lock_review.py`.
Durable result: `research/profile-lock-review-20261023.json`.

The actual wrapper was copied into an isolated temporary repository. Its fake
Flutter executable ran only reader/lock checks and returned 7. No actual Flutter,
Go or HAP command ran. While the wrapper held its profile handle:

- The actual Flutter-OHOS Dart executable read the file through
  `File.readAsStringSync`; DevEco's bundled JBR read it through Java
  `Files.readString`; Node read it through `fs.readFileSync`. All three
  successfully observed the temporary x86_64 ABI selection. Compatibility was
  measured, not assumed from the FileShare name.
- A second raw writer and a second complete wrapper invocation were both
  refused. The second fake Flutter executable was never called.
- Two fake build failures restored the exact original BOM/CRLF/Chinese profile
  bytes and produced two distinct recovery backups.
- A temporary-only wrapper copy injected a truncation/exception during the
  initial write. It restored the exact original bytes before any Flutter call.

The fixture's first attempt hit a Python subprocess-output GBK decoding error;
the fixture was corrected to explicitly capture UTF-8, then passed. That was a
fixture defect, not a wrapper failure. These lock results apply to Windows and
the actual reader executables recorded in the JSON. They are not a complete
Hvigor build test.

### Inspector binding and refusal fixture

Reusable fixture: `research/fixtures/inspector_binding_review.py`.
Durable result: `research/inspector-binding-review-20261023.json`.

All 11 checks passed against synthetic ZIP fixtures. The two actual staged Go
libraries and actual SDK `llvm-readelf`/`llvm-strip` were used exclusively on
temporary copies. The Flutter ELF was a synthetic header, other ABI provenance
records were synthetic, and the source-digest provider was frozen for this
isolated comparison test. Accordingly, these results prove inspector logic,
not a real package or a real five-ABI build:

- Both x86_64 and arm64-v8a: staged identity and the exact SDK strip transform
  were accepted; the real Go exports were checked in each accepted library.
- Both ABIs: appending a single extra byte to the transformed packaged runtime
  was refused, despite its valid ELF/export identity.
- Wrong native source digest, missing build ABI, changed build script, missing
  catalog case and unexpected packaged ABI were all refused.
- The complete current manifest regenerated exactly to the 364-case source
  inventory with no inventory issues.

### Findings (not fixed after re-review)

No new local source issue remains in this bounded re-review. The previously
reported shared macOS descendant-cleanup gap is still owned by C. Actual new
five-ABI builds/provenance, full analysis/tests, real HAP inspection/signature,
OHOS execution and macOS/Xcode verification remain unexecuted acceptance gates.

### Verification after repair

- Profile reader/writer/failure-recovery fixture: pass.
- Inspector positive and negative fixture checks: 11/11 pass.
- Current complete manifest regeneration: pass, 364 cases, no issues.
- PowerShell parser: pass, zero errors in both reviewed build scripts.
- Python AST parser: pass for inspector and both fixtures.
- Lint and TypeCheck: not run, per coordinator's no-heavy-check queue.
- Full Dart/native/SDK tests: not run, per the same instruction.
- No real Flutter/Go/native/HAP build, install, signature or device action ran.
