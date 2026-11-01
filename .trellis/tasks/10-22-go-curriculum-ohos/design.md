# Go content design

Read the parent's `design.md` learning-content execution contract and baseline inventory. Authoring source remains in `tool/go_curriculum/topics` and `samples`; aggregate output must be reproducible and UI-displayed code must match executed bytes.

Implement an exhaustive corpus manifest covering tutorial/example code separately, support files, stdin/fixtures, expected exit/output and operation kind (program/test/module). A test-package snippet cannot pass merely because a different host fixture compiled. The product must import the runnable shape shown to the learner. Use bounded per-item execution and separate compiler, shipped host-native and actual OHOS reports.

Repair Yaegi defects where preserving a language concept requires them; maintain focused regressions in `native/go_runtime`. Content rewrites must retain the taught behavior. Preserve original topic IDs and distinguish historical failures from fresh reports.

Stage the new 160-topic map for independent substantive review before authoring. Group by practical standard-library tasks and programs with distinct behavior. Run AST/text duplication checks and manual topic review. Shared asset changes are one digest-checked Go-slice application by the core integrator, with backup and rollback support.

The acceptance artifact records exact source, catalog and bundled library hashes. Missing real OHOS execution leaves the child incomplete regardless of all-green host reports.
