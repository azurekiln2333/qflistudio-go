# Overnight independent review (w8:p4) — running log

> Reviewer pane `w8:p4`. Responsibilities: independent review of the patch and
> `verify_shared_apply.py`, ongoing content/runtime-classification review of the
> 120 topics, maintenance of `mobile_check/` and the four review docs. Not
> editing p3's files (emit/dry-run/README/spec/check-report ownership, Dart
> content test, topics/samples).
>
> Shared `apply` is NOT executed (external write is a permission boundary). Real
> assets remain 100 Go rows → any 120 claim from live assets is **pending**.

## Session start (handoff from coordinator)

- 120 Go authored slice: assemble 120/120; `evidence/verify-results.json` = 120
  items, 0 failed; `dedup.py` clean. Not re-running (no change).
- `patch.py` R1–R4 shared-safety audit: PASS. Real-dir dry-run: `non-Go
  kept=1520, Go 100 -> 120`, no write.
- Handoff message sent to w8:p3 (owner tonight) establishing boundaries.

## Rehearsal: apply/rollback on a WORKSPACE COPY of the real shared files

`mobile_check/rehearse_real_apply.py` copies the live aggregates into
`.artifacts/go-curriculum/rehearsal/`, runs `emit + apply + rollback` there, and
checks byte invariants. Result:

```
apply rc0
APPLY non-Go raw byte/position invariance: OK   (raw bytes + relative order)
ROLLBACK restores 100 Go: OK
REAL shared untouched: True
REHEARSAL OK
```

Findings:
- Real layout confirmed: Go entries are **contiguous** at indices 700–799 in
  both files (before: rust, after: html). `_go_run_span` handles this.
- Absolute offsets of entries *after* the Go run legitimately shift when the Go
  block grows 100→120; the invariant is **raw bytes + relative order**, which
  holds. (Initial check compared absolute offsets and over-reported; corrected.)
- No non-Go byte change in either file; rollback restored 100 Go.
- Real shared sha256 after rehearsal unchanged: `4822ae…` / `aadb0a…`.

## Content review — recent fix batch (T040/T047/T052/T053/T083)

| Topic | runtime | code==sample | limit statement | verdict |
| --- | --- | --- | --- | --- |
| T040 | desktop | True | yes | native-only, desktop-only OK |
| T047 | desktop | True | yes | native-only, desktop-only OK |
| T052 | desktop | True | yes | native-only, desktop-only OK |
| T053 | desktop | True | yes | native-only, desktop-only OK |
| T083 | desktop | True | n/a (passes native) | deterministic, OK |

No substantive errors found in this batch.

## Open items

- **F-T6 map drift (minor):** T009 omits `fmt.Scan`; T013 omits `fallthrough`
  vs their curriculum-map rows. Internally consistent; sent to w8:p3 to add or
  reconcile the map row.
- Real shared still 100 Go: the 120/120 live-asset claim is **PENDING** the
  authorized apply. `verify_shared_apply.py` is ready and validated on a
  synthetic apply.
- `test/go_curriculum_content_test.dart`: 7 pass / 1 fail — the failing test is
  the post-apply bundle gate (`application asset bundle loads the exact 120/120
  Go slice`), expected red pre-apply.
- Pre-existing `test/content_code_import_test.dart` invalid-filename failure left
  intact (not masked).
- Next content batches: pending p3's signal on which topic IDs change.
