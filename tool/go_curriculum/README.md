# Go curriculum tooling

Maintainable source and tooling for the Go learning content used by the Go app.

## Layout

| Path | Purpose |
| --- | --- |
| `schema.md` | Authoring contract for one topic file (both authors) |
| `GUIDE.md` | Learner entry: roadmap, chapter index, run commands, diagnostics, limits |
| `topics/T<NNN>.json` | One topic = one tutorial + one example + verification |
| `samples/T<NNN>/` | Runnable Go source (with `go.mod`) backing the topic |
| `baseline/` | Captured pre-change Go slice + shared-file hashes (rollback) |
| `assemble.py` | topics -> `content/go/{tutorials,examples}.json` + `classify.json` |
| `verify.py` | compile/run every topic + independent example variant |
| `test_verify_race.py` | self-test: `--race` gate is fail-closed (mocked, no WSL) |
| `dedup.py` | substantive-duplication detection |
| `patch.py` | emit/apply the Go-only slice for the shared aggregate files |
| `evidence/` | per-item verification results |

## Workflow

```powershell
$go = "native/build/go-sdk-1.27.1/go/bin/go.exe"
python tool/go_curriculum/assemble.py
python tool/go_curriculum/verify.py            # uses the pinned SDK
python tool/go_curriculum/dedup.py
python tool/go_curriculum/patch.py emit
```

`verify.py` sets `GOMAXPROCS=2`, `GOFLAGS=-p=1`, `GOTOOLCHAIN=local` and a local
`GOCACHE`, and binds the pinned SDK to `PATH` for each `runCommand`.

`--go` path handling: the SDK path may be **absolute or relative** (e.g.
`--go native/build/go-sdk-1.27.1/go/bin/go.exe`); `find_go` resolves it to an
absolute path because `runCommand` runs with `cwd=<sample dir>` while the SDK
dir is prepended to `PATH`, so a relative path would otherwise become an
unusable PATH entry and every topic would fail with `'go' is not recognized`.
An explicit `--go` that does not exist is a hard error (`VERIFY FAIL: --go SDK
not found: <path>`, exit 1) and does **not** silently fall back to the bundled
SDK; a typo therefore cannot run an unintended toolchain. With no `--go`, the
bundled SDK (or `QFLI_GO_CURRICULUM_GO`) is used.

`--race` is a **fail-closed gate**, not an annotation. When `--race` is given,
every selected topic must report exactly `RACE-OK`; a `RACE-FAIL`, a missing
result, or a race-gate error (WSL failure, non-zero exit, timeout, missing
gate script) all count as failures and make the run exit non-zero. A race
result is never fabricated: if the gate cannot run, verification fails rather
than passing silently. (Regression: `tool/go_curriculum/test_verify_race.py`
asserts this with a temp evidence dir and a mocked gate.)

## Verification gates (final, 120/120)

- assemble: 120 tutorials, 120 examples from 120 topics.
- verify: **120 passed, 0 failed** (`evidence/verify-results.json`). Per-topic
  byte-match of `tutorial.code` to its sample, forced real compile
  (`go build ./...` for module dirs, `GO111MODULE=off go build -o tmp .` for
  module-less dirs) plus the declared run assertion; distinct example variants
  asserted against their own `expectedOutput`; anti-spoof `runCommand` checks.
- dedup: no substantive duplication in 120 topics.
- patch dry-run vs real shared: non-Go kept=1520, Go replaced 100 -> 120.

### Yaegi mobile boundary (do not mis-promote)

The definitive matrix is `research/mobile-validation.md`. All 120 topics are
`desktop` (official Go only); none device-verified, so none are promoted to
`mobile`. Empirically confirmed against this project's native runtime:
method expressions (T040), interface assignment via reflection (T047),
`errors.As` (T052/T053) panic; `%T` on named types differs (T008);
Linux-only context timing (T083) and dir size (T088) differ. `text/template`
(T096) and `log/slog` (T116) previously produced empty stdout under native
capture — both samples were **fixed to render into a buffer then print**, and
now emit their declared output under official Go; they remain `desktop` pending
device verification.

## Status

- 120/120 topics; **verify 120 passed / 0 failed** (`evidence/verify-results.json`).
- assemble 120/120, dedup clean, patch dry-run: non-Go kept=1520, Go 100→120.
- **Integrated**: the Go slice is applied in `../qfli_studio_core` commit
  `8731df8` — the shared aggregates now carry 120 Go tutorials + 120 Go examples
  (1640 entries each: 1520 non-Go preserved + 120 Go), and the application asset
  load + shared-parser suite passes (13 checks). This is the current released
  state; nothing about this round is awaiting authorization.

## Shared integration

`patch.py emit` writes a reviewable patch under `patch-go/`. The transform is a
**raw byte-splice**: it locates the contiguous Go run inside `entries[]` and
replaces exactly those bytes. Every other byte is preserved, and because the
non-Go bytes before/after the run are unchanged, each non-Go entry keeps its
**relative position around the Go block** (this is relative-block preservation,
not an absolute byte-offset guarantee, since the Go block's own length changes).
No whole-file JSON round-trip. Guarantees:
- `dry-run` executes the same transform + validation as apply and writes nothing.
- unknown Go edits: if the current Go entries differ from `baseline/`, apply
  refuses and changes nothing.
- exclusivity: apply opens both targets with `CreateFileW` denying write/delete
  sharing, so a competing writer — including a non-cooperating one that never
  takes our lock — is refused (the open fails, apply aborts, no file changes).
  **Mutation is Windows-only** (`sys.platform == "win32"`); on any other OS apply
  is fail-closed (`shared mutation requires Windows file sharing locks`), because
  advisory `flock` cannot stop a non-cooperating writer.
- both targets are verified before either is written; on a write failure the
  already-written targets are restored from the in-memory originals, so the pair
  stays recoverable. This is **in-process exception recovery**, not a power-loss
  transaction — a process kill mid-write is covered by `--backup` originals.
- `rollback --confirm` restores only the Go entries, preserves the latest non-Go
  edits, and is protected by the same `CreateFileW` exclusivity.

The Go slice for this release was already integrated this way (commit `8731df8`).
**Any future change to the Go content or tooling must still go through the same
single authorized integration step** — never a blind overwrite and never an
uncoordinated write from a content-authoring pane.

Precise apply command (authorized use only):

```powershell
python tool/go_curriculum/patch.py apply `
  --shared ../qfli_studio_core/assets/content `
  --patch tool/go_curriculum/patch-go `
  --baseline tool/go_curriculum/baseline `
  --backup tool/go_curriculum/apply-backup --confirm
```

## Not owned here

Do not edit the Go runner, native runtime, terminal flow, generated `.so`/`.h`,
or any non-Go content from this tree.
