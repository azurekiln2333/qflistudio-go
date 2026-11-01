# Native source review handoff — 2026-10-24

Reviewer: `/root/go_native_check_1024`, dispatched `trellis-check` for
`10-22-go-curriculum-ohos`; source ownership handed back to `/root` after this
report. This is source review and regression authorship, not executable proof.
Shared core, sibling products and Dart files were not edited by this reviewer.

## Source identity and resource state

Current `audit_native.native_source_hash()`:

`61c25dceaa6d7dd067410c32a493378bfef82ab9686345902b79ae2d883f68e7`

Computed by importing the Python audit module and invoking only its hash
function. The digest includes native tests and vendored Go sources. It replaces
the implementer snapshot
`5fed89f7c6ed1fe44e40b1701b4760d0cf6bdb38a52da0894a8860e9b38b79d6`.
Any subsequent source edit or gofmt changes this attribution and requires a new
digest. Per-file bytes and SHA-256, including the spec and pinned source proof,
are in `native-source-check-20261024-hashes.json` beside this report.

Go236 remains RELEASED: original global sequence 287, confirmed 414. No live
native/SDK handle or reservation is held by this reviewer. Historical native
handle **85731 exited 1** with four retained failures. SDK **21711 exited 0**;
final SDK **70405 / shell PID 64664 exited 0**. SDK passes do not validate the
later native changes. No new Go/gofmt/Dart/Flutter/SDK/test/analyze/build/WSL or
device command was started during this source review. No kill/reset occurred.

## Findings (fixed)

1. **Registration ancestry was not actual retained-callback provenance.**
   `vendor/.../interp/qfli_callsite.go` previously bound the registration caller
   to every direct function argument; a generic native-dispatch stack marker
   could not establish that identity after return or while another native call
   invoked a retained argument. Unknown direct callback arguments now receive
   an opaque `nativeCallback` owner and a source-stack cutoff. Only exact native
   Type + function Pointer + callback argument index 1 for `sort.Slice`,
   `sort.SliceStable`, and `sort.Search` preserve a proven synchronous caller.
   The caller must have a real frame, be non-external, and not be a bare native
   `go` dispatch. `qfli_execution.go` now documents that the generic stack marker
   classifies panic propagation, not caller identity. Synchronous opaque panic
   still propagates to source recover; an external callback panic fails its
   owning epoch.

2. **The retained Helper GC expectation invented an exited caller.**
   `embedded_helper_lifetime_test.go` now expects the live retained callback's
   diagnostic line and rejects registration-main attribution. Both collection
   waves, registry-pruning pressure, retained liveness and actual failed-test
   evidence remain asserted. Ordinary in-call T/F/B Helper tests were unchanged.

3. **The live-owner check raced a new callback's scalar mutation.**
   Product `debugger.go` now snapshots scalar locals inside
   `DebugEvent.WithStoppedValues`. The vendored debugger holds registry lock
   `gLock`, then the stopped owner's `g.mutex`, through eligibility and bounded
   scalar conversion. A callback cannot register and mutate captures during the
   read; Continue/Step cannot resume the owner during it. `interp.go`
   `startGoroutine` reserves a debugger worker count before scheduling, covering
   compiled `go` calls without a source frame and the scheduling-to-registration
   gap. Worker release precedes the epoch token's Done.

4. **Native work can mutate scalar storage after its apparent dispatch ends.**
   This is concrete in the shipped `net/rpc.Client.Go`: it retains the reply
   pointer and an autonomous native input worker writes through it after Go
   returns. `qfli_native_values.go` now latches possible mutable native aliases
   under `gLock` before dispatch. Pointer/map/slice/channel/unsafe-pointer types,
   interface underlying values, and recursive struct/array types are handled
   conservatively. No pointer targets, aggregate field values or heap graphs
   are followed. Native bound receivers are included; custom fmt/errors native
   adapters cannot bypass argument marking. Registered source wrappers mark
   mutable results before returning them to compiled code, covering a callback
   returning `&local` to a native library that writes later. The latch remains
   for the entire debug session and causes explicit unavailable locals:
   `Native code may retain mutable values; locals are unavailable for this session`.
   Exact direct-sort argument 0 has a pinned synchronous/non-retaining borrow
   contract. Ordinary scalar-only args/results remain usable; there is no
   blanket native-call suppression or mutable-alias completion heuristic.

The runtime spec and pending validation coverage table were synchronized.

## Exact pinned source proof

Read the staged SDK files directly; no Go SDK command was run. Its VERSION file
is included in the hash manifest. Current vendored export files use their
`go1.22` build constraints and export the exact reflected native function values.

| Proof | Inspected locations |
| --- | --- |
| Slice and SliceStable invoke their local comparator synchronously and do not retain the slice/comparator | SDK `src/sort/slice.go:24`, `:29`, `:41`, `:44`; `src/sort/sort.go:85` (`lessSwap`) |
| Complete native sorting path remains inline | SDK `src/sort/zsortfunc.go:10` (`insertionSort_func`), `:61` (`pdqsort_func`), `:335` (`stable_func`), their inline helper call tree |
| Search calls its predicate in its own loop | SDK `src/sort/search.go:58` |
| Current public sort symbols are the exact functions checked | `vendor/.../stdlib/go1_22_sort.go` |
| Actual native RPC client input worker is started independently | SDK `src/net/rpc/client.go:201` (`NewClientWithCodec`), `:206` (`go client.input()`) |
| RPC reply alias is retained and written asynchronously | SDK `src/net/rpc/client.go:141` (`ReadResponseBody(call.Reply)`), `:298` (`Client.Go`), `:302` (`call.Reply = reply`), `:231` (gob decode into body) |
| The RPC client API is actually shipped in the interpreter | `vendor/.../stdlib/go1_22_net_rpc.go:16`, `:38` (Client), `:28` (NewClientWithCodec) |

The contracts are exact function-value contracts. A same-signature lookalike in
the regression fixture deliberately retains its comparator and remains opaque.
There is no configurable trust allowlist, goroutine-ID inference, TLS, shared
current-call variable, or production stack-token identity protocol.

## Lock and execution trace

- Value eligibility and snapshot use `gLock -> g.mutex`. Owner registration,
  worker counting and native-escape marking use `gLock`. Snapshot code performs
  scalar conversions only, never user methods/Stringer, native dereference,
  aggregate expansion, debugger reentry or session-lock acquisition.
- Continue/Step release their registry lookup lock before taking `g.mutex`.
  Debug execution releases `g.mutex` before sending an event. `exitCall` releases
  it before owner removal. Terminate collects owners under `gLock`, releases
  it, then takes routine mutexes. Scope/variable enumeration and scalar
  conversion under the guard do not acquire an interpreter frame mutex.
- Session response assembly can take session lock then registry lock. The
  guarded snapshot does not reverse into session lock. The explicit native
  escape-reason accessor is called only on the unguarded unavailable path.
- Epoch registration closes under the same mutex used for token acquisition,
  before Wait. Callback token acquisition precedes owner registration and
  interpreted argument/body mutation. Owner removal happens once, before token
  release. Main owner remains until joined callbacks/workers leave.
- Debug caller links are separate from lexical `.anc`; captured storage remains
  available for execution while displayed/source ancestry ends at opaque entry.
  Event kind/boundary metadata remains available after an owner exits.

## Regression source authored, all UNRUN

`native_callback_provenance_test.go` adds these real execution scenarios:

- Retained direct comparator called after its registrar has actually exited,
  with live fresh owner/step/continue, exact source cutoff, normal return and
  interpreted synchronous recover.
- Registrar still blocked while two other dispatches independently invoke and
  pause its retained argument; one callback can resume/leave while the other
  remains live and held. Exactly-once body/owner accounting is asserted.
- External retained-argument panic fails its epoch and leaves no live owners.
- Actual SliceStable/Search callbacks preserve main's identity; existing direct
  and deferred Slice identity checks remain unchanged. A same-signature native
  registrar receives no trust. Bare `go sort.Slice` has a fresh opaque callback
  owner and later drains its worker exclusion.
- A stopped-main scalar snapshot holds its registration guard until an actual
  native callback contender is observed waiting in `enterRoutine`, reads 42,
  then releases the callback to mutate to 99. Stack inspection synchronizes this
  test only; production provenance does not use it.
- A compiled native `go` worker with no source frame and no pointer arguments
  suppresses locals until it leaves, then eligibility returns. This independently
  tests the worker count without relying on the mutable-escape latch.
- A real `rpc.Client` with a channel-controlled native codec retains `&reply`,
  mutates 42 to 99 while main remains stopped, and keeps locals explicitly
  unavailable even after mutation completes. No socket/server is required.
- A retained native call obtains `&local` through an interpreted callback's
  interface result, returns, then a real native goroutine mutates it later.
  Locals stay unavailable, owner/body accounting and output99 are checked.
- Pure scalar native callback args/results and ordinary fmt.Print leave value42
  readable and preserve normal output. Existing ordinary scalar/Helper tests
  were not weakened to accommodate unavailable locals.

The fixture channels contain detached snapshots; its retained event pointer is
used for eligibility probes only while that same owner remains stopped. Cleanup
unblocks native fixtures before Terminate/Wait.

Promoted native method-expression receiver projection, nested/interface/deferred
coverage, by-value rejection, weak registry lease/pruning and callback close
ordering were also inspected against the implementation handoff. No additional
concrete defect was established in those paths during this review.

## Findings (not fixed) and pending verification

- No remaining concrete source finding is intentionally left unrepaired within
  this review scope. Runtime correctness is UNVERIFIED: no new source has been
  compiled or executed since the historical failing native handle85731.
- The native escape gate is deliberately conservative and sticky. It supports
  tracked interpreter storage with valid safe-Go use, not arbitrary unsafe
  memory access or native heap/aggregate introspection. Unknown native APIs do
  not receive a fabricated release point. This is not a blanket race-safety
  claim for arbitrary native code.
- **gofmt: NOT RUN.** First later named grant must format the owned Go files and
  recompute the digest before executable attribution.
- **Lint/vet: NOT RUN. TypeCheck: NOT RUN. Tests: NOT RUN.** The explicit released
  Go236 slot prohibits these commands until another named grant. Static checks
  are not a substitute for any of them.
- Scoped `git diff --check`: PASS (exit0; Git reported only LF/CRLF conversion
  notices). Python whole-file final-newline/trailing-whitespace/merge-marker
  checks on all owned sources/docs, including untracked files: PASS.
  Lightweight lexical duplicate-test-name scan, excluding embedded source
  fixture strings: PASS; this does not establish Go syntax/type correctness.
- Next named Windows window: after gofmt/fresh digest run serial full
  `go -C native/go_runtime test -mod=vendor -count=1 -timeout=90s -v ./...`, then
  `go -C native/go_runtime vet -mod=vendor ./...` if the grant permits. Capture
  exact tool/session handle, shell PID, terminal exit and elapsed time; retain
  all failures; recompute digest; release immediately. Use the pinned local
  offline SDK and bounded process-local settings in the validation plan.
- Actual **Linux race** execution still needs a separate named WSL/resource
  grant. Include lifecycle/Helper/provenance/snapshot/native-escape tests and
  real symlink comparisons. Passing injected race-gate tests is insufficient.
- Actual rebuilt DLL + Dart FFI, all five Android/OHOS rebuilds, exact packaged
  HAP inspection/signature, original364 and expanded844 corpus, and handed-off
  target product execution remain separate open gates in the validation plan.

This handoff closes the source-review ownership only. It does not close the
standalone-product objective or authorize any runtime/resource command.
