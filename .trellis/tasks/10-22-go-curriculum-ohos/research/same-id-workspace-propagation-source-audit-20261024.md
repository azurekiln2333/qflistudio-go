# Research: same-ID saved-workspace propagation

- Query: Do same-ID rename/member/primary changes reach an already mounted Go editor/explorer/retained session, and can stale session writes revert metadata?
- Scope: internal, current shared dirty worktree and Go acceptance source only.
- Date: 2026-10-24 (Asia/Shanghai).

## Provenance correction and current source status

The initial gate trace below was gathered while the shared owner was changing
these files. Its prose and final hash capture were not atomic. Follow-up Go
source inspection found that the table's `8549c7...` page, `6b99ad...` explorer
and `58d919...` retained-host bytes already contain the owner's repairs. Those
hashes must not be used as proof that the historical ID-only gates still exist.

At that repaired snapshot, same-ID page updates refresh metadata without
applying a stale saved session; explorer metadata-only updates retain the tree;
all nonnull saved results notify the retained owner; and `attachWorkspace`
accepts a changed same-ID metadata object. The earlier Go workspace handoff
recorded page `487267...`, explorer `57e662...` and host `af9f514...` as older
source snapshots. These are historical leads, not an atomic before/after patch
or an executed reproduction. `workspace_store.dart` remained byte-identical.

Three additional active real-Go regressions are being added for mounted and
retained metadata refresh with dirty buffers, cursors, expansion and identity
preserved. All remain unexecuted under the released host slot. The concrete
source gaps described below are superseded by the owner's source repair;
runtime acceptance and coherent publication remain open.

## Findings

### Historical same-ID metadata propagation trace

1. `../qfli_studio_core/lib/editor/retained_editor_host.dart:167-197` already replaces the retained session's workspace when `updatedAt` or resolved member paths change on `open`, and notifies the mounted `EditorPage`. This is a useful partial fix; identity still correctly follows workspace ID across effective-primary changes.
2. `../qfli_studio_core/lib/editor/editor_page.dart:334-353` calls `_applyWorkspace` only when the ID changes. A same-ID update only assigns `_workspaceMembers` if paths differ. `_workspace` therefore keeps the prior metadata object/name even after the controller supplies the newer document. `_sameWorkspaceMembers` at 357-362 compares only ordered paths.
3. `../qfli_studio_core/lib/editor/file_explorer.dart:206-215` returns immediately when ID, member paths and primary path are unchanged. A rename-only updated widget does not replace `_savedWorkspace`. Member/primary changes do reach its branch at 225-229, but the page above may still supply the old metadata object.
4. The explorer's own settings action emits the updated document at `file_explorer.dart:362-385,526-535`. `EditorPage._onWorkspaceChanged` correctly updates its local metadata at `editor_page.dart:642-650`, but calls the retained owner only if the ID differs (651-653). A same-ID rename/member edit therefore does not synchronize the retained session metadata/label.
5. Even if that callback were invoked for every edit, `RetainedEditorController.attachWorkspace` currently returns for same ID plus same member paths at `retained_editor_host.dart:219-221`. Rename-only updates are discarded there. `_SessionEditor` passes the retained document into `EditorPage` at 667-681, so both caller and callee gates need coherent handling.

### Concrete public trigger

Create W(A,B), open it through `RetainedEditorController.open`, minimize, and update W through `WorkspaceStore.save(existing: W, name: 'Renamed', members: [A,B], primary: A)`. Reopen the returned same-ID document via `controller.open` with unchanged paths. The controller takes the newer document because `updatedAt` differs, but the already mounted page's `didUpdateWidget` leaves `_workspace` unchanged; its workspace title/settings object remain old. Rename through the mounted explorer provides a second trigger: the local page title changes, but the retained controller's `sessionInfos`/restore label do not receive that same-ID update. These are source-derived traces, not executed reproductions.

For member/primary updates, the retained controller can update its effective project and member list, and the explorer handles changed member/primary paths. The missing metadata-object refresh remains relevant: after a same-ID reopen the editor can show the old name while using current roots. A stale name shown by a later management dialog could then be explicitly resubmitted; that is distinct from session-save rollback.

### Store transaction merge is already protected

`../qfli_studio_core/lib/workspace/workspace_store.dart:217-243` snapshots the incoming session, enters serialized/root-coordinated work, reads the current disk document, and writes `current.copyWith(session: snapshot)`. The stale `SavedWorkspace` argument supplies the ID only. A queued stale session write consequently does not restore stale name/membership/updatedAt metadata, and a deleted record is not resurrected (225-231). `save` at 174-203 reads current state in the same transaction and preserves the latest session when no explicit session is supplied (195-198).

Existing `workspace_store_test.dart` directly covers old-dialog/latest-session preservation (172 onward), both membership/session ordering variants (192 onward), another-store metadata preservation (224 onward), and deleted-record stale-writer rejection (244 onward). Those are source coverage leads; no tests were run here. Session snapshots still follow invocation order as their owned field; this audit did not prove a separate queued-session corruption bug.

## Acceptance coverage and smallest shared-owner follow-up

`test/go_saved_workspaces_test.dart:155-202` tests rename/removal by mounting the explorer fixture; it asserts the explorer callback and disk name, not retained-owner labels or a same-ID mounted-page update. Its disk/card/reconstruction case at 204 onward mounts a fresh page. Neither establishes the trigger above. Current `main_workspace_sessions_test.dart` covers promotion/session identity and missing-primary reopening, but contains no rename-only/same-ID metadata regression.

A focused C/main fix should refresh the metadata reference on same-ID widget updates without reloading tab/dirty-buffer/expansion snapshots. Notify/update the retained owner for actual same-ID metadata/member edits; ensure `attachWorkspace` does not ignore changed metadata merely because paths match. Keep existing path/primary reconciliation and workspace ID identity intact. Avoid using `_applyWorkspace` wholesale for metadata-only changes, because it replaces live expansion from a possibly old session snapshot.

One public regression can open retained W(A,B) under the real offline Go profile with dirty source and nontrivial tree expansion, save a rename through its actual explorer dialog, and assert page title, controller `sessionInfos` and restore label agree. Then minimize, externally update the same ID and reopen through `controller.open`; assert the same `EditorPage`/controller survive with new metadata and current roots while dirty buffers/cursors/expansion remain. Finally queue `saveSession` with the old W argument and assert disk name/membership stay current. This combines the missing propagation path with the already intended transaction invariant without a main-profile bypass.

## Files found and related specs

- `editor_page.dart`: owns live metadata, editor-session writes and explorer callbacks.
- `file_explorer.dart`: owns the settings dialog and mounted root view.
- `retained_editor_host.dart`: preserves editor identity and publishes retained labels.
- `workspace_store.dart`: serializes metadata/session transactions against current disk state.
- `test/go_saved_workspaces_test.dart`: real-Go product acceptance source; retained same-ID metadata trigger absent.
- Shared `.trellis/spec/frontend/saved-workspaces.md`: requires retained ID identity, preservation of live buffers and transactional field ownership. Its scope text is still main-only despite the new standalone capability; update belongs to C/main.
- Shared `.trellis/spec/frontend/offline-workspace.md`: requires live owner/cursor/expansion preservation and queued field merges.
- Local `.trellis/workflow.md`: research-only output and shared-owner boundaries preserved.

## Later captured source snapshot (already repaired)

| File | SHA256 |
| --- | --- |
| `../qfli_studio_core/lib/editor/editor_page.dart` | `8549c7e4d00692c27876636d436811100a231d04cb842f263d50eaaab7c07ca4` |
| `../qfli_studio_core/lib/editor/file_explorer.dart` | `6b99ad68a789e2a20d4f49f54ccbf9fa193e9eca852e34a8976bf0b13353a661` |
| `../qfli_studio_core/lib/editor/retained_editor_host.dart` | `58d91921b177173842222f1d2aecb1261f73633abe3a8fefeb4ae33f27e8ba78` |
| `../qfli_studio_core/lib/workspace/workspace_store.dart` | `1c1cd747f3b3c66b92399aa92a6f61703774a6e1754423ca61acf222a9fecf8d` |
| `../qfli_studio_core/test/main_workspace_sessions_test.dart` | `cb20407508cf7b15c8286fa1ddf5a5bd3e3db751ff07401cae38219dd6b5b606` |
| `test/go_saved_workspaces_test.dart` | `1199ee3628f42bd14131aff4e9d8ae99066efbcdab3478f523cbc4ded581dc1b` |

## External references

None required: the finding concerns current internal source contracts. No web documentation or external API/version assumption was used.

## Caveats / Not Found

This is a bounded source audit, not compilation, analysis, widget execution or OHOS proof. Shared source is concurrently owned by C/main; line numbers and hashes identify the inspected bytes rather than a publication freeze. No implementation/test/spec/shared file was changed. No Go/gofmt/Dart/Flutter/SDK/test/analyze/build/WSL/hdc/device command or process cleanup was started. Go236 remains released; this work holds no host reservation. Runtime validation and any shared fix belong to the coordinator/owning agents.
