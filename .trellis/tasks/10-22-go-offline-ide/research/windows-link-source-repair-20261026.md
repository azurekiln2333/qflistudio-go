# Windows native linker source repair — 2026-10-26

Status: SOURCE CANDIDATE. Compiler/linker execution and all native tests remain
UNRUN on these changed bytes. Grant655 was consumed and released661. This file
requests no new grant and claims no runtime pass.

## Boundary and observed failure

Only `native/go_runtime/windows-cc.cmd` and this handoff were edited. The original
adapter was already untracked; it was not added to the index. No other source,
toolchain file, binary, library, frozen runner, common core or sibling changed.

Actual evidence:
`research/go-native-next-20261026-01/native/test.stderr.bin` records the external
Windows test linker failing with `unable to find library -lgcc_eh` twice. The
command invokes the adapter with `-m64`, link flags, `export_file.def`, `go.o`
and `000000.o` through `000009.o`. No native test executed; vet was UNRUN.

Recorded environment:

- Clang: `D:/ProgramFiles/Huawei/DevEco Studio/sdk/default/openharmony/native/llvm/bin/clang.exe`.
- MinGW root: `D:/ProgramFiles/Dev-Cpp/MinGW64`.
- GCC library directory: `lib/gcc/x86_64-w64-mingw32/4.9.2` below that root.

That directory contains `libgcc.a` and `libgcc_s.a`, but no `libgcc_eh.a`.
Byte inspection of the import archive identifies `libgcc_s_seh_64-1.dll`.
That DLL exists in MinGW `bin`, already included in the frozen runner's PATH.
No library was copied, synthesized, renamed or downloaded.

## Source change and reasoning

The adapter scans its existing arguments without invoking another process.
An object-file link (`.o` or `.obj`) with no source input or compile/preprocess
option selects `--driver-mode=g++ -nostdlib++`. All C/source compilation,
preprocessing and syntax-only invocations retain the original driver. The
existing target, sysroot, GCC library path, lld selection and argument forwarding
remain in place. The compiler's exit code is returned unchanged.

Upstream LLVM15.0.4 `clang/lib/Driver/ToolChains/MinGW.cpp`,
`tools::MinGW::Linker::AddLibGCC`, selects `-lgcc -lgcc_eh` for a non-shared C
executable. For the C++ driver it selects `-lgcc_s -lgcc`. Its link job calls
`ShouldLinkCXXStdlib`; `-nostdlib++` prevents an extra C++ standard-library link.
This uses the installed shared GCC runtime while preserving C compilation.
It avoids manually duplicating the full CRT/system default-library list.

The exact failing command is an object-only external link, so it takes the new
branch. The pinned Go source `src/cmd/cgo/gcc.go:1804-1811` supplies `-c -xc` for
C probes, so those remain on the original compiler branch.

`shift /1` advances only positional inspection. Windows documents that SHIFT
leaves `%*` unchanged. The final invocation forwards the original `%*`, including
its quoting. `setlocal EnableExtensions DisableDelayedExpansion` confines local
variables and preserves literal exclamation marks. Source extensions and
`-c`, `-E`, `-S`, `-fsyntax-only`, `-M`, `-MM` prevent the link-driver override.

Primary source references, read without running a compiler:

- LLVM `llvmorg-15.0.4`, `clang/lib/Driver/ToolChains/MinGW.cpp`,
  `Linker::AddLibGCC` and `Linker::ConstructJob`.
- Microsoft Learn, Windows `shift` command, Remarks (`%*` behavior).
- Installed Clang resource tree: `lib/clang/15.0.4`.

The installed Huawei compiler may carry vendor changes. Upstream source plus
installed library inventory establishes this candidate's rationale; only a fresh
bounded execution can establish that the actual compiler behaves as expected.

## Identities and static checks

| Artifact | SHA-256 |
| --- | --- |
| Adapter before | `12e254f89d532b497ba63598c4559a6a985340feb367aa24cf7156c5296268b0` |
| Adapter after | `5c486c5420c7d74178250e03fa52061c7df638418560744d587bbba7e36c4f8b` |
| Installed libgcc.a | `3bcd1cb8b97a84ffb1c8d4921e781c2b4bbada235225ba1e7e6a31bb7880a58e` |
| Installed libgcc_s.a | `c11d5f7b2dc2a0456362a8afa64467bd2394df139860c0509a2f6181113c9eae` |
| Installed runtime DLL | `3d43be679b49ea6996b9b3b0c2ee3a7e5b219e251584f1e550f309bd832a388f` |
| Frozen runner, unchanged | `9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8` |

After: 2062 bytes, 40 lines, ASCII/LF, final newline, no trailing whitespace.
Text checks verified every GOTO target, compile/source guards, original `%*`
forwarding and the final exit-code propagation. No batch interpreter execution
or compiler dry-run occurred. `git diff --check` had no findings, but the adapter
is untracked, so the direct byte/text checks are the actual whitespace evidence.

The native suffix digest does not include `.cmd`. Preserve the formatter's
current native source digest
`574b1478dd41ce41e23a632fb2624ec6168c209d6c38420b0e027b6ef2859298`;
this edit changes the adapter's separate tool identity. The frozen runner already
includes the adapter in its pre/post tool hash set. Do not replay655 or reuse
its pre-repair adapter identity for a new execution.

## Required next validation and limits

A separate check worker should review the adapter before any new READY. Under a
fresh named grant, rebind its new hash, verify genuine compile and object-link
invocations, run actual native tests, then vet only if tests pass. No native,
race, DLL, FFI, corpus, SDK, HAP or OHOS gate closes here.

The shared GCC import archive can introduce a dependency on
`libgcc_s_seh_64-1.dll` when its symbols are used. The host runner can find the
installed DLL through its explicit PATH. A later packaged desktop DLL must have
its real dependencies inspected and shipped lawfully if required; this source
change makes no packaging or redistribution claim.

Compile-and-link commands with source inputs deliberately keep the original C
driver. This focused adapter repair targets Go's observed object-only external
link. If a future actual Go invocation exposes the same failure in a source-link
probe, record that command and expand the supported case through review rather
than silently changing the source language or suppressing linker diagnostics.
