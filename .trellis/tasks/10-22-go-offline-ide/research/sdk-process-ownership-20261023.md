# SDK process ownership repair

Date: 2026-10-23, Asia/Shanghai. Product-only implementation; shared core remains
owned by C. This note does not claim a test or device pass.

## Change boundary

The existing Unix cancellation kills only the `go` parent, while `go run` and
`go test` create child executables which can retain stdout/stderr. The behavior
lives in both SDK launch paths in `lib/go_runner.dart`, including terminal
commands. Both now consume the existing shared `ProcessSupervisor` and delegate
cancellation to its `ManagedProcess`. No second process-tree implementation is
added to Go. Only this runner, its focused tests and local specs/evidence change.

The reviewed shared source SHA256 is
`25ba430ce7c0a6e2740c506ce6b0319eeecd31c90a3dc20b53a005861d8f54a1`.
It captures identity-backed Linux descendant trees and retains Windows tree
cancellation. Its macOS branch still signals only the parent. Global channel
seq225 requests the shared owner's macOS plan/checkpoint; this integration alone
cannot close macOS process-tree acceptance.

## Output lifetime

`ManagedProcess` forwards already-drained pipes using broadcast streams. Go's
terminal launch awaits stdin closure before returning its result. A short SDK
command can finish during that await or before a UI listener mounts.
`_GoSdkProcess` subscribes to both managed pipes synchronously after start and
buffers them in single-subscription controllers until their actual consumers
subscribe. Its onDone closes the buffered streams without making process exit
depend on UI attachment. Existing exit-code-driven overlay cleanup is retained.

## Meaningful regressions

- Run and raw terminal `go run` emit Unicode stdout and stderr, finish, and only
  then obtain UI stream subscriptions. Both complete lines must survive.
- Run, terminal `go run` and terminal `go test` create a nested child executable
  which ignores TERM/INT, owns a private loopback listener and inherits pipes.
  Two concurrent cancellation calls must complete, the exit must be nonzero,
  both pipes must close and the child's listener must be gone. A private `stop`
  command releases only this fixture's child if the regression fails.
- The earlier selected-entry cancellation/overlay test remains intact.

The Windows SDK can exercise the actual shared tree path. Real Linux and macOS
runs remain distinct requirements. Do not report a platform pass from a mock or
from the other platform's successful process cancellation.

## Verification status

`dart format` and focused `git diff --check` passed. In the explicitly granted
Go236 host window, the real pinned Windows SDK passed both new regressions:

- Delayed stdout/stderr subscription: 1/1 passed, handle21711 exit0, log
  `sdk-late-output-20261023.log`.
- Nested-child cancellation through Run, terminal run and terminal test: 1/1
  passed, final handle70405/shellPID64664 exit0, log
  `sdk-nested-cancel-20261023.log`.
- Scoped analysis of runner, SDK test and catalog integration audit: no issues
  (1.8s), same final handle, `sdk-audit-scoped-analyze-20261023.log`.

The complete SDK suite was not run in this bounded window. Neither Windows
regression establishes Linux/macOS cleanup. Shared C232 explicitly retains a
parent-only fallback on macOS/other POSIX/older Linux.

The separate native focused handle85731 exited1: compile succeeded but local
dependency debugger initialization and three Helper method forms failed. Its
log is `native-review-repair-focused-20261023.log`; source repairs continue.
No native library rebuild, device action, global process termination or
shared-core edit was performed. Go236 was explicitly released at global seq287
to Rust205 then C211; no new heavy command may start before a later grant.
