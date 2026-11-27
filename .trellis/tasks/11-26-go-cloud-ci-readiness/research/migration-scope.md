# Migration scope addendum

Task: `11-26-go-cloud-ci-readiness`  
Source snapshot: `main` at `e2062c1290e3f32785d0a15217e055ecb0a86b33`.

## Scope decision

The approved source migration covers S0-S2. Keep S3 limited to what existing GitHub Actions workflows require to pass. New installer features are follow-ups, not migration blockers. Preserve the S3 installer draft at `D:/MyNewProjects/_migration-backup/qflistudio-go-20261127/s3-installer-followup` as planning material.

S4 release signing is stopped and excluded from this migration. The stopped work has zero files in the migration source. Do not include release-signing workflow or signing-gate implementation in this scope.

Missing new installer platforms and signing remain follow-up items, not blockers. This scope note does not change acceptance criteria or claim completion or hosted validation.

## Core dependency

Keep the released core pin at `1ae4674a4b153701b0c3b3ff04b1a1b77a318611`. The previous migration baseline `476a30acee21dc486ee2849dd8064a7be665e4d5` was covered by core-check run `45656065902`; that historical result does not validate the released pin.

## CI-decoupled triage

Keep work that does not depend on cloud CI moving while runs are pending. Recheck migration-caused failures involving paths, core reference, lockfile, or generated registrants. Treat infrastructure failures using the coordinator's retry procedure. Failures already present at pre-migration GitHub main remain follow-ups, not migration blockers. CI evidence is still required at the final source revision; none is asserted here.

## Evidence boundary

This document records scope and triage decisions only. It does not claim that the source was pushed, that target parity or acknowledgment was completed, or that any current hosted check passed.
