# Native artifact verification — preparation (revised)

Status: verifier ready. Awaiting the fresh rebuild. No fresh binary verification
claimed. No production source/tests touched. Artifact ownership only
(`research/`).

## Deliverable

`research/native_artifacts_verify.py` — Python standard library only, no third
party installs, read-only inspection. CI-safe exit code: 0 all checks passed,
1 any failure.

## Phase `libs`

For the five bundled `libqfli_go_runtime.so` files, report SHA256, ELF class,
ELF machine, byte size and every `PT_LOAD` alignment. Require ABI directory ↔
ELF class ↔ ELF machine agreement. Android members additionally require every
`PT_LOAD` alignment `>= 0x4000` (16 KiB).

| Label | Expected class | Expected machine | 16 KiB PT_LOAD |
| --- | --- | --- | --- |
| android arm64-v8a | ELF64 | EM_AARCH64 | required |
| android armeabi-v7a | ELF32 | EM_ARM | required |
| android x86_64 | ELF64 | EM_X86_64 | required |
| ohos arm64-v8a | ELF64 | EM_AARCH64 | informational |
| ohos x86_64 | ELF64 | EM_X86_64 | informational |

## Phase `packages`

ZIP members are discovered from archive contents (`endswith
libqfli_go_runtime.so`) and mapped by ABI directory plus product line, adapting
to the observed layout:

- APK observed: `lib/<abi>/libqfli_go_runtime.so`
- HAP observed: `libs/<abi>/libqfli_go_runtime.so`

For **every** member:

1. Parse the packaged ELF; require its class and machine to match the ABI
   directory and the matching rebuilt file.
2. Android members require packaged `PT_LOAD >= 0x4000`.
3. Require allocated-section equivalence with the rebuilt file (see below).
   Byte-identical members are accepted as the fast path.

A declared `--apk`/`--hap` path that is missing is a hard `FAIL`. An omitted
optional argument is allowed and skipped. A differing whole-file hash is never
treated as a pass by itself.

## Exact equivalence method (stripping-independent)

Packaging may strip debug/symbol/string sections, changing the whole-file hash.
Loaded code and data are the `SHF_ALLOC` sections, so equivalence is defined on
those:

- Collect every section with `SHF_ALLOC` set and a non-empty name in both the
  packaged copy and the rebuilt file.
- Require the same set of allocated section names; a name present in only one
  side fails.
- For each name, require equality of:
  - section type (`sh_type`),
  - flags (`sh_flags`),
  - load address (`sh_addr`),
  - size (`sh_size`).
- For every allocated non-`SHT_NOBITS` section, additionally require identical
  content bytes: `SHA256(file[sh_offset:sh_offset+sh_size])` must match.
- `SHT_NOBITS` sections (`.bss`, `.tbss`) must match metadata and **size**;
  they have no file bytes, so no content hash applies.

Any allocated-section mismatch fails the member with the exact section name and
the two hashes/sizes. Non-allocated sections are ignored on purpose, which is
what makes a stripped copy verifiable without depending on debug data.

## Mechanical smoke test (existing pre-rebuild artifacts)

Run only to confirm parsing, path adaptation and the failure paths. This is NOT
fresh verification of the new runtime; the files predate the source change.

| Scenario | Result |
| --- | --- |
| `libs` | PASS — Android `LOAD_align=0x4000`, OHOS `0x1000` |
| `packages` with existing APK + HAP | PASS — APK members byte-identical; HAP members differ in whole-file hash but all 31 allocated sections match (metadata + allocated bytes) |
| declared missing `--apk` (`does-not-exist.apk`) | FAIL (`declared archive not found`), exit 1 |
| declared missing `--hap` (`nope.hap`) | FAIL, exit 1 |
| omitted `--apk`/`--hap` | PASS / skipped, exit 0 |
| stale runtime: one `.text` byte flipped in the APK copy | FAIL with `..text: content <a> != <b>`, exit 1 |

The stale-runtime case is the explicit regression for the review concern: a
mismatched archive never yields PASS.

## Usage after rebuild

```powershell
python .trellis/tasks/10-09-terminal-flow-pi/research/native_artifacts_verify.py --phase libs
python .trellis/tasks/10-09-terminal-flow-pi/research/native_artifacts_verify.py --phase packages `
  --apk <fresh.apk> --hap <fresh.hap>
```

Optional `--root <repo>` overrides the repository root.

## Boundaries respected

- No file deleted outside pi's scratch directory (verified absolute target
  inside `.artifacts/terminal-flow-pi` before any delete).
- No global settings changed, no dependency installed.
- No rebuild performed and no fresh-binary pass claimed.
- Only `research/native_artifacts_verify.py` and this report are owned/added.
