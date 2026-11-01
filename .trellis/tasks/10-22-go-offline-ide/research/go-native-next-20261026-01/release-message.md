ORCHESTRATION Go-native-20261026-01; requested next owner c-coordinator.
Result FAIL_OR_INCONCLUSIVE; controls PASS=True; native phase FAIL_OR_INCONCLUSIVE.
Parent elapsed 19.914s of 180.0s; withinGrant=True; overrun=0.0s.
Native deadline 22.5s; reserve 7.5s (entry 1.0 + launch 1.5 + evidence 2.0 + release 3.0).
Budget scope: measured from the wrapper run entry to the final durable write; outer ACK-to-terminal and parent publication are UNMEASURED.
Parent publication: UNMEASURED (pending=True); coordinator actual event timestamps are authoritative.
Frozen runner intact=True; runner sha256=9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8.
Owned-go template: 36 explicit paths; tool drift=[].
controls: PID=50128, HANDLE=332 (0x14c), creationFILETIME=134374323147474401, terminal=True, exit=0, elapsed=0.512s, holdObserved=False.
  controls evidence: release=RELEASE, result=PASS, phases=['control-normal', 'control-root-exit-child-live'], sha256=ffd1bb2c88201bdd0c33c6d794677322d1300b553ae3d9e86d179838435bd51f.
native: PID=57528, HANDLE=324 (0x144), creationFILETIME=134374323152619811, terminal=True, exit=1, elapsed=19.391s, holdObserved=False.
  native evidence: release=RELEASE, result=FAIL_OR_INCONCLUSIVE, phases=['gofmt', 'test'], sha256=c9d2d92d9e2114ee70b58e3ab1a1be8a73815596fc488b85cb5bd9cb3292ee8e.
  native problems: observed result is 'FAIL_OR_INCONCLUSIVE', expected exact PASS | the wrapper observed child exit 1, expected 0 | vet state is 'UNRUN', expected PASS | 2 native phases ran, expected 3 | test: not passed | test: exit 1 is not 0
Failure reasons: native phase FAIL_OR_INCONCLUSIVE did not PASS
The final report is written last; its presence with this result is the attestation, and the parent publishes it after the wrapper terminal.
Persistent HOLD observed=False; no kill, no timeout, no restart was used.
Publication NOT_ATTEMPTED; this wrapper neither publishes nor self-issues grants.
Successor grant NOT_GRANTED: No successor grant is issued before the wrapper terminal; the parent publishes after it
The parent must publish this exact report only after the wrapper terminal.
No build, corpus, SDK/Flutter, WSL or device gate is implied or closed by this run.
