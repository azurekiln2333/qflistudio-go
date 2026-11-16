# First GitHub run

- Commit: 0cb91fd.
- Run: https://github.com/azurekiln2333/qflistudio-go/actions/runs/43938724578
- Hosted Linux source test job reached Go 1.27.1 and failed in existing debugger
  tests. Native runtime source was not modified by this CI task.
- `TestDebugOpaqueCallbackCreatedByMainCalledByWorker` reported a missing opaque
  callback identity/boundary at `debugger_test.go:574`.
- `TestDebugRetainedNativeArgumentAfterRegistrarExit/returns` panicked while
  `Debugger.SetBreakpoints` visited a node without a type. Stack includes
  `interp/type.go:2477`, `interp/op.go:608`, `interp/debugger.go:645`, and
  `native_callback_provenance_test.go:100`.
- These are actual test failures, not missing SDKs or a syntax-only result.
- Platform builds were initially skipped because source checks were a success
  prerequisite. Keep the source checks red and allow the requested experimental
  platform builds to proceed independently; record the source-check result in
  artifact manifests and summaries. Do not use `continue-on-error` or drop tests.
- Separate Go test, Go vet and artifact regression steps so test failure cannot
  hide the other check results. This task does not expand into interpreter fixes.

## License follow-up

The user requested GPL v3.0 notices matching `D:/MyNewProjects/qflistudio`.
The existing root LICENSE is already byte-identical to the main project's file
(SHA-256 3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986).
Three README translations now state the project license and preserve separately
declared licenses. Commit b324c92 was pushed to the GitHub feature branch.
