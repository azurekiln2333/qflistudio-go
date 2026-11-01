# Verify and expand Go learning content on OHOS

## Goal and scope

Own the Go deliverable for parent R1/R2, without closing the all-product umbrella. Preserve and repair all 120 current topics and the actual 240 tutorial/example code blocks. Then add 160 distinct substantive runnable examples with explanations and expected behavior. Parent source request and constraints remain authoritative.

## Current facts

`../10-22-standalone-ide-completeness/research/baseline-inventory.json` captures current catalog and topic hashes. Baseline contains 87 single-file topics, 15 module projects and 18 test packages; only three tutorial/example pairs have differing code. All 120 authoring records say desktop; current official-Go checks cannot prove their app imports run on OHOS.

## Requirements and acceptance

- Enumerate every visible Go code block and its imported-project shape. Preserve IDs and teaching concepts; make support files/test execution usable in the product rather than silently skipping complex topics.
- Assert official compiler results and actual shipped host-native runtime results independently for tutorials and example variants. Repairs must address concrete failures.
- Verify every existing/new item through the current OHOS packaged FFI runtime, with item IDs, content/runtime hashes, output/exit assertions and no unexplained omissions.
- Add 160 meaningful examples after baseline investigation. No title/constant-only copies; include explanations and expected behavior, deterministic inputs and realistic offline tasks.
- Shared integration preserves all other languages' content and existing user edits. Full Go tests/build/import gates pass.

## Exclusions and dependencies

No network/package-download exercises. Do not relabel failures as desktop-only to satisfy mobile acceptance. Shared catalog application waits for the designated core integrator; no other product's curriculum is owned here. Real OHOS execution waits for an actual connected target while host work proceeds. Go diagnostics/debugger are owned by sibling `10-22-go-offline-ide`; where lesson execution needs additional real mobile functionality, coordinate that dependency explicitly.
