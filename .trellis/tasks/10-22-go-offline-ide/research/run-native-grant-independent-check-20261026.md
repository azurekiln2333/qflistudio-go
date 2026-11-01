# run_native_grant.py — independent source review (2026-10-26)

Reviewer: independent check worker (not the author). Source only.

No import, no execution, no control/native/SDK/WSL/device run, no git mutation,
no edit to `run_native_grant.py`, `run_native_window.py`, the `.args` files,
specs or common core. Method: byte hashing, `ast.parse`, text/line inspection.
No runtime grant requested.

## Final status

**PASS — changed-region review, final snapshot `295b23b5…`.** No blocking
findings remain. Static source review only; runtime is **UNRUN**.

## Final identities

| Artifact | Bytes | SHA-256 |
| --- | --- | --- |
| `fixtures/run_native_grant.py` (final) | 45077 | `295b23b5dfc1f94b758ad6a34ba372cbbd0b6ae14b84a3d3b8c85c4280833441` |
| `fixtures/run_native_window.py` (frozen) | 38484 | `9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8` |
| native source (root-confirmed) | 374 files | `61c25dce…f68e7` |
| interpreter (root-confirmed) | — | `d87063e5…` |

The wrapper hash matches root and disk. The frozen runner is byte-identical and
is asserted before `output.mkdir`, so a drifted runner creates no directory and
starts no process.

## Current findings table

| # | Area | State | Evidence (final snapshot) |
| --- | --- | --- | --- |
| A | Durable PASS ordering | Resolved | Message written first, final report last (761); `finalEvidence` no longer claims the report write |
| B | Message after forced FAIL | Resolved | `force_failure` (738-757) rewrites message and report, returns 1 |
| C | Sticky HOLD vs final drain | Resolved | `child_release_is_hold` (250-252); `persistentHold` from final child release; `BLOCKED_HOLD` removed |
| D | Native full verdict | Resolved | `native_verdict` (342-430) checks exit code, mode, grant, owner, release, within150/withinPlan, vet, skips, 3 phases, per-phase and per-process drain, errors, drift, controls binding |
| E | Skip policy | Compliant | Distinct `PASS_REQUIRES_SKIP_REVIEW`, non-PASS, non-zero, no promotion (422) |
| F | Grant clock scope | Resolved | `clockScope` (470-476) and `withinGrantScope` (668-670) scope the clock to run entry → final durable write; outer ACK and publication marked UNMEASURED |
| G | Post-final-save clock | Resolved | Post-write sample at 770, timing persist 782, re-sample 786; overrun calls `force_failure` (776, 792); exit gate requires PASS + message + final report |
| H | Scope / pending parent | Resolved | `parentPublication` (478-483) `UNMEASURED`/`pending: True`; message prints budget scope and "coordinator actual event timestamps are authoritative" (816-819) |
| — | Exact observed PASS | Resolved | `observed != "PASS"` rejected (355-356) |

Schema reuse: every field `native_verdict` reads exists in the frozen runner's
native report with the expected value (`mode`/`grant`/`nextOwner` 547,
`release` 632, `within150Seconds` 636, `withinPlanSeconds` 637, `vet.state` 603,
`skipReview` 630, `testSkips` 629, 3 phases 638, `toolDrift` 621,
`toolIdentitiesAfter` 620, `sourceDrift`/`nativeDigestDrift` 615-616,
`controlsEvidence.sha256`/`grant` 535-537). No false-reject of a genuine
no-skip PASS. `skipReview` is an exact-string match (372), correct against the
frozen runner and brittle only if its wording changes.

## Historical

Earlier snapshots are superseded and kept only as history:

- `62131779…` (41765 bytes, 821 lines) — **blocked** on G (post-final-save
  clock) and H (scope / pending parent), later repaired.
- `758eb403…` — blocked on A/B/C/D/E.
- `4584a631…`, `7f68637f…` — intermediate, superseded.

## Scope and limits

- Static source review only. No import, execution, control/native/SDK/WSL or
  device run was performed by this reviewer.
- Windows API behaviour, process containment and executable correctness remain
  unproven by this review; runtime is **UNRUN**.
- Reserve arithmetic unchanged and verified: total 7.5s, deadline 22.5s,
  remaining 157.5s.
- Non-blocking nit: `parentElapsedSeconds` is the pre-final-write value;
  the post-write value is `parentElapsedAfterWriteSeconds`.