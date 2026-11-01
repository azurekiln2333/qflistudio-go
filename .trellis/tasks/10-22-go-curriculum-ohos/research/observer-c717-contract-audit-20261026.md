# Research: Go observer compliance with C717

- Query: Does the frozen Go terminal observer satisfy every condition of the C global717 control-plane exception?
- Scope: internal source audit only
- Date: 2026-10-26

## Findings

Verdict: NOT READY for a new validation grant on this protocol. C717 accepts a role distinction conditionally. It does not waive exact validation-outer identity/Job or publisher evidence requirements.

The reviewed source is `.trellis/tasks/10-22-go-offline-ide/research/fixtures/native_terminal_observer.mjs`, SHA-256 `3465b83e7ebc09d3e0f696f6f16560d78970faac6dc2a27cfcb99048e19914ef`. Its existing source check/handoff honestly marks runtime behavior UNRUN and explicitly admits the missing numeric outer HANDLE. This review did not execute or import it.

### Contract matrix

| C717 condition | Source evidence | Assessment |
| --- | --- | --- |
| Dedicated observer identifies itself as control plane | observer:241-242 describes live controller and current sender without self-terminal claims | Source satisfied |
| No SDK starts after validation completion | observer:303-345 has one validation spawn; retryFinalPublication:420-427 only republishes | Source satisfied within one run; a fresh run remains an operator-controlled grant action |
| Retain exact validation-outer child identity and Job | observer:329-334 retains original Node ChildProcess/PID and explicitly says numeric HANDLE unavailable; no validation-outer private Job exists | NOT satisfied |
| Validation root is actually terminal | original retained child close callback at observer:338-344 drives finalize; checkDrain:185 requires terminal | Node child-close proof exists, but it does not supply the missing exact Win32 outer identity/Job |
| Every payload Job terminal and active0 | checkDrain:196-219 checks retained Python children and exact reported payload Job handles, PID/FILETIME, cleanup, active0, handlesClosed | Source checks exist for recorded payload Jobs; these must not be substituted for the outer Job |
| Previous/pending publishers terminal before final sender | publisher objects retained at144; queuePublication:173-177 serializes and resolves only after close157-167 | Prior direct publisher closure is serialized, but publisher descendant Job active0 is absent |
| Final publisher separately bounded and recorded | publisher PID/close/event/exit recorded at113-167; final timing recorded264-284 | Recorded, but not separately bounded: no publisher timeout/deadline or Job; finalization clears the only deadline timer251 |
| Next SDK grant waits for final sender terminal/result | finalPublication stores actual publisher close/result271-283; run.done resolves after it289 | Evidence path exists after close, but no enforcement across startGrantedNative calls, processes, or controller restarts |
| No self-terminal claim or automatic successor inference | finalMessage233,241-242 and explicit c-coordinator target | Source satisfied |

### Concrete gaps

1. Outer identity/Job is missing. The actual validation outer is the Python `run_native_grant.py` process spawned by Node at329. Its children have exact handles and the grandchildren have Jobs. Those different process levels cannot prove the outer's exact Job state. PID plus original ChildProcess close is useful evidence but does not meet the exact outer identity/Job condition as written.

2. A publisher can hang indefinitely. `publish` has no deadline timer. `queuePublication` then blocks all later sends. ACK can hang before validation starts. A deadline-HOLD publisher can hang and prevent final publication. A final publisher can hang after `finalize` clears the run timer. None of these paths is a bounded final sender, even though indefinite retention avoids false terminal claims.

3. Publisher tree state is unknown. The observed direct PowerShell ChildProcess launches `trellis.cmd`; there is no private publisher Job or equivalent descendant ledger. Direct-process `close` alone supplies no explicit Job active0 evidence for that tree. Serialization prevents overlap of retained direct ChildProcess objects, but cannot supply absent descendant Job facts.

4. The next-grant barrier is procedural only. `runs` tracks grants in one live module instance, while the persistent exclusive marker prevents reuse of the same grant. Neither checks whether another grant has unresolved validation or publishers. The final publisher-close data can support a coordinator decision, but the launcher itself does not reject a new grant when an earlier run remains unresolved. Do not claim an implemented final-sender barrier.

5. Approval is an operator assertion. `approvedPersistentController` and a syntactically valid `globalN` string do not read or validate event717 content. This is acceptable only with the parent explicitly reconciling the precise reviewed protocol and coordinator decision. It must not turn a conditional role approval into blanket source acceptance.

### Smallest faithful future repair

Use one retained Windows-aware control-plane process to launch the validation outer suspended, capture its actual process HANDLE and creation FILETIME, assign a private outer Job before resume, and retain those original objects through final exit and Job active0. A prepared Python/ctypes observer can reuse the existing runner's Win32 identity conventions. The observer itself remains explicitly control plane. No additional SDK or product work is needed for this source change.

Apply the same exact-process/private-Job ownership to each channel publisher, including ACK, HOLD, final and retry. Give each publisher a concrete observation deadline within the global reserve. Reaching that deadline must record HOLD with original identities and prevent successor readiness. Retain and observe the original process/Job. A timeout must not imply terminal or active0. No kill/reset is authorized by this audit.

Bind final relay to the actual outer terminal plus outer/payload Jobs active0 and all earlier publisher Jobs terminal/active0. Record final sender identity, exit and Job drain after its real completion. Before any later SDK grant, require coordinator-consumable final-sender evidence. A local cross-run unresolved-run guard should reject a second launch while any prior validation/publisher remains unresolved. Controller-restart behavior needs an explicit safe recovery protocol rather than a fresh map implying no live work.

Re-freeze the changed observer and helper source. Request C review against the concrete identity and sender protocol before READY. Actual Windows launch, nested Job compatibility, real CLI sender and idle callback timing remain runtime gates for a new explicit grant. Never import or run the current observer using consumed655.

## Files Found

- `.trellis/tasks/10-22-go-offline-ide/research/fixtures/native_terminal_observer.mjs`: prepared Node control-plane observer.
- `.trellis/tasks/10-22-go-offline-ide/research/native-terminal-observer-source-check-20261026.md`: prior independent static review and explicit runtime caveats.
- `.trellis/tasks/10-22-go-offline-ide/research/native-terminal-observer-source-handoff-20261026.md`: source handoff and proposed operator invocation.
- `.trellis/tasks/10-22-go-offline-ide/research/fixtures/run_native_grant.py`: pinned child orchestrator; parentPid denotes its own PID, not an outer Job identity.
- `.trellis/spec/backend/native-go-runtime.md`: separates native source review from actual runtime and target acceptance.
- `.trellis/workflow.md`: persists research and requires quality evidence before completion.

## External References

None. This audit compares internal source with the C717 text provided by the parent. It makes no external API compatibility claim.

## Caveats / Not Found

No source code changed. No observer imported or executed. No SDK/native/test/compiler/WSL/device/channel/git action occurred. No grant accepted or slot reserved.

The parent requested an output path under sibling task `10-22-go-offline-ide`. This research role permits writes only under its injected active task `10-22-go-curriculum-ohos/research`. The report is therefore persisted here for the parent to reference or copy through an authorized role.