# Native terminal observer source review — 2026-10-26

Status: **SOURCE PASS for reviewed logic; PREPARED / UNRUN / NOT READY.**

Scope: static review of `fixtures/native_terminal_observer.mjs` and its author handoff. No module import, validation launch, channel publication, or Git mutation occurred. This reviewer owns no live validation process or retained process handle. This report does not establish the terminal state or release of consumed grant655.

## Findings (fixed)

- File: `fixtures/native_terminal_observer.mjs`, validation log creation in `ackThenLaunch()`.
- Issue: if stdout log creation succeeded and stderr log creation failed, the persistent controller leaked the stdout file descriptor.
- Fix: guard both opens, close the opened stdout descriptor on failure, record any close failure, and defer without launching validation.

- File: `fixtures/native_terminal_observer.mjs`, fixed adapter identity and existing `requireInputs()` callsites.
- Issue: the 374-file source digest excludes `.cmd`, so it did not bind the repaired Windows compiler adapter.
- Fix: pin `native/go_runtime/windows-cc.cmd` and its expected SHA-256. Both existing preflight calls check it: before ACK and after ACK before launch. The controller report records its path, expected hash, and each observed hash with a timestamp.

## Findings (not fixed)

- Controller boundary approval remains pending in the supplied coordination evidence (proposal global666; no approval visible through692). A source review cannot approve that boundary or authorize execution.
- Runtime behavior remains unverified: persistent callbacks, Windows spawn and stdio behavior, CLI parsing, publication retry behavior, cleanup evidence, and total timing require a separately authorized run.
- The self-hash checks disk bytes. A persistent caller could retain an older imported module after a disk edit. The reviewed module has not been imported. A future caller should use a first frozen import or an explicitly fresh module URL. This is a caller/interface decision outside this local fix.
- The repaired adapter is now separately pinned. This narrow binding does not establish complete SDK/sysroot provenance or runtime success.
- The author handoff contains the pre-fix observer hash. Future invocation must supersede that hash with the reviewed hash below. The handoff is outside this reviewer's edit scope.
- Node's outer ChildProcess does not expose a numeric Win32 HANDLE. The module discloses that limitation. Exact child identities and Job drain evidence depend on the pinned child reports; none was produced by this static review.

## Verification

- Lint: PASS for scoped static hygiene (UTF-8 without BOM, LF, final newline, no trailing whitespace). Full project lint was not run under the static-only scope.
- Syntax: PASS, `node --check` exit0. The module was not imported or executed.
- TypeCheck: N/A for this plain JavaScript fixture; no separate type-check was run.
- Tests: UNRUN by instruction. No SDK, controls, compiler/native tests, WSL, or device execution.
- Static inspection: four standard imports; two spawn sites; no kill/terminate, shell:true, execSync, or spawnSync.
- Original validation and publisher objects remain retained. Finalization follows the original validation close callback. RELEASE requires terminal/drain evidence and may follow failing tests. Publications remain serialized; publication retries do not relaunch validation.

## Reviewed identities

- Observer SHA-256: `3465b83e7ebc09d3e0f696f6f16560d78970faac6dc2a27cfcb99048e19914ef`.
- Observer size: 24,506 bytes, 428 lines.
- Superseded observer SHA-256: `eb1eb84f40e96316b3e3ed36ab727dbe27a5f248f16116b8bbb6cd341af12c0b`.
- Frozen wrapper SHA-256 unchanged: `295b23b5dfc1f94b758ad6a34ba372cbbd0b6ae14b84a3d3b8c85c4280833441`.
- Frozen runner SHA-256 unchanged: `9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8`.
- Independently recomputed native inventory: 374 files; SHA-256 `574b1478dd41ce41e23a632fb2624ec6168c209d6c38420b0e027b6ef2859298`.
- Pinned Python SHA-256: `d87063e5597f257004c731b66c59c56c91038861c6877b1a3dca6b8c4e919125`.
- Statically verified repaired adapter SHA-256: `5c486c5420c7d74178250e03fa52061c7df638418560744d587bbba7e36c4f8b`. Adapter runtime validation remains unrun.

Only the observer module and this review report were changed by this reviewer. No specification or public-interface change was made. No fresh grant was accepted or executed.
