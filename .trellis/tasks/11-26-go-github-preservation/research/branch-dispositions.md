# Audited Branch Dispositions

Date: 2026-11-27.
Task: 11-26-go-github-preservation.
Source repository: D:/MyNewProjects/qfli_go.

This file records read-only migration evidence and branch dispositions. It does
not authorize Git mutations or establish final publication acceptance. Only
w5V:p2 may execute Git writes under sequenced instructions from w5V:p1 during
the pre-handoff source migration.

## Commit identities

| Key | Full commit ID | Role |
| --- | --- | --- |
| A | 82e17af4233e3aa2c6dd8eac2cb3f808f0f20a4f | Historical mirror main and integrity-fix tip |
| B | e5eb5d631639a65c31da0e8fad964ec631de7771 | Historical offline-IDE tip |
| M | c5cab3d2541b77f3a584dc024d1245a1576c5e68 | Local and GitHub main baseline |
| H | f279134c0525ca704f5ae8ea122ce27e76a2e24b | GitHub application-package publication baseline |
| P | cc1dd4e5f1a61ab46432dd1ebad67d08494e189c | Reviewed local preservation source |

A is an ancestor of B. Both are already included in M, H and P. The original
audit established a linear history from A through B and M to H. The reviewed
preservation checkpoints extend H to P. No historical mirror branch requires a
merge or cherry-pick.

## Every audited local branch

| Local branch | Tip | Disposition |
| --- | --- | --- |
| main | M (c5cab3d) | Fast-forward target. Advance only to the reviewed source after the final gate and explicit p1 instruction to p2. |
| ci/app-packages | P (cc1dd4e5) | Reviewed source for fast-forwarding local main. Preserve its reviewed checkpoints. Do not create a merge commit. |

## Every audited remote branch

The five remote names are github, cnb, gitcode, gitlab and origin. The origin
remote is the historical Gitee mirror, not the GitHub publication destination.

| Remote branch | Tip | Disposition |
| --- | --- | --- |
| github/main | M (c5cab3d) | Publication baseline. Recheck before any authorized fast-forward publication. |
| github/ci/app-packages | H (f279134) | Publication baseline. Local preservation checkpoints above H await publication under separate p1 instructions. |
| cnb/main | A (82e17af) | Ancestor already included. Do not merge or push this branch. |
| cnb/fix/go-release-integrity | A (82e17af) | Ancestor already included. Do not merge or push this branch. |
| cnb/feat/go-offline-ide | B (e5eb5d6) | Ancestor already included. Do not merge or push this branch. |
| gitcode/main | A (82e17af) | Ancestor already included. Do not merge or push this branch. |
| gitcode/fix/go-release-integrity | A (82e17af) | Ancestor already included. Do not merge or push this branch. |
| gitcode/feat/go-offline-ide | B (e5eb5d6) | Ancestor already included. Do not merge or push this branch. |
| gitlab/main | A (82e17af) | Ancestor already included. Do not merge or push this branch. |
| gitlab/fix/go-release-integrity | A (82e17af) | Ancestor already included. Do not merge or push this branch. |
| gitlab/feat/go-offline-ide | B (e5eb5d6) | Ancestor already included. Do not merge or push this branch. |
| origin/main | A (82e17af) | Ancestor already included. Do not merge or push this branch. |
| origin/fix/go-release-integrity | A (82e17af) | Ancestor already included. Do not merge or push this branch. |
| origin/feat/go-offline-ide | B (e5eb5d6) | Ancestor already included. Do not merge or push this branch. |

Remote default HEAD evidence: github/HEAD points to main at M. cnb/HEAD,
gitcode/HEAD and gitlab/HEAD point to main at A. origin/HEAD points to
fix/go-release-integrity at A. These symbolic defaults are not extra branches
or evidence of additional commits to preserve.

## Ref refresh and inventory evidence

The coordinator-supplied five-remote refresh at 2026-11-27 04:43 reported all
five inventories unchanged: github main=M and ci/app-packages=H; cnb, gitcode,
gitlab and origin main=A, fix/go-release-integrity=A and feat/go-offline-ide=B.
This file records that supplied live-remote evidence. Its preparation did not
fetch or query the remote servers again.

Read-only local ref inspection during preparation confirmed the two local tips
and all remote-tracking tips listed above. Remote-tracking refs alone do not
replace a final live-remote recheck.

The original branch audit found no tags, stashes or submodules, including no
gitlinks or root .gitmodules. It found no local-only commits at that original
audit baseline. No extra branch history was left outside the audited source.

The current reviewed preservation source is newer than that baseline. Read-only
inspection now counts three local-only preservation commits above unchanged
GitHub ci/app-packages at H:

1. 810946ed999827b8f483e16595fd7b45da378147: sanitize OHOS signing configuration.
2. b65d38362d4a51297025e6d1a401c7c8c8b51eba: preserve portable project context.
3. cc1dd4e5f1a61ab46432dd1ebad67d08494e189c: preserve the ignored-source archive.

These are accounted-for, reviewed checkpoints awaiting publication, not
unreviewed historical branch divergence. Therefore the original no-local-only
finding must not be presented as a current zero before publication. This new
research file is not included in P and needs explicit review if it is committed.

## Required final gate and prohibited operations

- Recheck local refs, all five live remote inventories, ancestry and local-only
  commit accounting immediately before the gate. The 04:43 refresh is not a
  substitute for that final recheck.
- Reconcile any changed tip with p1 before Git execution. Preserve concurrent
  work and use the final reviewed source commit if it advances beyond P.
- p2 alone may fast-forward local main and publish to GitHub after explicit
  sequenced p1 instructions. This report performs neither operation.
- Do not merge or push the historical cnb, gitcode, gitlab or origin branches.
- Do not force push, delete branches or tags, rewrite history, prune refs or
  perform cleanup. No such operation is required by these dispositions.
- Record the final local/GitHub commit and tree equality before claiming the
  preservation publication gate is satisfied. That final evidence is pending.

Only this research file was written for this assignment. No builds, tests,
project checks, dependency setup, artifact downloads or Git writes were run.

## Evidence sources

- ../prd.md: preservation requirements, ownership and unfinished acceptance gates.
- ../../11-26-github-workspace-migration/research/audit.md: original branch graph,
  remote inventory, default HEADs and absence of tags, stashes and submodules.
- Coordinator assignment: reviewed P source and unchanged five-remote refresh
  dated 2026-11-27 04:43.
- Read-only local ref and commit-range inspection during this file's preparation.

## Addendum: later local ancestry snapshot

The later local source snapshot is `main` at `e2062c1290e3f32785d0a15217e055ecb0a86b33`. Relative to the locally recorded `github/main` tracking ref at `c5cab3d`, local `main` contains 11 commits. The recorded sequence above that base, newest first, is `e2062c1`, `d361118`, `2f15296`, `18996a2`, `db831ae`, `3783588`, `cc1dd4e`, `b65d383`, `810946e`, `f279134`, and `ca8b5a4`.

Local `ci/app-packages` at `3783588` is integrated into this `main` ancestry. It has no separate push disposition; do not publish it separately. This addendum supplements the historical observations above and does not refresh live remote inventories. The historical mirror branch dispositions remain unchanged; any publication gate still requires its separately specified live checks.
