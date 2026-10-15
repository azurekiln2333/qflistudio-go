# Go curriculum — mobile / native-runtime validation (R5, AC2)

> Reviewer: trellis-check `w8:p4`. Scope: prove or refute mobile-support claims
> against **this project's** runtime, and record the evidence level honestly.
> No device/emulator run; no native code changed.

## Evidence levels (explicit)

1. **Host official Go** — `verify.py` runs the real sample with the pinned
   `native/build/go-sdk-1.27.1/go` (desktop proof).
2. **Host Yaegi interpreter** — same Yaegi pin as the shipped runtime, run on
   the host (`tool/go_curriculum/mobile_check/`). Proves the interpreter accepts
   and runs the sample; **not** a device run.
3. **Host `-race`** — real `go test -race` under WSL with the project-pinned
   linux SDK. Desktop concurrency proof; **not** a device run.
4. **Device/emulator** — Android/OHOS/iOS `integration_test/go_native_test.dart`.
   **Not performed here.**

A mobile claim may only be asserted at level 4. Levels 1–3 are supporting
evidence, not a device guarantee.

## Shipped runtime

- `native/go_runtime/go.mod`: Yaegi `v0.16.2-0.20260209085605-fcb76d1ece0c`.
- `go build ./...` OK; `go test ./...` OK on host (multi-file / os.Exit cases
  pass).
- Note: no `vendor/` directory present locally, though spec says builds use
  `-mod=vendor`. Host module build still resolves from module cache.

## Host Yaegi probe

`tool/go_curriculum/mobile_check/main.go` creates a Yaegi interpreter with
`stdlib.Symbols` and `EvalPath(file)`, mirroring `native/go_runtime/runtime.go`'s
interpreter setup. `run_yagi.py` runs every single-file sample and compares
stdout to the declared `verification.expected`.

## Host-native probe (the shipped runtime path)

Bare Yaegi (`main.go`) only proves the interpreter version accepts a sample. It
does **not** exercise the shipped runtime's local vendor fixes, the
`projectSourceFS` lookup, or the app's symbol/import constraints. To get
host-native evidence, `run_native_check.sh` injects a check-only test into
`native/go_runtime` via `go test -overlay` (build tag `hostcheck`, no real file
modified) and calls the real **`runGo`** — the same function the mobile FFI uses.

Evidence level: **HOST-native interpreter** (vendored Yaegi + project FS +
stdlib). Still **not** a device run.

Result over all 87 single-file candidates (`evidence/native-check-host.json`):

**4 non-zero exits (panics):**

| Topic | Runtime panic | Area |
| --- | --- | --- |
| T040 | `reflect: Call with too many input arguments` | method expressions |
| T047 | `reflect.Set: value of type interp.valueInterface is not as…` | interface/strategy assignment |
| T052 | `errors: *target must be interface or implement error` | `errors.As` |
| T053 | `errors: *target must be interface or implement error` | custom error + `errors.As`/`Unwrap` |

**5 stdout differences vs official Go:**

| Topic | Cause |
| --- | --- |
| T008 | `%T` of a named type (`main.point` vs `struct{…}`) |
| T045 | Stringer/value formatting inside a composite differs |
| T058 | `errors.Join`/`Unwrap` chain not reproduced |
| T096 | `text/template` rendered **empty** |
| T116 | `log/slog` output **empty** (not captured/unsupported) |

All affected topics are `desktop`, so no mobile claim is wrong today. These are
recorded as **mobile blockers**: any of T008/T040/T045/T047/T052/T053/T058/T096/
T116 must not be promoted to `mobile` without a passing host-native run *and*
ultimately a device run.

### Classification (per user decision)

These are **native capability limits, not content defects** — all six (T040,
T047, T052, T053, T096, T116) pass **official Go** (`verify.py --only` confirmed;
and T047/T052/T053 are in the passing evidence set). Closure action is therefore:

- keep them **desktop-only** (already true); do NOT change the runtime and do NOT
distort the lesson to force Yaegi compatibility;
- the lesson text must state the platform limit (mobile Yaegi unsupported /
empty output), so R5/AC2 honesty holds;
- keep the evidence.

Genuine content determinism issues remain separate and must be fixed:
**T083** (context timing) and **T088** (dir size, filesystem-dependent).

The bare-Yaegi probe had only surfaced T008/T040; the **native** path also
exposes T047/T052/T053 (panics) and T045/T058/T096/T116 (output) — confirming
that "same Yaegi pin" is not equivalent to this project's runtime.

Result (bare Yaegi, first pass, 80 single-file samples): **79 OK, 1 diff**.

| Topic | Official Go | Host Yaegi | Verdict |
| --- | --- | --- | --- |
| T008 | `t=main.point` | `t=struct { X int; Y int }` | differs — `%T` on a named type |
| T040 | prints 3 method-value/expression lines | `panic: reflect: Call with too many input arguments` | **panics** — method expression `rect.area` |

Both are classified `desktop`, so neither is a defect today. They are recorded
so that T008 (any `%T`-of-named-type) and T040 (method expressions) are **never
promoted to mobile** without an interpreter-specific expected output and a
passing interpreter run.

## Interpreter capability gaps observed (for R5)

- **Method expressions** (`T.method`, `(*T).method` stored and called) — Yaegi
  panics via `reflect: Call with too many input arguments` (T040).
- **`%T` of a named type** — Yaegi prints the underlying struct type, official Go
  prints `main.point` (T008).
These join the curriculum-map's known `Yaegi*` caveats (generics, embed,
reflect, net, timers, templates, filesystem).

## Host `-race` (concurrency gate)

Environment discovered without any download/install:

- WSL distro **`qfli-java-build`** ships `gcc 13.3.0` (`/usr/bin/gcc`).
- Project-pinned linux Go: `native/build/go-linux-1.27.1/go` (go1.27.1 linux/amd64).
- `GOROOT` → that SDK, `CGO_ENABLED=1`.

`tool/go_curriculum/mobile_check/run_race.sh` runs `go test -race ./...`:

| Topic | Kind | `-race` result |
| --- | --- | --- |
| T077 | test-package (Mutex) | RACE-OK |
| T078 | test-package (RWMutex) | RACE-OK |
| T080 | test-package (Pool+bench) | RACE-OK |
| T081 | test-package (atomic) | RACE-OK |

The w8:p3 progress note "`-race` unavailable → fall back to plain `go test`" is
**obsolete** and was sent back for correction.

## Mobile claims in current content

All 120 authored topics are `runtime: desktop`; **none** claim mobile. The Go
content test enforces: a `mobile` claim must pair with
`importKind=single-file` and a stdout (non-test/bench) verification kind. No
violations today.

## Host-native vs device (evidence separation)

| Level | What it proves | What it does NOT prove |
| --- | --- |
| Official Go host | sample compiles/runs on desktop | anything mobile |
| Bare Yaegi host | version accepts sample | shipped runtime behaviour |
| **Host-native (`runGo` via overlay)** | shipped runtime path (vendor fixes, FS, symbols) | device/OS behaviour |
| Device/emulator | actual phone execution | — (not run) |

Final report must label every mobile-relevant claim with its level; no topic is
device-verified.

## Limitations / what is NOT proven

- No Android/OHOS/iOS device or emulator run: mobile execution is **unverified**
  for every topic. Do not ship mobile labels on this evidence.
- Host Yaegi ≠ device Yaegi: filesystem, `net`, timers, `context` behaviour can
  differ on mobile (e.g. T086/T088/T093/T096 are `Yaegi*` in the curriculum map
  and remain desktop here).
- The `-race` result is desktop-only.
