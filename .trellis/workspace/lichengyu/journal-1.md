# Journal - lichengyu (Part 1)

> AI development session journal
> Started: 2026-09-30

---



## Session 1: Bundle and verify mobile Go runtime
<!-- trellis-session: v=2 fp=d42ecac0cc820520 -->

**Date**: 2026-09-30
**Task**: Bundle and verify mobile Go runtime
**Branch**: `main`

### Summary

Bundled a patched Yaegi FFI runtime for Android and OpenHarmony; verified OHOS x86_64 execution and restored the normal signed application.

### Main Changes

- Added synchronized output, context cancellation, and recovery for main/worker panics.
- Pinned and built the community OHOS Go compiler to fix dynamic TLS loading.

### Git Commits

| Hash | Message |
|------|---------|
| `5d59143` | feat(go): bundle cancellable mobile runtime |

### Testing

- [OK] OHOS x86_64: three device integration tests passed; normal signed HAP installed and launched.
- [OK] Flutter analyze passed; all 14 tests passed with official Go SDK integration enabled.
- [OK] Final Android APK built with three runtime ABIs; 16 KB zip alignment passed.

### Status

[OK] **Completed**

### Next Steps

- Implement the remaining official mobile SDK commands: build, test, vet, formatting, and module management.
- Verify runtime execution on Android and OHOS arm64 devices.


## Session 2: Simplify learning lists and import detail code
<!-- trellis-session: v=2 fp=d2a590ca41e65c54 -->

**Date**: 2026-10-01
**Task**: Simplify learning lists and import detail code
**Branch**: `main`

### Summary

Completed MD3 tutorial/example lists and code import with custom filenames, project registration, and automatic project/file opening.

### Main Changes

- Added shared detail code actions, confirmed replacement, custom Go entries, and restored editor selection and explorer root.
- Recorded the content import contract and completed the task review; commits and archive are deferred.

### Git Commits

(No commits - planning session)

### Testing

- [OK] All 17 focused import tests passed; application/shared regressions passed 32 tests with 1 official Go SDK test skipped because go version is unavailable.
- [OK] Flutter analysis and targeted shared analysis passed without issues; 24 phone, desktop, dark, and large-text screenshots passed pixel checks and visual inspection.

### Status

[OK] **Completed**


## Session 3: Keep native startup progress until the Flutter home frame
<!-- trellis-session: v=2 fp=7e800bee75894e71 -->

**Date**: 2026-10-01
**Task**: Keep native startup progress until the Flutter home frame
**Branch**: `main`

### Summary

Ported qflistudio OHOS startup progress and deferred the Go app first frame until bootstrap and home layout complete.

### Main Changes

- Added native splash builder and validated startupProgress event bridge; documented the native startup contract.

### Git Commits

(No commits - planning session)

### Testing

- [OK] Three startup regression tests and 11 existing Go application tests passed; Flutter analysis and scoped diff checks passed.
- [OK] Signed arm64 debug HAP built after retrying PackageHap with temporary JVM heap limits to resolve Windows errno=1455.

### Status

[OK] **Completed**

### Next Steps

- Confirm the visible cold-start transition on a connected HarmonyOS device; hdc reported no connected targets.


## Session 4: Complete Go native platform integration and validation
<!-- trellis-session: v=2 fp=8c6a5ca0ac28fd01 -->

**Date**: 2026-10-02
**Task**: Complete Go native platform integration and validation
**Branch**: `main`

### Summary

Added iOS c-archive/Xcode integration and shared backend metadata; verified Windows SDK, Android FFI and Linux backend/source behavior, with unavailable Apple/GUI/OHOS execution recorded.

### Main Changes

- Added shared Go platform mapping and iOS process-symbol loading; configured Xcode archive build, retained exports and LF shell checkout.
- Recorded platform evidence and fixed two content-regression waits on fake-clock registry writes while preserving shared-core production code.

### Git Commits

(No commits - planning session)

### Testing

- [OK] All 38 Flutter application tests passed with the official Windows SDK enabled; Flutter analysis passed without issues.
- [OK] All 3 Android FFI cases passed; APK includes three native ABIs with 16 KB ELF alignment.
- [OK] Windows SDK actions/errors/cancellation passed; Windows and Linux native modules each passed 8 top-level tests and vet.
- [OK] Linux official SDK command checks passed in qfli-java-build WSL; Apple build/runtime and desktop GUI checks were skipped where tools were unavailable.

### Status

[OK] **Completed**

### Next Steps

- On a Mac with Xcode, build iOS and run the existing native FFI integration test; confirm cold-start visuals when a HarmonyOS device is connected.


## Session 5: Go release integrity audit and Android 16KB integration
<!-- trellis-session: v=2 fp=7ab81d1d814af51b -->

**Date**: 2026-10-15
**Task**: Go release integrity audit and Android 16KB integration
**Branch**: `fix/go-release-integrity`

### Summary

Completed scoped Go terminal/runtime, offline-policy and 120-topic curriculum audit; committed changes and archived linked product tasks with explicit release blockers.

### Main Changes

- Both terminal surfaces use real Go delegates; selected-entry and modern build constraints verified; shared-core offline guards and exact imports integrated without sibling workspace edits.
- Replaced Go placeholders with120 substantive tutorials/examples, preserved non-Go content; rebuilt five native runtime ABIs and retained current APK/unsigned HAP.

### Git Commits

| Hash | Message |
|------|---------|
| `775c207` | fix(ohos): complete native startup and remove unused account bridge |
| `96df3ad` | feat(go): add 120 verified tutorials and curriculum tooling |
| `4ace2f4` | fix(go): honor selected entries and modern build constraints |
| `df2f46d` | fix(go): route both terminals through the Go toolchain |
| `2b2fef6` | test(go): cover offline entry points and exact code imports |
| `7502c08` | style(go): apply canonical Dart formatting |
| `6b1373d` | docs(trellis): record Android integration and final release gates |

### Testing

- [OK] Flutter analyze clean; Go Flutter111 passed; curriculum120 passed; selected real race4 passed; shared terminal/offline/layout99 and import75 passed; native go test/vet clean.
- [OK] Android API37 x86_64 emulator with16384-byte pages: five real FFI/terminal integration cases passed, driver exit0; normal release installed/cold-launched, five product pages and terminal refusal inspected, normal app restored/stopped.

### Status

[OK] **Completed**

### Next Steps

- Before store submission supply Android production signing and matching Go OHOS key/certificate/profile, then run current signed OHOS and Android arm64 physical-device gates. Do not substitute historical results.
- Rust accepted temporary emulator5580/privateADB5039 ownership and cleanup via global channel seq49; no further Go device actions.
