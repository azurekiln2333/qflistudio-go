# Replace Go placeholder lessons/examples with 120 substantive tutorials and examples

## Goal

Replace the placeholder Go learning content the Go app displays with a real,
progressive Go curriculum: **exactly 120 substantive tutorial lessons and 120
matching runnable examples**, beginner to advanced. A learner must be able to
read a lesson, understand why it works, run the code, and see a real, verified
result — not a template whose only difference is a number.

## Background (confirmed by repository inspection)

- Content lives in the shared package `../qfli_studio_core`:
  - Aggregate assets the app consumes: `assets/content/tutorials.json` and
    `assets/content/examples.json` (`qfli_studio_core/pubspec.yaml:42-44`).
  - Loaded by `lib/content/asset_content_repository.dart`, parsed by
    `lib/content/content_repository.dart` (`ContentCatalog.fromJson`), adapted by
    `lib/content/local_content_adapter.dart`, rendered by
    `lib/pages/local_content_pages.dart`.
- The Go app filters by `productKey == 'goshift'` → `{'go'}`
  (`content_repository.dart:30`), so only `type:'go'` entries show. No UI change
  is needed to swap content.
- The legacy loader `lib/services/tutorial_service.dart` excludes `go` and there
  is no `assets/tutorials/go.json`; the Go app uses the aggregate path.
- Placeholder proof: all 16 languages have exactly 100 entries each; Go =
  `go-tutorial-001..100` / `go-example-001..100`. Every Go lesson reuses one
  generic `explain` sentence and one weighted-sum `code` with only a numeric
  seed changed (`weighted=22/28/34`); `objective`/`prerequisites`/`pitfalls` are
  absent; every lesson repeats the same exercise; `source` is a bare
  `https://go.dev/doc/`.
- `ContentCatalogValidator.validateForRelease`
  (`lib/content/content_validator.dart`) requires ≥100 per type and non-empty
  fields; it does not detect duplication or length.
- Import/entry contract (`CodeImportService`, `ProjectTemplate.go` main file
  `src/main.go`): `suggestedFileName('go') == 'main.go'`; single-file import
  writes one file and sets `entryFile`. This task must not change it.
- `HomePage` builds the content tabs without injecting a repository
  (`home_page.dart:217,226`), so they always read the shared assets.

## Requirements

- **R1 Scope.** Exactly 120 Go tutorial lessons and 120 Go examples, unique by
  topic, following the chapter plan in `research/curriculum-map.md` (owned by
  w8:p3): environment/basics, control flow, collections/functions/pointers,
  structs/methods/interfaces, errors & defer/panic/recover, packages/modules/
  generics, concurrency/sync/context, stdlib IO/JSON/time/regexp, network/HTTP,
  testing/benchmark/fuzz, performance & engineering practice, integrated
  projects.
- **R2 Substance per lesson.** Each lesson has a real `objective`, non-empty
  `prerequisites`, concept-and-why `explain`, a complete standalone `code` sample,
  a verified `output`, non-empty `pitfalls` (≥2), and ≥1 exercise with a distinct
  prompt/hint/answer.
- **R3 Real, verified examples.** Each example demonstrates its own topic,
  self-contained and offline; its code is compiled and run with the pinned local
  SDK (`native/build/go-sdk-1.27.1/go/bin/go.exe`) and its captured result matches
  `expectedOutput` (or the pre-declared assertion for non-stdout cases).
- **R4 No filler.** No shared boilerplate where only a label/seed changes; no two
  lessons share identical `explain` bodies; no template-with-constant variant
  masquerading as a new topic; no duplicated exercise sets. Reasonable identical
  *primitive* lines (e.g. a shared `package main` header or a 3-line bootstrap)
  are allowed via an explicit whitelist; detection targets **substantive**
  duplication. Note: identical `output` bodies are explicitly allowed when two
  genuinely different samples both produce e.g. `true` or empty stdout; and a
  lesson and its own paired example may share code.
- **R5 Runtime honesty.** Content must classify each lesson desktop vs mobile
  based on *this project's* native runtime boundary, not vendor claims. All
  generic topics are **desktop-only by default** until the actual Yaegi build in
  `native/go_runtime` is proven to run them; any other mobile claim is likewise
  asserted only after native-runtime verification. Desktop-only lessons say so
  and state their command; `go test`/`bench`/`fuzz`, multi-file modules, cgo,
  `os/exec`, `//go:embed`, `//go:generate` are never presented as one-click
  `main.go` imports on mobile.
- **R6 Preserve UI/import behavior.** No change to the content tabs,
  `CodeSnippet`, `CodeImportService`, or the single-file import/`entryFile`
  contract. Multi-file/module/test examples are represented honestly:
  `implement.md` defines, before coding, what is importable as a single
  `main.go` versus what the lesson states must be created by hand or run via a
  command. No false lossless multi-file import claim.
- **R7 Localization.** `zh-CN`, matching existing Go entries and the app locale
  contract. No new locale fields or contract.
- **R8 Shared-repo isolation.** Only Go entries inside the two shared aggregate
  files change; every other language stays byte-identical. Because concurrent
  writers exist, the default deliverable is a **reviewable Go-slice patch**
  assembled in this workspace and applied by a single authorized integration
  step; there is no last-writer-wins overwrite of unknown Go edits.
- **R9 Preserve existing Go work.** The uncommitted Go runner/native/terminal
  changes and generated `.so`/`.h` must not be reverted, overwritten, or
  reformatted.

## Acceptance Criteria

- **AC1 (R1, R4).** Count is exactly 120 tutorials and 120 examples, topics
  unique against `research/curriculum-map.md`, each with a desktop/mobile
  classification.
- **AC2 (R2, R5).** Every lesson passes `validateForRelease` per-entry checks and
  has non-empty `objective`/`prerequisites`/`pitfalls` and ≥1 distinct exercise.
  Mobile support claims match verified native-runtime behavior (generics =
  desktop-only unless proven otherwise).
- **AC3 (R3).** Every one of the 120 tutorial code samples and 120 examples is
  compiled and executed (or tested) with per-item recorded evidence: pass/fail
  and actual vs expected. For concurrent output and benchmarks, a pre-declared
  deterministic assertion (sorted/normalized comparison, counters, or benchmark
  presence) replaces literal stdout equality; no item is exempted without a
  recorded method.
- **AC4 (R4).** A duplication analysis over Go entries flags no substantive
  template reuse (beyond the whitelisted primitives); identical trivial
  `output`s and a lesson sharing its own example's code are not flagged.
- **AC5 (R6).** Existing content/import regressions pass
  (`test/content_code_import_test.dart`, shared `content_repository_test.dart`);
  the Go app renders the new Go content; `suggestedFileName('go')=='main.go'` and
  `entryFile` metadata are unchanged; every non-single-file example honestly
  states how it is created/run.
- **AC6 (R2, R3).** A per-chapter semantic review (recorded in the check phase)
  confirms each lesson teaches its mapped topic and its code/explanation/output
  agree.
- **AC7 (R8).** The Go-slice patch audit proves only Go entries change in the
  shared files; applied by a single authorized integrator (or all writers obey a
  shared lock), never as a blind overwrite.

## Out of Scope

- New UI, schema fields, locales, or product features.
- Other languages' content, legacy per-language `assets/tutorials/*.json`.
- Go runtime/toolchain/terminal/native changes.
- Network dependencies at runtime; all examples offline and self-contained
  (`net/http/httptest` instead of real services).

## Constraints / decisions

- **C1 (resolved).** The user authorized the Go content improvement; writing into
  `../qfli_studio_core` is a **permission boundary for the final application
  step**, not a product decision. Plan: finish 120/120 content and all local
  validation in this workspace, produce a reviewable Go-slice patch, then request
  precise shared-file write authorization for the single integration step. This
  does not block content authoring.
- **C2 (resolved).** Locale is `zh-CN` (existing Go contract); no further
  confirmation needed.
- **C3 (durable location).** Samples, source content and verification scripts
  live under `qfli_go/tool/go_curriculum/` (long-term maintainable), not solely
  under the archived task `research/`.
