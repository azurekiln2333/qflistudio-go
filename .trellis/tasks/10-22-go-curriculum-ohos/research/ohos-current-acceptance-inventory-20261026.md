# OHOS current-acceptance inventory — 2026-10-26

Owner: evidence-audit worker, task `10-22-go-curriculum-ohos`.
Scope: source-only reconciliation of the **actual current** original-120 corpus,
tutorial/example variants, imported sample shapes, OHOS API/UI evidence
references and outstanding execution gates.
Boundary: read-only outside this report. No program, SDK, Go, compiler, native,
test, build, device, WSL, channel or git operation was run. All existing files
and other workers' edits were preserved. Nothing is promoted and no asset or
core file was changed.

This is an evidence audit, not runtime acceptance. It does not claim any pass.

## Source-routing correction (2026-10-26)

A subsequent read-only entry-point trace corrects the initial lineage conclusion.
Current `lib/main.dart` installs `GoContentRepository` through
`goProfile.contentRepositoryFactory`. `lib/go_content_repository.dart` loads
app-owned `assets/curriculum/{tutorials,examples}.json` through `rootBundle`;
`pubspec.yaml` bundles that directory. The core factory is a fallback and is not
used by this current standalone profile. The actual model/adapter/page/import
chain preserves `inputFixtures`. Shared-core/extracted old content drift is
real, but does not make app-owned fixtures invisible in current source.

The missing release proof is a fresh current-source HAP build and archive
inspection of `resources/rawfile/flutter_assets/assets/curriculum/` using
`tool/inspect_go_catalog_hap.py`, followed by actual device acceptance. No
shared-core catalog patch is required merely to expose fixtures in this
standalone source. Shared-core catalog mutation remains C-owned. No build,
archive inspection or runtime pass is implied by this source correction.

## 1. Actual current original-120 scope (exact counts)

Source of truth: `assets/curriculum/audit-manifest.json`
(file SHA-256 `c306b6bd5fa52da3aa45c3b1c4f5fe141366c5516783cd587af37c4edef79ffc`,
`inventorySha256` `687f9d6e02f0d2ccdde9681e8894897261d26bf28cc2696a70b542151f3636fc`,
120 topics / 364 cases, `inventoryIssues: []`).

| Catalog | Count | File SHA-256 |
| --- | --- | --- |
| Tutorials (T001–T120, 1 lesson each) | 120 | `a4f3d2b1a081cb89f4666f97c2f50c6623a305b058f20d6d7b74165a1ab984bc` |
| Examples (T001–T120) | 120 | `f9674e28f6c199b15e8ff2b97a76f7f2b7c1c6f373c71d2eec1e13b5f6707ab1` |

364 cases = 240 displayed imports + 120 canonical samples + 4 canonical support
tests.

| Dimension | Breakdown |
| --- | --- |
| shape | displayed-import 240, canonical-sample 120, canonical-support-test 4 |
| operation | program 306, test 58 |
| entry file (displayed) | `src/main.go` 204, `src/snippet_test.go` 36 |
| verification | stdout-exact 303, stdout-sorted 3, test-pass 48, bench-exists 10 |
| support-test ids | `canonical-tests/T113,T118,T119,T120` |

## 2. Imported sample shapes

Canonical-sample shape (one per topic, matches PRD "87 / 15 / 18"):

| declaredImportKind | Count |
| --- | --- |
| single-file | 87 |
| module-project | 15 |
| test-package | 18 |

Displayed-import shape: single-file 174, module-project 30, test-package 36.
Module and test topics carry `go.mod`, `go.sum` and imported-subpackage trees;
the verifier manifest attaches them as exact `inputFixtures`.

## 3. Tutorial/example variants

Method: compare `tutorials[i].lessons[0].code` with `examples[i].code` per topic.

- 117 pairs share identical code.
- Exactly **3** pairs differ: **T007, T024, T027** (matches PRD "only three
  tutorial/example pairs have differing code").

## 4. Catalog lineages (a real discrepancy)

Two Go catalog lineages exist on disk and are **not** the same content:

| Lineage | Location | Go entries | Identity |
| --- | --- | --- | --- |
| Shared fallback / extracted older package | `ohos/entry/src/main/resources/rawfile/.../qfli_studio_core/assets/content/*.json` and sibling `qfli_studio_core/assets/content/*.json` | 120 | identical to each other, 120/120 |
| Verifier / authoring | `assets/curriculum/*.json` = `tool/go_curriculum/content/go/*.json` | 120 | identical to each other, 120/120 |

Shared fallback/extracted slice vs current app-owned authoring, same120 ids, **0/120 entries identical**:

| Kind | Differing field | Count |
| --- | --- | --- |
| examples | `inputFixtures` (product `null` vs verifier `go.mod`/aux/subpackages) | 120 |
| examples | `code` (import-shape header lines) | 33 |
| examples | `expectedOutput` (product `""` vs verifier `"PASS"`) | 18 |
| tutorials | `lessons[].inputFixtures` (product `null` vs verifier fixtures) | 120 |

The initial conclusion that this prevents the current standalone source from
using the verified import shapes was incorrect. The profile routes to the
app-owned catalog instead. The old archive still needs fresh inspection. 33 code ids: 059,060,062–065,068–070,
077,078,080,081,099–115,118–120. 18 output ids: 077,078,080,081,099–111,114.

## 5. OHOS API/UI evidence references that exist

Runtime export surface (cgo, `ohos/entry/libs/{arm64-v8a,x86_64}/libqfli_go_runtime.h`),
9 symbols: `QfliGoRun`, `QfliGoCancel`, `QfliGoFree`, `QfliGoDebugStart`,
`QfliGoDebugPoll`, `QfliGoDebugCommand`, `QfliGoDebugClose`, `QfliGoAnalyze`,
`QfliGoFormat`. OHOS ships 2 ABIs (arm64-v8a, x86_64); android ships 3.

| Evidence | Date | Result | Binding |
| --- | --- | --- | --- |
| `.artifacts/terminal-flow-pi/ohos-native-test.log` | 2026-10-09 | **PASS** — 3 on-device Go FFI tests (multi-file program, worker panic, cancel) via `integration_test/go_native_test.dart` | runtime of that day |
| `.artifacts/terminal-flow-pi/ohos-normal-install.log` | 2026-10-09 | HAP installed on device | same HAP |
| `.artifacts/terminal-flow-pi/native-package/verify-packages.txt` | 2026-10-09 | **PASS** — 5 ABIs (3 android + 2 ohos) packaging check | pre-current SOs |
| `.artifacts/14u-install/*` | 2026-10-17 | HAP installed on "nova 14 Ultra", `native_startup: true`, arm64-v8a | HAP `dcab86a2…` |
| `.artifacts/native-startup-review/device-startup-*.png` | 2026-10-17 | startup screenshots | startup only |
| `.artifacts/release-integrity/ohos-native-device-tests.log` | 2026-10-15 | **FAIL** — `Permission denied`, `QFLI_GO_NATIVE_EXIT:126` | none |
| `.artifacts/native-startup/verification.md` | 2026-10-01 | `hdc list targets` = `[Empty]`; device transition unverified | none |

Currency check against the current tree:

- Current signed HAP `build/ohos/hap/entry-default-signed.hap` = `dcab86a2d18e8b66ff4af302ace76a4b372528c5a856894ee507fa74da0c48fe`
  (2026-10-17). It matches the 14u-install record, so those two agree — but both
  predate the current catalog (2026-10-23).
- Packaged OHOS runtime `ohos/entry/libs/arm64-v8a/libqfli_go_runtime.so`
  (2026-10-23) hashes `c360012403c6b785…`, x86_64 `d29165b6d91fd22f…`; both
  **differ** from the 2026-10-09 `verify-packages.txt` records
  (`5d1f178b84a5a5de…`, `a2aeb225461fbf21…`). The runtime changed after the last
  device evidence.
- No OHOS evidence exists for the current runtime binaries or the current
  catalog. The only on-device Go FFI proof is 3 tests on a different runtime.

## 6. Execution-report staleness (decisive)

Current `native_source_hash()` recomputed read-only (Python stdlib hashing of
the 374 hashed native files) =
`574b1478dd41ce41e23a632fb2624ec6168c209d6c38420b0e027b6ef2859298`.

| Report | Backend | total | pass | fail | inv == current | native == current |
| --- | --- | --- | --- | --- | --- | --- |
| `catalog-official-import-baseline.json` | official | 364 | 364 | 0 | no | no |
| `catalog-native-neutral-cwd.json` | native | 364 | 364 | 0 | no | no |
| `catalog-native-import-baseline.json` | native | 364 | 357 | 7 | no | no |
| `catalog-official-exhaustive-baseline.json` | official | 364 | 322 | 42 | no | no |
| `catalog-native-compat-exhaustive.json` | native | 364 | 300 | 64 | no | no |
| `catalog-native-exhaustive-baseline.json` | native | 364 | 270 | 94 | no | no |
| `catalog-official-baseline.json` | official | 360 | 320 | 40 | no | no |
| `catalog-native-baseline.json` | native | 360 | 272 | 88 | no | no |
| `catalog-native-compat-repair.json` | native | 30 | 30 | 0 | no | no |

**0 of 9 reports bind the current inventory; 0 of 9 bind the current native
source.** Every recorded `inventorySha256` (`e23e008b…`, `b56d3360…`,
`57884cab…`, …) differs from the current `687f9d6e…`. Only
`verifier-runtime-handoff.md` names `687f9d6e…`, and it does not carry records.
The two 364/364 passes (official-import-baseline mtime 2026-10-22; native
neutral-cwd 2026-10-23) are structurally the closest to acceptance but are
stale: they bind the pre-cleanup inventory and a pre-fix native source.

## 7. Outstanding execution gates

| Gate | State | Reason |
| --- | --- | --- |
| Fresh official-SDK 364-case run on current catalog | UNRUN | no report binds `687f9d6e` |
| Fresh host-native 364-case run on current native source | UNRUN | no report binds `574b1478` |
| Native host `go test`/`vet` of `native/go_runtime` | NOT PASS | link fail `-lgcc_eh`, vet UNRUN |
| OHOS packaged FFI run of the 364 corpus | UNRUN | device test exited 126 |
| OHOS run on the current runtime SOs | UNRUN | last device proof 2026-10-09 |
| Device execution (`deviceExecution`) | UNRUN | `false` in all reports, by design |
| HAP archive inspection / signature | UNRUN | `archiveInspected`/`signatureVerified` = `false`, by design |
| `native/build/bundled-go-runtime-build.json` (inspector source) | MISSING | only a native build can emit it |
| T106 failing-helper attribution regression | UNRUN | 364 successes do not prove it |
| Draft promotion of T121–T280 | FORBIDDEN now | blocked on the OHOS baseline |

## 8. Concrete missing proof for all-original examples

1. No report binds the current `inventorySha256` `687f9d6e…`; the 364/364
   evidence is against `e23e008b…`/`b56d3360…`.
2. No report binds the current `native_source_hash()` `574b1478…`.
3. The shared fallback/extracted older Go slice differs from current authored
   assets (fixtures120, code33, output18, tutorial fixtures120). Current source
   loads authored assets directly. A fresh HAP archive has not been inspected
   to prove those exact authored bytes are shipped.
4. No on-device execution of the 364-case corpus exists; the one device attempt
   exited 126 (permission denied).
5. The only on-device Go FFI pass is 3 tests on a runtime that no longer matches
   the current SOs.
6. The native host test failed at link before any case ran; vet is UNRUN.

## 9. Discrepancy vs historical 364 operations and expanded 844

- **364** is corroborated exactly: 240 displayed imports + 120 canonical samples
  + 4 support tests. No current report binds it to the current tree (section 6).
- **844** is the arithmetic target if the 160 drafts are promoted with the same
  per-topic shape: 160 × 3 = **480** cases (draft inventories confirm 80 topics =
  240 cases), so 364 + 480 = **844**. No 844-case manifest exists on disk:
  `tool/go_curriculum/topics` is still 120, and draft promotion is FORBIDDEN
  until the OHOS baseline passes. The 844 figure is a projection, not measured
  current content.
- The historical extracted shared-core slice has120 ids. It is not proof of
  which catalog the current source would load. Neither current364-case archive
  binding nor expanded844-case promotion has been established in a fresh HAP.

## 10. Explicit non-claims

- This report grants nothing and accepts nothing.
- It does not claim a host, native, SDK, FFI, ABI, HAP, signature or device pass.
- Historical host/compiler reports are not current OHOS evidence.
- Packaging PASS and startup screenshots are not corpus execution.
- No file outside this report was modified; no other worker's edits were touched.