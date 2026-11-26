---
name: trellis-check
description: "Comprehensive quality verification: spec compliance, lint, type-check, tests, cross-layer data flow, code reuse, and consistency checks. Use when code is written and needs quality verification, before committing changes, or to catch context drift during long sessions."
---

# Code Quality Check

## Project execution override

Read `AGENTS.md` and `.trellis/spec/backend/cloud-only-execution.md` first.
All tests, lint/type-check/analyze (including Chinese documentation lint), builds,
dependency/toolchain setup, code generation and artifact verification/downloads
are GitHub-hosted Actions only, never local. Use `python -B` for permitted task
metadata. Review/fix owned files directly without redispatch. During the
pre-handoff source migration only, report to w5V:p1 and do not mutate index/refs
owned by w5V:p2. After verified Herdr handoff, target Codex assigns its own workers
and Git executor; source pane IDs do not govern target work. Follow AGENTS.md
model recovery/final-fallback policy.

Comprehensive quality verification for recently written code. Combines spec compliance, cross-layer safety, and pre-commit checks.

---

## Step 1: Identify What Changed

```bash
git diff --name-only HEAD
git status
```

## Step 2: Read Task Artifacts and Applicable Specs

Read the current task artifacts in order:

- `prd.md`
- `design.md` if present
- `implement.md` if present

```bash
python -B ./.trellis/scripts/get_context.py --mode packages
```

For each changed package/layer, read the spec index and follow its **Quality Check** section:

```bash
cat .trellis/spec/<package>/<layer>/index.md
```

Read the specific guideline files referenced — the index is a pointer, not the goal.

## Step 3: Review Hosted Project Checks

Review GitHub-hosted lint/type-check/test results for the exact changed source SHA.
Do not execute project checks locally. If no hosted result exists, report pending
verification and the required cloud gate. Fix failures only in owned files and
request/review new hosted evidence; skipped or old results are not a current pass.

## Step 4: Review Against Checklist

### Code Quality

- [ ] Linter passes?
- [ ] Type checker passes (if applicable)?
- [ ] Tests pass?
- [ ] No debug logging left in?
- [ ] No suppressed warnings or type-safety bypasses?

### Test Coverage

- [ ] New function → unit test added?
- [ ] Bug fix → regression test added?
- [ ] Changed behavior → existing tests updated?

### Spec Sync

- [ ] Does `.trellis/spec/` need updates? (new patterns, conventions, lessons learned)

> "If I fixed a bug or discovered something non-obvious, should I document it so future me won't hit the same issue?" → If YES, update the relevant spec doc.

### Scope Discipline

- [ ] Any tidying of code the task did not require?
- [ ] Any abstraction, config or extension point added for a case that does not exist yet?
- [ ] Any speculative fallback for a state that cannot occur?
- [ ] Any file changed that the acceptance criteria do not mention?
- [ ] Any workaround added at the caller instead of a fix where the behavior actually lives?

## Step 5: Cross-Layer Dimensions (if applicable)

Skip this step if your change is confined to a single layer.

### A. Data Flow (changes touch 3+ layers)

- [ ] Read flow traces correctly: Storage → Service → API → UI
- [ ] Write flow traces correctly: UI → API → Service → Storage
- [ ] Types/schemas correctly passed between layers?
- [ ] Errors properly propagated to caller?

### B. Code Reuse (modifying constants, creating utilities)

- [ ] Searched for existing similar code before creating new?
  ```bash
  grep -r "pattern" src/
  ```
- [ ] If the same value repeats, does it represent one stable concept whose callers must change together? Extract only then — two literals that merely happen to match today should stay separate.
- [ ] After batch modification, all occurrences updated?

### C. Import/Dependency (creating new files)

- [ ] Correct import paths (relative vs absolute)?
- [ ] No circular dependencies?

### D. Same-Layer Consistency

- [ ] Other places using the same concept are consistent?

---

## Step 6: Report and Fix

Report every violation you find. Then:

- Mechanical and scoped (lint nit, missing type, wrong import, dead branch, failing assertion) → fix owned files, then request/review exact-SHA hosted checks without local execution.
- Design or judgment (naming a shared concept, moving a module boundary, changing a public interface, reassigning where behavior lives) → record the evidence and your recommendation, and stop. Do not rewrite it silently.

If a fix would touch files outside the current task's scope, say so and stop instead of widening the change.
