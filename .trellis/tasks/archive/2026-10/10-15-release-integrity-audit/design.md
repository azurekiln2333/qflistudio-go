# Design

The Go app consumes ../qfli_studio_core as a path dependency. StudioProfile is the
shared policy boundary: isOffline/ offlineOnly already gate network features;
terminalCommandDelegate is the language-owned terminal command extension point.
GoProgramRunner and native/go_runtime remain the execution owners. Both terminal
surfaces must consume the same delegate and use the existing shared shell contract.

The curriculum source is tool/go_curriculum/topics and samples, assembled into a
Go-only patch. Main integrates shared assets through patch.py with exclusive file
handles and verifies all non-Go bytes before/after. Do not replace the aggregate
with root-level local JSON without proving which files the loader consumes.

Pi 1 owns Go terminal/runtime code and associated focused tests. Pi 2 owns Go
curriculum sources/tooling and curriculum tests. Pi 3 owns offline-profile/platform
entry audit and a dedicated offline regression test; lib/main.dart shared edits are
serialized through main. Main owns task state, integration, build/device operations,
shared-core mutation and all commits. No Pi may stage or commit another Pi's work.

Record baseline diffs before integrating. Preserve existing startup and generated
native artifacts until reviewed. Rebuild native libraries if runtime source changes.
Rollback uses explicit reviewed paths or Go-only content rollback; never reset the
shared worktree or whole shared aggregate files.
