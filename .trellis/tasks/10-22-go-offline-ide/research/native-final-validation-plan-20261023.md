# Native validation after Go236 release

Date: 2026-10-23, Asia/Shanghai. This is a pending validation plan, not a test
result, host reservation, source freeze or permission to run a command.

Go236 was released at global channel sequence 287. Native handle 85731 exited
1 and its failing log remains authoritative for that attempted source. SDK
handles 21711 and 70405 exited 0; neither validates the later native repairs.
No new Go, Flutter, build or WSL command starts before another explicit grant.

## Source review input

The implementer's handoff is
`debug-epoch-native-method-source-handoff-20261023.md`. Its review snapshot is
`85d2fae6e988fb59cbd9975681791897fe6da4c1da2b9778cd74bd73a5ae1a82`,
computed by Python using `audit_native.native_source_hash()`. The digest includes
native test files. Any review fix, regression addition or gofmt change requires
a fresh digest. The independent epoch review and promoted-method source review
are still running when this plan is written.

Subsequent source review found two additional defects: promoted native method
expressions lose their outer receiver, and opaque native callbacks can reuse a
lexical debugger routine after it has exited. Repairs are active; the digest
above is now historical. The approved opaque-entry contract uses an explicitly
labeled logical `nativeCallback` execution owner with a real live command ID
and an opaque source-stack boundary. Proven direct synchronous caller identity
is preserved. Debug ownership and asynchronous panic recovery are separate.
The independent evidence and required functional regressions are in
`native-epoch-source-review-20261023.md`; none has been executed yet.

The subsequent reviewer handoff is `native-source-check-20261024.md`. It records
the current digest after retained-argument provenance, snapshot exclusion and
sticky native mutable-alias escape repairs. Its new regressions remain unrun;
the historical digest above must not be attributed to those repairs.

## First later named Windows window

Run serially, with process-local offline/memory settings from the existing
handoff: `GOMAXPROCS=2`, `GOFLAGS=-p=1`, `GOMEMLIMIT=512MiB`, `GOGC=20`,
`GOTOOLCHAIN=local`, `GOWORK=off`, `GOENV=off`, `GOPROXY=off`, `GOSUMDB=off`,
`GO_TELEMETRY_CHILD=2`. Use the pinned local Windows SDK under
`native/build/go-sdk-1.27.1/go/bin/` and the existing native compiler wrapper.

1. Format the owned changed Go files and record the exact resulting native
   source digest before execution. Do not format other products or shared core.
2. Run `go -C native/go_runtime test -mod=vendor -count=1 -timeout=90s -v ./...`.
   Capture all output in a fresh log, the exact outer tool/session handle, shell
   PID where available, terminal exit and elapsed time. Preserve any failure.
3. If that passes within the grant, run
   `go -C native/go_runtime vet -mod=vendor ./...` serially. If the boundary is
   reached, release and request another named window for the remaining check.
4. Recompute the source digest and reject attribution if it changed during the
   checks. Publish exact terminal results and release immediately; no build,
   corpus audit, WSL launch or device command is implied by this first window.

Full `./...` avoids the earlier filter's omissions. Relevant coverage must be
visible in the verbose log:

| Contract | Current regression source |
| --- | --- |
| Initial debug barrier, dependency-created callbacks, proven synchronous callback identity, opaque retained callbacks with live labeled owners, entered callback ownership and late callback rejection | `debugger_test.go` |
| Retained direct arguments after registrar exit/while held, concurrent independent owners, source cutoff, sync/external panic, exact trusted sort identity, bare native go, snapshot registration exclusion, compiled-worker drain, actual RPC reply/result escape and preserved pure-scalar locals | `native_callback_provenance_test.go` |
| Ordinary Run/Invoke asynchronous panic containment, body/cleanup/benchmark accounting, entered callbacks, late callbacks and interpreted-worker shutdown | `execution_lifecycle_test.go` |
| Helper caller attribution, method values/expressions/defer, Unicode, T/F/B families and concurrent/per-test identities | `embedded_helper_test.go` |
| Discarded closure collection while a compiled library retains a live source-aware callback | `embedded_helper_lifetime_test.go` |
| General standard-library method values, expressions, interfaces, promoted receivers, automatic addressing, deferred calls and incompatible signature rejection | `native_method_values_test.go` |
| Actual original test topics, benchmark skip semantics, cancellation and typed execution evidence | `embedded_testing_test.go` |
| Official subprocess comparison of relative/absolute/link return behavior without changing host cwd | `project_symlinks_test.go` |
| Entry-directory behavior across execution modes, per-iteration closures and existing runtime/analysis regressions | `entry_environment_test.go`, `loop_variables_test.go`, remaining native test files |

Inspect every reported skip. A Windows symlink privilege skip leaves the real
symlink acceptance open; a successful reference helper alone does not establish
the comparison ran. Subprocess panic cases must complete in the full parent
test, rather than being invoked as a standalone success-looking fixture.

### Prepared bounded runner, 2026-10-24

The source review has completed at native digest
`61c25dceaa6d7dd067410c32a493378bfef82ab9686345902b79ae2d883f68e7`
(374 native inventory files). Root independently recomputed that digest by
reading bytes, without importing or executing a runtime. The new runner is
`fixtures/run_native_window.py`, SHA-256
`9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8`.
Its source handoff is `native-window-runner-source-handoff-20261024.md`.
Root also parsed its Python AST and checked the two literal argument files;
none was imported/invoked and no Win32 containment control has run.

Global request509 asked for one NEW named Windows window with an explicit
successor and an at-most165s plan. C537 actually released that new window to
Go509 after Go534's short C deferral. Go509 was never accepted or executed:
global545 explicitly DEFERRED it to ready Web510, then Note511, after an
interrupted continuation. Do not execute under request509 now; later Go
runtime work requires another explicit named grant. Go236 remains released.
The source-only product UI/check work does not reserve the host lane.

The first15s plan runs only the runner's real-process containment controls:
normal suspended/assigned root exit0/empty Job, then root exit0 with a held
descendant must reject release until exact owned-Job cleanup reaches zero.
The native mode rejects a missing/failed/different-grant controls report and
changed runner/Python identities. The parent must inspect the actual report and
remaining granted time before starting the separate150s native plan. Control
process release does not hand the global grant away between those phases.
The `.example.args` files retain rejected placeholders until a new explicit
grant and successor exist; their36-path formatting list is explicit and must
be rechecked against current ownership.

Each native phase starts suspended inside its own private Job before resume;
the report records exact process/Job HANDLEs, PID, creation FILETIME, command,
raw logs and actual terminal/active count.128s is the cutoff for new work;
140s is a cleanup observation deadline, not proof of exit. An early draft
discarded unconfirmed handles at that boundary; source review fixed it.
`drain_owned_job` now retains the same wrapper and handles, publishes HOLD,
starts no next phase, and continues exact-handle observation until root
termination AND zero active Job processes are authoritative. Parent must poll
the same launching tool/session and publish any overrun promptly. No foreign
PID cleanup, kill/reset, concurrent SDK/Flutter/ABI/corpus/WSL/device command is
part of this window. The runner never publishes to the channel automatically;
parent must inspect the report and publish exact terminal/release evidence.

Runner execution, Win32 controls, all formatting, compilation, native tests
and vet remain UNRUN. The source/AST checks above do not supersede native85731
exit1. Any edit or formatting changes the digest and requires fresh attribution.

## Separate later gates

- Actual Linux race execution needs a separate named WSL/resource grant. Include
  all lifecycle/Helper/debug concurrency cases and real symlink comparisons.
  The verifier's injected race-gate tests do not provide race-detector evidence.
- The final current-source DLL must be rebuilt before actual Dart FFI tests.
  The complete SDK suite and latest shared adapter/UI integration still need
  their own checks; the two focused Windows SDK passes have narrower scope.
- All five Android/OHOS libraries must be rebuilt with the source-bound build
  manifest. Inspect the real HAP's exact SDK-strip transform, exports, assets
  and signature. Synthetic archive fixtures do not establish HAP acceptance.
- Execute the entire original 364-operation corpus and native offline-host
  checks on an explicitly handed-off OHOS target before promoting the 160
  additions. Then verify the complete expanded 844-operation inventory and
  target product interactions. Host-only corpus results do not close this gate.

The full standalone-product objective, source ownership, selective conventional
commit plan and normal push verification remain unchanged.
