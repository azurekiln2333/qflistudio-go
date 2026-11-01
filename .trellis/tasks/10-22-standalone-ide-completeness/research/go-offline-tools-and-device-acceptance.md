# Go offline tools, IDE panel semantics and real OHOS acceptance

Research pane deliverable for `.trellis/tasks/10-22-standalone-ide-completeness` (child: `10-22-go-offline-ide`).
Planning-only. **No product, shared-core or spec file was modified by this pane.** Every claim below is
either a quoted official source (URL) or a command I ran in this session (command + observed output).

Fetched-page digests: `research/go-tools-source-fetch.json` (same hash-only convention the parent adopted;
raw HTML not retained in the task tree).

---

## 1. Current measurable state of this product (ran now, host only)

| Check | Command | Result |
| --- | --- | --- |
| Dart analysis | `flutter analyze --no-pub` | `No issues found! (ran in 25.3s)` |
| Dart/Flutter suite | `QFLI_GO_TEST_EXECUTABLE=<pinned sdk> flutter test --no-pub --concurrency 1` | `+111: All tests passed!` |
| Native runtime unit tests | `CGO_ENABLED=0 GOTOOLCHAIN=local go test -mod=vendor -count=1 ./...` in `native/go_runtime` (pinned `native/build/go-sdk-1.27.1/go/bin/go.exe`) | `ok qfli_go/native/go_runtime 1.578s` (28 `runGo` tests) |
| Official-Go curriculum | `research/baseline-official-go.log` (recorded earlier today) | `VERIFY: 120 passed, 0 failed` |
| Flutter toolchain | `flutter --version` | `Flutter 3.27.5-ohos-1.0.1`, `flutter build` lists `hap/app/har/hsp` |
| Connected targets | `hdc list targets` | `[Empty]` |
| Device list seen by Flutter | `flutter devices` | Windows + Chrome + Edge only; **no OHOS device** |
| Existing OHOS package | `build/ohos/hap/entry-default-signed.hap` | 59,019,010 B (build artifact, not execution proof) |

### Packaged native runtime is a hard gate for any new native export

`native/go_runtime/bridge.go` exports exactly three symbols and the shipped libraries match:

```
llvm-nm --dynamic --defined-only ohos/entry/libs/arm64-v8a/libqfli_go_runtime.so
  T QfliGoRun
  T QfliGoCancel
  T QfliGoFree
```

| Artifact | Size | mtime | sha256 |
| --- | --- | --- | --- |
| `ohos/entry/libs/arm64-v8a/libqfli_go_runtime.so` | 21,184,976 | 2026-10-15 19:21:09 | `abd6988a0f18fedbab2cef9e790771a114174bd54b06d023086963c99b149b3c` |
| `ohos/entry/libs/x86_64/libqfli_go_runtime.so` | 22,785,072 | 2026-10-15 19:21:55 | `2c1750f6a1071aa89e8cdb0338725ba9a6c78fb632ee56aec3c046eac0bb1b39` |
| `android/app/src/main/jniLibs/arm64-v8a/…so` | 21,127,696 | 2026-10-15 19:19:31 | — |
| `android/app/src/main/jniLibs/armeabi-v7a/…so` | 21,285,396 | 2026-10-15 19:20:11 | — |
| `android/app/src/main/jniLibs/x86_64/…so` | 22,716,208 | 2026-10-15 19:20:52 | — |

Consequence: any `QfliGoAnalyze*`/`QfliGoFormat*`/`QfliGoDebug*` export is **absent from the packaged app**
until `tool/build_go_runtime.ps1` is re-run (OHOS arm64 + x86_64, Android 3 ABIs, iOS archive) and the new
`.so` hashes are recorded. Mobile diagnostics/debugger cannot be claimed from Dart-only work.

### Concurrent shared-core ownership (observed live, do not edit)

`D:/MyNewProjects/qfli_studio_core` is dirty and *changing while I read it* (C coordinator `w1R:p1`,
tasks `10-22-offline-content-explorer`, `10-22-offline-editor-analysis`). It now carries the shared contract
the Go adapter must implement (untracked, brand new):

- `lib/services/code_analysis.dart` — `CodeAnalyzer.analyze(CodeAnalysisRequest)`, `CodeDocumentSnapshot`
  (`path`, `text`, `revision`), `CodeAnalysisRequest` (`projectPath`, `activeFilePath`, `language`,
  `revision`, `documents` overlay), `CodeDiagnosticSeverity {error,warning,information,hint}`,
  `CodeDiagnostic` (`filePath`, `startOffset`, `endOffset`, **UTF-16 code units, half-open, zero-based**,
  `message`, `severity`, `source`, `code`), `CodeAnalysisResult(diagnostics, unavailableReason)`.
- `lib/services/studio_profile.dart` — new optional constructor field `this.codeAnalyzer` +
  `export 'code_analysis.dart';`.
- `lib/widgets/language_badge.dart` (`LanguageBadge`, `languageKey`, `languageLabel`, C vs C++),
  `lib/editor/file_explorer.dart` now calls `_restoreExpanded()` from `_rebuildRoot()` (initState path).

So Go must *consume* `StudioProfile(codeAnalyzer: …)` and must not re-create or patch these files.

---

## 2. Official sources → concrete applicable contract

### 2.1 Go standard library (all compile into the existing native module; no network)

| URL | Contract that actually binds our implementation |
| --- | --- |
| https://pkg.go.dev/go/parser | `ParseFile(fset, filename, src, mode)` takes `string`/`[]byte`/`io.Reader`; with `SkipObjectResolution` (documented as *recommended*) `File.Scope`, `File.Unresolved`, `Ident.Obj` are nil. On syntax errors the result is a **partial AST** with `ast.Bad*` nodes and a `scanner.ErrorList` **sorted by source position**; `AllErrors = SpuriousErrors` reports "all errors (not just the first 10 on different lines)". |
| https://pkg.go.dev/go/token | `Position{Filename, Offset, Line, Column}` — **column is a byte count**, line/column start at 1. `FileSet.Position/Offset` map between `Pos` and byte offsets. This is the exact conversion hazard against Dart's UTF-16 offsets. |
| https://pkg.go.dev/go/format | `Source(src []byte) ([]byte, error)`; `Node(dst, fset, node)` formats in canonical gofmt style and does **not** modify the node; imports are not sorted for partial-file nodes. Docs explicitly warn that formatting changes over time and tools wanting stability "should execute a specific version of the gofmt binary", so our formatter result must be labelled with the runtime/Go version that produced it. |
| https://pkg.go.dev/go/ast | `Inspect(node, f)` / `Walk` (depth-first), `Fprint` — enough for outline/symbol extraction without type info. |
| https://pkg.go.dev/go/types | `Config.Error func(error)` collects **all** errors (nil ⇒ stop at first); `Error.Fset/Pos/Msg/Soft`; `Check(path, fset, files, info)`. An `Importer` is required for imports — "error if an importer is needed but none was installed". |
| https://pkg.go.dev/go/importer | `Default()` imports for "the compiler that built the running binary" — i.e. it reads installed export data. On a device with no GOROOT there is no such data. |
| https://pkg.go.dev/go/build | `Context.ImportDir(dir, mode)`, `Import(path, srcDir, mode)`; needs GOROOT/GOPATH-style roots. |
| https://pkg.go.dev/cmd/test2json | `test2json [-p pkg] [-t] [command]`; event struct `{Action, Package, Test, Elapsed, Output, FailedBuild}`; `Action ∈ start/run/pause/cont/pass/bench/fail/output/skip`. This is the sanctioned way to turn `go test` output into structured rows for the Test/Output panel. |
| https://go.dev/ref/mod | Module graph/version semantics for `go list -m -json` style inspection (desktop only). |
| https://pkg.go.dev/cmd/gofmt , https://pkg.go.dev/cmd/vet | Desktop `gofmt`/`go vet` remain real SDK operations; nothing about them exists in Yaegi. |
| https://pkg.go.dev/cmd/doc | Package/symbol documentation extraction for a local "Go doc" tool. |
| https://pkg.go.dev/net | `net.Listen`/`Listener.Addr()` — in-process, offline listener introspection is possible without reading `/proc`. |
| https://pkg.go.dev/github.com/traefik/yaegi/interp | `Debugger` methods `Continue(id)`, `Step(id, reason)`, `Interrupt(id, reason)`, `Terminate()`, `Wait()`, `GoRoutines()`, `SetBreakpoints(target, requests…)`; `DebugOptions`, `DebugEvent`, `DebugFrame`, `DebugFrameScope`, `DebugVariable`, `Breakpoint`. |

### 2.2 VS Code (panel/workspace/debug semantics we should mirror, not invent)

| URL | Semantics worth copying |
| --- | --- |
| https://code.visualstudio.com/docs/getstarted/userinterface | The **Panel** is "an additional space for views below the editor region. By default, it contains output, debug information, errors and warnings, and an integrated terminal." One panel region, several views — exactly the requested Problems/Output/Debug Console/Terminal/Ports selector. |
| https://code.visualstudio.com/docs/languages/go.md | gopls "detects build and vet errors… shown red/green squiggly lines in the editor. These diagnostics also show up in the **Problems** panel". Formatting is a separate explicit capability; test runs are separate commands. Confirms: diagnostics ≠ execution. |
| https://code.visualstudio.com/docs/debugtest/debugging.md | Debug Console "view debugger output and **evaluate expressions**"; logpoints write to the Debug Console without pausing; state is inspected in Run and Debug **when execution pauses**. So Debug Console requires a paused session to be honest. |
| https://code.visualstudio.com/docs/debugtest/tasks.md | "Problem matchers scan the task output text for known warning or error strings, and report these inline in the editor and in the Problems panel"; task fields `label`, `type`, `command`, `group`, `dependsOn`, `dependsOrder`, `isBackground`, `problemMatcher`. Useful pattern for turning a real Go tool's stderr into diagnostics **with the tool's own text** instead of a second parser. |
| https://code.visualstudio.com/docs/remote/ssh.md , https://code.visualstudio.com/docs/devcontainers/containers.md | The **Ports view** lives "in the bottom panel", has an **Add Port** action, and can restore forwarded ports (`remote.restoreForwardedPorts`). Forwarding/publishing is explicitly the remote case — **out of our offline scope**; only a local, read-only listener list is in scope. |
| https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces.md , https://code.visualstudio.com/docs/terminal/basics.md | Workspace = ordered folder list + per-folder settings; terminal/panel state survives restart. Terminal output feeds error detection (links/problem matchers). |

### 2.3 JetBrains (inspection interaction model)

| URL | Semantics |
| --- | --- |
| https://www.jetbrains.com/help/go/code-inspection.html | Every inspection has a **severity level** with distinct editor highlighting, grouped into **profiles** (enabled inspections + scope + severity); Problems tool window hosts results; quick-fixes are attached to a problem; one action can "open the Data Flow Analysis tab in the **Problems tool window**". |
| https://www.jetbrains.com/help/clion/code-inspection.html | Same severity/scope model for the C/C++ product (cross-product consistency argument). |
| https://www.jetbrains.com/go/features/ | "**Code → Go Tools** menu allows you to run Go tools on your project without switching to the command line"; "The built-in **formatter** provides the functionality equal to `go fmt`"; debugger offers Watches/Evaluate/Inline Values. This is the reference for a **flat** Go tool list (no second-level "dedicated feature" pages). |

---

## 3. Empirical probes that decide the analyzer design (run in this session)

I copied the vendored Yaegi (`native/go_runtime/vendor/github.com/traefik/yaegi`, v0.16.2-0.20260209085605)
into a throwaway module under `%TEMP%\yaegi_probe` and drove it with the pinned Go 1.27.1 SDK. Marker files
(`os.WriteFile`) prove whether user code actually executed. **No repository file was touched.**

| Probe | Result | Meaning |
| --- | --- | --- |
| `interp.Compile(src)` — single file, top-level `var x = "type-error"` assigned to `int` | `cannot convert "type-error" to int`; **no marker created** | Yaegi's single-file compile performs a real type check and does **not** run package initializers or `main`. |
| `interp.Compile(clean)` then `Execute` | compile: no marker; execute: marker created | Initializers run only at `Execute`. |
| `interp.CompilePath(dir)` using the **shipped `projectSourceFS`-style mapping** (`src/qfli-project` → project root), program with `main` writing a marker and importing a source subpackage whose `var X = touch()` writes another marker | **both markers created during `CompilePath`**, program stdout `value 7` printed before `Execute` | The directory/import path used by the shipped `runGo` **executes the program while compiling**. Yaegi is therefore *not* a safe analyzer at directory scope. |
| `go/parser.ParseFile` with `AllErrors\|ParseComments\|SkipObjectResolution` on a broken file | `bad.go:4:3: expected ';', found 'EOF' (and 1 more errors)`, `ErrorList.Len() == 2` | Pure-syntax diagnostics with byte positions, zero execution risk. |
| `go/format.Source` on messy source | err `nil`; output canonical gofmt form | Real formatter, no execution. |

Not resolved by these probes (must be an explicit test, not an assumption): whether a **single-file**
`Compile` can be made to touch source-imported packages (probe 1's import failed with
`package location . not in GOPATH`, so it proved nothing about source imports), and whether any Yaegi path
can be made init-free for multi-file projects. Treat "Yaegi as type checker" as **unproven** until a
marker-based regression passes for the exact shipped FS.

### Derived analysis contract (three honest capability tiers)

1. **Always available (desktop + OHOS/Android/iOS, no SDK): syntax diagnostics.**
   `go/parser` + `parser.AllErrors` + `SkipObjectResolution` on the unsaved buffer text passed from Dart;
   map `scanner.ErrorList` entries through `token.File.ColumnInfo`-free byte arithmetic to UTF-16 offsets.
   This never executes code, never reads the disk beyond the snapshot, never uses the network.
2. **Import-free type diagnostics (optional, same native library).** `go/parser` → `go/types.Config{Error: …}`
   with an importer that only knows predeclared/`unsafe` (or a tiny allow-list), for files whose imports are
   empty; any file with imports returns `CodeAnalysisResult(unavailableReason: …)` — matching the shared
   "unavailable must explain why" rule. `importer.Default()` is unusable on device (no GOROOT export data),
   so do not promise stdlib type checking.
3. **Desktop (`official-go-sdk`) full diagnostics.** `go vet` / `go build` output parsed into the same
   `CodeDiagnostic` type with real file/line/column, capability-gated on `GoRuntimeBackend.officialSdk`.

**Forbidden:** calling `runGo` (or `CompilePath`) to "check" syntax — probe 3 shows it *runs* user code.

### UTF-8 → UTF-16 mapping (required for the shared contract)

`CodeDiagnostic` offsets are UTF-16 code units; `token.Position.Column` and `parser` error columns are
**bytes**. Required algorithm, with a regression test in the native suite:

- Build one byte→UTF-16 offset table per analyzed file from the snapshot text: iterate the UTF-8 bytes,
  add `1` to the UTF-16 counter for ASCII/BMP (2–3 byte sequences) and `2` for 4-byte sequences
  (astral runes / emoji), 0 for combining marks is *not* special-cased (they are separate code points).
- CRLF counts as **two** UTF-16 units (the shared doc comment says so explicitly); a lone `\n` counts as one.
- Diagnostic end offset: `start + utf16Len(message-token)` or the error token length; never exceed the
  document length, and clamp instead of throwing (stale revision rejection happens in the shared owner's layer).

---

## 4. Debugger contract (real Yaegi, not a UI toggle)

Feasible pieces (vendored source, not speculation):

- `native/go_runtime/vendor/.../interp/debugger.go`:
  `interp.Debug(ctx, prog, events func(*DebugEvent), opts *DebugOptions) *Debugger`,
  `dbg.SetBreakpoints(PathBreakpointTarget(path), LineBreakpoint(n), FunctionBreakpoint(name)) []Breakpoint`,
  `dbg.Continue(id)`, `dbg.Step(id, reason)` (stepInto/stepOver/stepOut via `DebugEventReason`),
  `dbg.Interrupt(id, reason) bool`, `dbg.Terminate()`, `dbg.Wait()`, `dbg.GoRoutines()`,
  `evt.Frames(start,end) []*DebugFrame` → `Frame.Name()`, `Frame.Position() token.Position`,
  `Frame.Scopes()` → `Scope.Variables() []*DebugVariable`.
- Because `CompilePath`/`importSrc` already runs the program (probe 3), the debugger **must own the run**:
  build the program, attach `Debug`, then let the debugger drive `Wait()`; a separate "analyze then debug"
  flow would double-execute user code.
- Session model required for FFI: ID-owned registry (like `runs` in `bridge.go`), bounded event polling from
  Dart (`Isolate.run` per poll or a `NativePort`), deterministic `Terminate`/free on widget dispose,
  one active debug session per project root, and hard caps on retained events/log lines.
- Honest gating: on desktop the truthful statement is "embedded interpreter debugger available"; there is no
  `dlv` offline. Controls must be disabled (with a reason) when a session is not paused.

---

## 5. Direct Go tools: flat Tools-page list with real behaviour

Per VS Code Go docs + GoLand "Code → Go Tools", the useful **Go-specific** cards (first-level, no detours):

| Card | Desktop (`official-go-sdk`) | Mobile (`embedded-go-runtime`) |
| --- | --- | --- |
| 格式化（gofmt） | `gofmt`/`go fmt ./...` real process | native `format.Source` via new FFI export (needs `.so` rebuild) |
| 语法检查 | `go vet` (+ parser) | `go/parser` only; type check only for import-free files |
| 运行 / 构建 / 测试 | `go run/build/test` (exists today via `GoToolchain`) | `go run` only (exists today); `build/test` must stay refused |
| 测试结果表 | `go test -json` (test2json event stream) | unavailable |
| 包/符号大纲 | `go doc` / `go/ast` outline | `go/ast` outline (native) |
| 模块信息 | `go list -m -json`, `go mod graph` (read-only) | unavailable (no module cache) |
| 导入检查 | parse imports + `go/build` resolution | parse-only "unused/missing from this package" hints |
| 端口/监听器 | in-process `net` listener registry | same (no `/proc` parsing) |
| 调试 | Yaegi debugger session | Yaegi debugger session |
| 静态数据工具（JSON/YAML 互转、格式化 JSON 常量、`go:embed` 视图） | real | real |

Rule from PRD/design: capability comes from `goRuntimeBackendFor(...)`; every unsupported card must return a
typed error string, never an empty success, and must reuse `kProgramNotRunExitCode` (127) for "did not run".

---

## 6. Real device acceptance (what will and will not count)

Confirmed toolchain facts (official SIG README, sha256 `4edc0dd9…`): build output is
`<project>/ohos/entry/build/default/outputs/default/entry-default-signed.hap`; install via
`hdc -t <deviceId> install <hap>` or `flutter run --debug -d <deviceId>`; `flutter devices` must list the
target first. Official `hdc` doc: `hdc list targets` lists connected devices, `hdc shell`, `hdc file send/recv`,
`hdc hilog`, `hdc jpid`.

Acceptance checklist (each step must be recorded with the literal command and output):

1. **Gate 0 — target exists.** `hdc list targets` returns a non-`[Empty]` id **and** `flutter devices` lists it.
   Today: `[Empty]` and no OHOS device ⇒ device acceptance is **open**, not "passed by build".
2. **Gate 1 — packaged identity.** Record `sha256` of the HAP, of each `ohos/entry/libs/<abi>/libqfli_go_runtime.so`
   in the HAP, and of the shipped catalog assets
   (`assets/content/examples.json`, `tutorials.json` inside `flutter_assets/packages/qfli_studio_core/`).
   `unzip -l`/`llvm-nm` on the HAP are build-time checks, **not** execution.
3. **Gate 2 — install & launch.** `hdc -t <id> install <hap>` then launch (bundle from
   `ohos/AppScope/app.json5`) and confirm a non-crashing first frame (`hdc shell hilog`, `hdc jpid`).
   A successful HAP assembly or `flutter build hap` alone proves nothing.
4. **Gate 3 — real per-item execution on device.** The existing device harness
   (`integration_test/go_native_test.dart`, 6 cases) proves the FFI path, panics, cancellation and the
   terminal delegate, but not the 240 catalog blocks. Required addition: an integration test that reads the
   **bundled asset catalog** (not repo files), extracts every tutorial/example code block, runs it through the
   real `GoProgramRunner` (and the same project shapes as `tool/go_curriculum` — 87 single-file, 15 module,
   18 test packages), asserts declared stdout/exit, and writes a JSON report with the runtime/content hashes
   out of the app sandbox via `hdc file recv`, or emits it as structured `hilog` lines.
5. **Gate 4 — no unexplained omissions.** Every inventory id appears in the report with `pass|fail|unsupported`
   plus stderr. Filtering failures, or relabelling them "desktop" to fit, invalidates the run.
6. **Gate 5 — depth of evidence.** `mobile` label requires gate 3–5 output from the *actual packaged* runtime.
   Host-native (`tool/go_curriculum/mobile_check/native_hostcheck_test.go` via `go test -overlay`, real
   `runGo`) is the strongest non-device evidence and stays labelled host-only; bare Yaegi and official-SDK
   compile are weaker still. (`mobile_check/README.md` already encodes this ladder — keep that wording.)
7. **New exports add a gate:** if analysis/format/debugger go native, gate 1 must show the new symbols in the
   HAP's `.so` (`llvm-nm`) before any device claim.

Do **not** touch signing, keystores, credentials or a real device without an owner decision; nothing in
this report requires them.

---

## 7. Open items handed back to the parent/child tasks

1. Shared owner must finish/publish `code_analysis.dart` + `StudioProfile.codeAnalyzer` (in flight now) before
   the Go adapter can be wired; Go must not edit those files.
2. Decide whether "type diagnostics" ship at all on device, or only syntax + (desktop) `go vet`. Probe 3 rules
   out Yaegi directory compilation; single-file Yaegi compile is promising but unproven for source imports.
3. New FFI exports ⇒ rebuild OHOS arm64/x86_64 + Android 3 ABIs + iOS archive; update
   `lib/native_go_bridge_ffi.dart`, `libqfli_go_runtime.h`, `bridge.go` together, with a native test per export.
4. Debugger work needs an ID-owned session registry, bounded event buffers, and a test proving a breakpoint
   stops *before* a marker side effect and that `Terminate` releases the session.
5. Device acceptance stays open until a target appears; meanwhile the honest, useful work is the host-side
   analyzer/formatter/native tests and the exhaustive inventory driver described in gate 3.
