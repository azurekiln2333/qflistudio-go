# Windows linker adapter independent source check — 2026-10-26

Status: **SOURCE PASS** on the exact adapter bytes below. No source blockers found. Genuine link, test and vet validation remain **UNRUN**. Grant655 is consumed; this report requests no grant.

## Scope and changes

Checked `native/go_runtime/windows-cc.cmd`, the implementer handoff, the actual failed grant655 linker command, and the frozen runner environment. The adapter was not changed. Only this report was written. Formatter changes to `native_callback_provenance_test.go`, common/sibling code and frozen runners were preserved. No git mutation occurred.

## Current identities

- Adapter SHA-256: `5c486c5420c7d74178250e03fa52061c7df638418560744d587bbba7e36c4f8b` (2062 bytes,40 lines).
- Frozen runner SHA-256: `9a80246e8e958f0023b9b80a1c92b6bb11404e4a29780779fa920549c84834a8` (unchanged).
- Native suffix inventory:374 files, SHA-256 `574b1478dd41ce41e23a632fb2624ec6168c209d6c38420b0e027b6ef2859298` (unchanged after grant655 formatting).
- Installed `libgcc_s.a`: `c11d5f7b2dc2a0456362a8afa64467bd2394df139860c0509a2f6181113c9eae`.
- Installed `libgcc_s_seh_64-1.dll`: `3d43be679b49ea6996b9b3b0c2ee3a7e5b219e251584f1e550f309bd832a388f`.

The adapter is a separate tool identity because the native suffix digest excludes `.cmd`.

## Findings fixed

None. No mechanical or local source defect was found in the supported command path.

## Verified behavior from source

1. The actual failed command contains `go.o`, ten numbered `.o` inputs and a `.def`, with no C/source input or compile/preprocess flag. It reaches `--driver-mode=g++ -nostdlib++`.
2. `-c`, `-E`, `-S`, `-fsyntax-only`, `-M`, `-MM` and listed source extensions take precedence over object detection. C compilation and preprocessing retain the original driver. The installed Go cgo source uses `-c -xc` for its C probes.
3. Each scan iteration consumes one positional parameter with `shift /1`. Microsoft documents that SHIFT leaves `%*` unchanged. The invocation forwards `%*` once, so original order and quoting remain intact. Supplied compiler/sysroot/library paths remain quoted. Disabling delayed expansion preserves literal exclamation marks.
4. The link driver option precedes the untouched original arguments. No original option or diagnostic is removed. Explicit conflicting options retain their normal compiler behavior.
5. The pinned LLVM15.0.4 MinGW driver selects `libgcc` plus `libgcc_eh` for a non-shared C executable, or `libgcc_s` plus `libgcc` for the non-static C++ driver. `ShouldLinkCXXStdlib` excludes `-nostdlib++`. This changes runtime selection for object-only links without compiling C sources as C++ or adding a C++ standard library.
6. Direct byte inspection found the expected DLL name in `libgcc_s.a`. The installed DLL has a valid PE signature and AMD64 machine value0x8664. The frozen runner puts the same MinGW `bin` directory on its explicit PATH. No incompatible ABI/library replacement was introduced by this patch.
7. The command after clang is `exit /b %errorlevel%`, so the compiler status is propagated. There is no error suppression, fallback-to-success, download or machine PATH mutation.

## Findings not fixed / limits

- Source-input compile-and-link and response-file-only command forms retain the previous driver behavior. The observed Go command is neither form. A new observed failure in those forms needs its own evidence and reviewed change; this check does not broaden support silently.
- The upstream LLVM source may differ from Huawei's installed vendor build. Only actual compiler/link execution can validate that implementation.
- A shared GCC DLL can become a real output dependency. Future desktop package acceptance must inspect and satisfy the actual dependency. Presence in the host runner PATH is not packaging proof.
- The frozen runner binds the adapter and compiler executables, but its tool list is not a complete MinGW-library distribution manifest. The archive/DLL hashes above are read-only source-review observations, not a claim that all runtime inputs were exhaustively bound during an executed run.

These are explicit validation/provenance limits, not confirmed blockers in this source candidate. No compiler, adapter, Go SDK, native test, WSL, device or runtime script was executed or imported.

## Verification

- Static lint:PASS (ASCII, LF, final newline, no trailing whitespace, all GOTO targets resolve, expected guards/argument forwarding/exit propagation).
- TypeCheck:NOT APPLICABLE to this batch adapter. No batch interpreter was run.
- Tests/link/vet:UNRUN by grant restriction.
- Frozen runner and native source identities:PASS, unchanged.

## Primary source checks

Read source text only, without executing it:

- LLVM `llvmorg-15.0.4`, `clang/lib/Driver/ToolChains/MinGW.cpp`: `Linker::AddLibGCC` lines61–94 and C++ library guard at228.
- LLVM same tag, `clang/lib/Driver/ToolChain.cpp`: `ShouldLinkCXXStdlib` lines1001–1004.
- Microsoft Learn, Windows `shift` command:Remarks, `%*` behavior.

Ownership handed back to the main coordinator. No commit or fresh readiness request was made.
