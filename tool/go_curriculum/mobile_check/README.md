# mobile_check — host-side runtime probes (check-time only)

Not product code. These tools give **host-side** evidence for the runtime-honesty
gate (R5). They never touch `native/go_runtime` or the shared assets.

## Evidence levels

1. Official Go on host: `../verify.py` (owner w8:p2).
2. **Bare Yaegi on host** — `main.go` + `run_yagi.py`. Same Yaegi *version pin*
   only. Proves the interpreter version accepts a sample; does **not** include
   the shipped runtime's local vendor fixes, `projectSourceFS`, or symbol/import
   limits. **Never sufficient for a mobile claim.**
3. **Host-native** — `run_native_check.sh` + `native_hostcheck_test.go`. Injects
   a check-only test into `native/go_runtime` via `go test -overlay` (tag
   `hostcheck`; no real file modified) and calls the real **`runGo`** — the exact
   function the mobile FFI uses. This is the strongest non-device evidence.
4. **`-race` on host** — `run_race.sh`, via WSL `qfli-java-build` (gcc 13.3.0) +
   project linux SDK `native/build/go-linux-1.27.1/go`. Desktop proof only.
5. Device/emulator: `integration_test/go_native_test.dart` — not run here.

A `mobile` label requires level 5. Levels 1–4 never justify a mobile claim.

## Commands

```powershell
# bare Yaegi first screen (all single-file topics, or a subset)
python tool\go_curriculum\mobile_check\run_yagi.py
python tool\go_curriculum\mobile_check\run_yagi.py --only T008,T040

# host-native: drive the real runGo over candidate sample dirs (copy first)
#   windows: go test -mod=vendor -tags hostcheck -overlay <ov> -run TestHostNativeCandidateSamples
#   wsl:     wsl -d qfli-java-build bash .../run_native_check.sh <samples-dir> <out.json>

# real -race (WSL qfli-java-build)
wsl -d qfli-java-build bash /mnt/d/MyNewProjects/qfli_go/tool/go_curriculum/mobile_check/run_race.sh T077 T078

# patch.py invariant audit (sandbox, no real shared write)
#   asserts R1 raw-non-Go span/order, R2 unknown-Go rejection (baseline digest),
#   R3 lock/single-writer, R4 failure recovery; plus dry-run no-write and
#   apply-without-confirm refusal.
python tool\go_curriculum\mobile_check\audit_patch.py

# rehearsal: apply/rollback on a WORKSPACE COPY of the real shared files
#   (never touches the real shared dir); verifies non-Go raw bytes + relative
#   order, Go 100->120, rollback restores 100, real shared untouched.
python tool\go_curriculum\mobile_check\rehearse_real_apply.py

# post-apply byte-invariance check (run ONLY after an authorized real apply)
python tool\go_curriculum\mobile_check\verify_shared_apply.py --shared ../qfli_studio_core/assets/content --backup tool/go_curriculum/apply-backup
```

## Observed boundaries (see task research/mobile-validation.md)

- Native-path panics: T040 (method expression), T047 (interface assign),
  T052/T053 (`errors.As`).
- Output diffs: T008, T045, T058; Linux-only T083 (context timing), T088 (dir
  size); T096 (template) / T116 (slog) stdout empty under native capture.
- All affected topics are `desktop`; these facts only forbid future mobile
  promotion.
