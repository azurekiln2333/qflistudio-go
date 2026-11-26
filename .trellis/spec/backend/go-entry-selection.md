# Go Entry Selection

Execution policy: apply `AGENTS.md` and [Cloud-Only Execution](cloud-only-execution.md).
Run all development verification commands in GitHub-hosted Actions only. Descriptions
of user-facing Run/terminal behavior below do not authorize local agent execution.

## 1. Scope / Trigger

Read this contract when changing Go Run behavior, source selection, native source views or process cleanup. The shared editor already supplies the exact selected entry. The Go runner must not discard that filename by considering only its directory.

## 2. Signatures

    GoProgramRunner.run({required String projectPath, required String entryFile})
    GoToolchain.execute({required GoToolAction action,
                         required String projectPath, required String entryFile})
    char *QfliGoRun(unsigned long long id, char *projectPath, char *entryFile)

The public Dart and C signatures stay unchanged. The existing profile chooses official desktop SDK execution or the embedded mobile interpreter.

## 3. Contracts

- Tap Run resolves the configured project entry. Long press forwards the active file. The runner does not edit project metadata.
- Main and main2 may each declare a main function in the same source directory. Run only the selected entry while retaining standalone helper files.
- Exclude only competing receiver-free top-level main declarations from main-package files in the selected directory. Never filter imported subpackages or functions merely named main in comments, strings, runes, raw literals or method receivers.
- Desktop keeps package execution through go run . so Go owns module imports, build constraints, cgo, assembly and embedded assets.
- When another entry exists, write a per-run overlay JSON object whose Replace map contains absolute competing-source paths mapped to an empty string. Pass it through go run -overlay <file> .; never modify the source files themselves.
- Use dart:convert jsonEncode for the overlay. The lexer identifies declarations; it is not a full Go parser and must not replace compiler diagnostics.
- Include sibling symlinks to regular Go source files in entry discovery. Do not follow linked directories during enumeration.
- Decode lossily for declaration discovery only; never rewrite source bytes. The real compiler must still report encoding errors in retained files, while platform-excluded files remain excluded normally.
- Recovery after arbitrary broken Go syntax may differ between the small Dart lexer and go/parser. This is an accepted boundary; identifiable unfinished main bodies are handled, while selected-source and retained-helper diagnostics remain authoritative.
- The process exit future owns temporary overlay cleanup. Failed preparation/start also releases the owned directory. Cancellation still stops the process tree.
- Both desktop SDK paths consume the shared ProcessSupervisor. Subscribe to its
  broadcast stdout/stderr immediately and buffer through single-subscription
  controllers before any stdin-close await or UI handoff. Process exit must not
  wait for the UI to attach. Preserve complete output when the UI subscribes
  after a short command has exited.
- Shared supervisor checkpoint 9b0c01fe guarantees the documented owned Linux
  pidfd/procfs descendant path and Windows taskkill path. Its macOS, older-Linux
  and other-POSIX fallback owns only the parent; do not report descendant cleanup
  as proven there. Verify Run, terminal go run and terminal go test with a real
  nested child, inherited pipes and child-owned listener rather than parent exit
  alone. Shared implementation changes remain the core owner's responsibility.
- Native execution uses go/parser and a projectSourceFS.ReadDir view that hides competing entries only in the selected directory, then uses normal Yaegi package evaluation. Preserve the vendor patches and C ABI described in native-go-runtime.md.
- A helper selected as entry fails visibly. It never launches a sibling main as a fallback. Source errors must not be classified with the unavailable-runtime sentinel.
- Run titles are short go run <basename> labels and never contain the temporary overlay path. Other Go tool actions retain their package semantics.
- Compare the selected path using the host filesystem semantics; a Windows case-only spelling must not exclude the selected file itself. Keep Go test-file suffix checks case-sensitive: _TEST.go is not _test.go.
- A clearly identifiable non-selected top-level main may be excluded even when its body is malformed. Keep real diagnostics from the selected source and every retained helper; partial AST facts must never hide those errors.
- A source excluded by the backend build rules is not a successful selected-entry run. Verify against the interpreter/compiler build view instead of adding a separate build-tag parser.
- Yaegi permits helper-only packages to return success. After normal EvalPathWithContext, import the cached package under a local alias and resolve alias.main without invoking it. This checks the actual interpreter build view; init and main must still each execute exactly once. Quote import paths with fmt.Sprintf %q.
- Output-finalization defers must preserve errors produced before evaluation. Directory/source-read failures must retain their diagnostic rather than becoming an empty nonzero result.

## 4. Validation & Error Matrix

| Condition | Expected behavior |
| --- | --- |
| Selected main plus another main and helper | Only selected output; helper resolves |
| Ordinary one-main package | Original package command and behavior |
| Selected helper without main | Nonzero compile/entry error; no other main output |
| Selected malformed source | Real parser/compiler diagnostic |
| Missing SDK | Existing unavailable-runtime result |
| Wrong package / invalid helper | Preserve normal compiler/interpreter error |
| Ignored or platform-specific source | Existing backend build filtering applies |
| Overlay write/start failure | Error plus cleanup of only owned temporary data |
| Cancelled process | Process tree stopped, streams closed, overlay released |

## 5. Good / Base / Bad Cases

Good: main.go and main2.go both call message() from helper.go. Running main / main2 / main prints three distinct expected lines in that order.

Base: a normal main.go + helper.go module continues to run without an overlay.

Bad: replacing go run . with go run main2.go. Explicit file mode drops implicit helper files. Another bad pattern is dropping all package-main sources, which also drops helpers.

## 6. Tests Required

- Real SDK regression with both mains present, shared helper, local module import, embedded asset and a platform-excluded file.
- Assert selected output, concise title and unchanged source bytes/project metadata.
- Lexer cases cover comments, interpreted/raw/rune literals, receivers, nesting, package declarations and unusual whitespace.
- Actual syntax diagnostics and helper-as-entry rejection must be asserted, not just nonzero exit.
- Native tests cover both selected mains with helpers/subpackages; keep panic, cancellation and concurrent-output checks.
- Device integration checks the same main / main2 / main sequence through the FFI boundary.
- Rebuild all bundled Android/OHOS libraries after native source changes; source tests do not update installed binaries.

## 7. Wrong vs Correct

Wrong:

    go run main2.go

Correct for a multi-entry project:

    go run -overlay <owned temporary JSON> .

The temporary Replace map hides main.go while the compiler still discovers helper.go, imports and assets normally. On mobile, apply the equivalent selected-directory filtering through the source filesystem instead of a new vendored interpreter API.
