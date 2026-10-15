# Native package verification report — final frozen packages

Status: **PASS.** All five rebuilt runtime libraries are accounted for in the
frozen APK and HAP. Artifact verification only; no code or library changes.

## Inputs

| Artifact | SHA256 | Bytes | Timestamp |
| --- | --- | --- | --- |
| `build/app/outputs/flutter-apk/app-debug.apk` | `290E491C076A9E4A57E6643113A2E4FD42B7C254C96E797A4CB506EC233014E0` | 253711854 | 2026/10/9 13:06:40 |
| `build/ohos/hap/entry-default-signed.hap` | `08A5994557E178F275762E7DB36E2DD7DA788ECE1A1D74FCFB58917B9F98185F` | 160526085 | 2026/10/9 13:35:58 |

Command:

```powershell
python .trellis/tasks/10-09-terminal-flow-pi/research/native_artifacts_verify.py `
  --phase packages `
  --apk D:\MyNewProjects\qfli_go\build\app\outputs\flutter-apk\app-debug.apk `
  --hap D:\MyNewProjects\qfli_go\build\ohos\hap\entry-default-signed.hap
```

Result: `RESULT: PASS`, exit 0. Raw output:
`.artifacts/terminal-flow-pi/native-package/verify-packages.txt`.

Note: the APK/HAP are normal `lib/main.dart` application builds, not the test
entry. This check verifies packaged native bytes only.

## Rebuilt library baseline (from the prior build)

| ABI | Rebuilt SHA256 | Bytes |
| --- | --- | --- |
| android arm64-v8a | `52AB502DF25279781BE4E0F4662603A7E4DDF4C638F8E3AD77A97DD2E5ED5C13` | 21125520 |
| android armeabi-v7a | `7633DD2401964F8391003A0F6542DBDF7D2E593DEDFA5F47DF650F0AEDB039E7` | 21283044 |
| android x86_64 | `6A387E79AA76489245540851DE5E39969A3A8446DB2302C79444B479161EE8DA` | 22713744 |
| ohos arm64-v8a | `5D1F178B84A5A5DE7C90D54850F8BCDCB7D750086EE8E1E4224B46DE259EEE3B` | 21182864 |
| ohos x86_64 | `A2AEB225461FBF21B6FFEC08D6FEB8FE76BBCEF73E00DD12186145DB1145C6F3` | 22782640 |

## Discovered members and equivalence

### APK — members `lib/<abi>/libqfli_go_runtime.so`

| Member | Equivalence | Packaged SHA256 |
| --- | --- | --- |
| `lib/arm64-v8a/libqfli_go_runtime.so` | byte-identical to rebuilt android arm64-v8a | `52ab502d…5c13` |
| `lib/armeabi-v7a/libqfli_go_runtime.so` | byte-identical to rebuilt android armeabi-v7a | `7633dd24…39e7` |
| `lib/x86_64/libqfli_go_runtime.so` | byte-identical to rebuilt android x86_64 | `6a387e79…e8da` |

Android packaged class/machine matched (ELF64/EM_AARCH64, ELF32/EM_ARM,
ELF64/EM_X86_64) and every packaged `PT_LOAD` alignment is `0x4000` (16 KiB).

### HAP — members `libs/<abi>/libqfli_go_runtime.so`

HAP packaging re-strips the shared libraries, so whole-file hashes differ from
the rebuilt files. Equivalence is established on the loaded image: every
`SHF_ALLOC` section must match by name, type, flags, load address and size, with
identical bytes for allocated non-`SHT_NOBITS` sections (`SHT_NOBITS` compared
by metadata and size). Non-allocated/debug sections are intentionally ignored.

| Member | Rebuilt | Archive | Equivalence |
| --- | --- | --- | --- |
| `libs/arm64-v8a/libqfli_go_runtime.so` | `5d1f178b…ee3b` (21182864 B) | `6ef228fd…425b` (21182680 B) | **PASS** — all 31 allocated sections match (metadata + allocated bytes) |
| `libs/x86_64/libqfli_go_runtime.so` | `a2aeb225…c6f3` (22782640 B) | `9a541331…2cc4` (22782456 B) | **PASS** — all 31 allocated sections match (metadata + allocated bytes) |

Packaged OHOS class/machine matched (ELF64/EM_AARCH64, ELF64/EM_X86_64); PT_LOAD
alignment `0x1000` (OHOS has no 16 KiB requirement).

The byte-count deltas (184 bytes each) are explained by the removed
non-allocated sections; no allocated section differs.

## Conclusion

- 3/3 Android ABI members are byte-identical to the rebuilt libraries.
- 2/2 OHOS ABI members are loaded-image-equivalent (all allocated sections match).
- All five rebuilt libraries are present in the frozen packages and none is
  stale or altered in its loaded code/data.

Cross-check (reported by Codex, not re-run here): Android and OHOS device
integration passed 3/3 after the rebuild; the full Flutter suite passed 68/68.

## Boundaries respected

- No Flutter run, device install, build, code or library change.
- No Git staging/commit. Raw output kept under `.artifacts/terminal-flow-pi`.
