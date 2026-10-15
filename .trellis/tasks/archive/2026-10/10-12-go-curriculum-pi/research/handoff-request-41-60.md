# Handoff request: T041–T060 → w8:p3

Requested by: w8:p3 (this pane), at user direction ("接手 T041–T060").
Status: **WAITING for confirmation** — not writing anything under T041–T060 yet.

## What w8:p3 needs before writing

Either of:
1. Direct confirmation from pi-go-terminal (w8:p2) that it has narrowed to T001–T040
   and released T041–T060, **or**
2. The file `research/handoff-41-60.md` authored by w8:p2.

## Current observed state (read-only check)

- `research/handoff-41-60.md`: **absent**.
- `tool/go_curriculum/topics/`: T001–T020 (w8:p2) + T061–T120 (w8:p3). **T021–T060 absent.**
- `tool/go_curriculum/samples/`: 40 dirs (T001–T020 by w8:p2, T061–T120 by w8:p3);
  T041–T060 have no samples yet.
- `research/progress-a.md` still declares scope **"T001–T060"** and lists only
  "Batch 1 (T001–T020): DONE". So w8:p2 has not yet formally narrowed to T001–T040.

## Why waiting

Writing T041–T060 now risks colliding with w8:p2, which still owns T001–T060 per its
own progress file. To avoid overwriting concurrent edits, w8:p3 holds until the
confirmation/ handoff file appears.

## Planned work once confirmed (no writes yet)

- Author real Go samples + substantive zh-CN lessons for T041–T060:
  - S4 interfaces: T041–T048
  - S5 errors/defer/panic: T049–T058
  - S6 packages/modules: T059–T060
- Per-topic `topics/T041..T060.json` (schema.md shape) + `samples/T041..T060/`.
- Verify each with the pinned SDK; update `progress-b.md`; hand to review Pi (w8:p4).

## Note to w8:p2

If you intend to keep some of T041–T060, please state the exact retained range in the
handoff file so w8:p3 authors only the remainder. Otherwise confirm a clean release of
T041–T060.
