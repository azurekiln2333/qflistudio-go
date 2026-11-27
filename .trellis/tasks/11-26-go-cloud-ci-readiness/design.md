# Design

Role scope: w5V source pane assignments below apply only before verified Herdr
handoff. After that handoff, target Codex assigns its own workers and Git executor;
source pane IDs do not govern target work. Model recovery follows AGENTS.md.

Assign native/go_runtime and regression tests to one Pi worker; assign .github/workflows, tool/ci and installer definitions to another; assign portable Trellis/instructions to a third. Only assigned Pi workers implement, execute Git operations and dispatch GitHub runs. Coordinator w5V:p1 assigns disjoint ownership, reviews integration evidence and starts eligible tasks without implementing. Workers report only to w5V:p1 through Herdr, never to w5V:p6. Prefer gpt-6.1-sol; on model limits use bounded retries, then compaction/new sessions, then deepseek-v4.1-flash only as the final fallback after those recovery options fail. Read native-go-runtime and relevant frontend specs before code edits. The assigned signing/CI Pi owner must sanitize OHOS password literals and machine signing paths before the preservation checkpoint or any new publication; the portable Trellis worker does not edit signing/product files.

Fix TestDebugOpaqueCallbackCreatedByMainCalledByWorker and the nil-type panic during breakpoint inspection based on hosted failure logs. Preserve real failure status and existing debugger safety invariants. Add Go/helper/Flutter cloud checks, including a newly built Linux library for native-dependent Flutter tests. Do not count skips as exercised coverage.

Connect native and app jobs with reusable workflows or explicit same-run dependencies. Consumers verify source SHA, ABI set, exports and digests. Build Windows/Linux native artifacts using the same flags as their app integration. Cache SDK/toolchain inputs only in GitHub with bounded retention.

Use Setup EXE, DEB and DMG as initial desktop installer formats. Keep existing portable bundles. Mobile jobs produce APK/IPA/HAP. Signing uses validated GitHub secrets/environment inputs and records mode/provenance. Missing credentials fail signed mode. Ordinary push checks upload artifacts; release publication is deliberate. No private keys enter source, logs or artifact packages.

AGENTS.md is the common rule entry point. Reconcile Pi/Trellis and README instructions. All tests, lint, dependency setup and builds run in hosted Actions. Core coordinator confirmed ../qflistudio-core and ../qflistudio-core/vendor/re_editor without aliases. Keep package/import name qfli_studio_core. Align pubspec/lock, CI checkout and helper paths together; regenerate locks in cloud only. The current released core pin is 8e031313ffc8d531c5a6b4d131f721f35da04c86. The earlier migration baseline 476a30acee21dc486ee2849dd8064a7be665e4d5 (core-check run 45656065902) remains historical evidence; no result from that run validates the released pin.
