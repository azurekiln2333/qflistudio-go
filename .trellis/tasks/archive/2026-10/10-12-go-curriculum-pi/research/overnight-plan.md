# Overnight plan — w8:p3 (autonomous, 2026-10-12 night)

Owner: w8:p3. Main controller has stopped monitoring; this pane proceeds
autonomously. No polling notifications, no ordinary decisions requested.

Write scope (mine): `tool/go_curriculum/**` except `mobile_check/` (w8:p4);
`test/go_curriculum_content_test.dart`; task `research/**`; related spec docs.
Not allowed: commit/push/publish; edit external shared files; overwrite others'
work; touch runtime/toolchain/terminal/`.so`/`.h`.

## Priorities (in order)

1. **Finish patch/doc wrap-up + Herdr handoff with w8:p4.**
   - patch.py emit/dry-run done; README + spec synced. Reconfirm audit green.
   - Handoff note to w8:p4 (what's mine vs theirs, no overlap).

2. **Per-chapter deep read of 120 tutorials + 120 examples.**
   - Fix real knowledge errors, shallow explanations, code/output/exercise-answer
     mismatches, wrong run commands; improve prerequisite path and beginner→
     advanced串联.
   - Only changed topics get re-verified (no blind 120 full re-run).

3. **Add learning aids inside `tool/go_curriculum/`,** keeping stable 120 IDs:
   - learning roadmap, chapter index, how-to-run (project/test/benchmark),
     common-error diagnostics, desktop/mobile limits.

4. **After content changes:** assemble → dedup → emit; re-verify affected
   samples; run full sweep only when the actual change count warrants it.

5. **Real asset load/import verification — report true state.**
   - Shared `apply` NOT executed; external write needs separate permission.
   - Until authorized: read-only dry-run + in-workspace temporary integration
     proof only. Provide the exact final command. Do NOT falsely claim the 8
     real asset tests pass.

6. **Fix issues my own tests/tools find.** Keep the invalid-filename contract-
   drift record; do not weaken it or mask failures. Don't touch unrelated runtime.

## Coordination with w8:p4 (review/check)

- p4 owns `mobile_check/`, review reports, and the audit tooling. Do not edit.
- Code changes go to p4 for review. Use Herdr channel if available; else leave a
  durable handoff note in `research/`.

## Evidence discipline

- Update `research/progress-b.md` and this plan per phase.
- Final `research/overnight-report.md`: done / verified / not-done + reason /
  one next step for the morning.

## Constraints

- 401/external failure: record and stop retrying.
- If context is tight: save handoff first, then continue via compaction.

## Status: COMPLETE (overnight pass)

All priorities done. Final: 120/120 verify, assemble 120/120, dedup clean,
emit 120/120, dry-run non-Go kept=1520 Go 100→120, audit OK, GUIDE.md added,
Dart content test 7/8 (fail = real-asset load, pending apply), race green.
Shared unchanged; no commit/push; see `research/overnight-report.md`.
