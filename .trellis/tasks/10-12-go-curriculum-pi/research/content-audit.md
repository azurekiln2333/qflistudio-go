# Go content & loading-chain audit (read-only)

Scope: `qfli_go` + `../qfli_studio_core` only. No product code changed.

## 1. Where Go learning content actually lives

| Concern | Path | Notes |
| --- | --- | --- |
| Aggregate tutorials | `../qfli_studio_core/assets/content/tutorials.json` | 3.4 MB; `{schemaVersion, entries[]}` |
| Aggregate examples | `../qfli_studio_core/assets/content/examples.json` | 1.7 MB; `{schemaVersion, entries[]}` |
| Legacy per-language tutorials | `../qfli_studio_core/assets/tutorials/*.json` | `c, cpp, web, python, java, dart, lua` only — **no `go.json`** |
| Asset registration | `../qfli_studio_core/pubspec.yaml:42-44` | `assets/content/` already bundled |
| Loader | `../qfli_studio_core/lib/content/asset_content_repository.dart` | `AssetContentRepository`, keys `packages/qfli_studio_core/assets/content/*.json` then bare |
| Parser/model | `../qfli_studio_core/lib/content/content_repository.dart` | `ContentCatalog.fromJson`, `ContentProductTypes` |
| Adapter | `../qfli_studio_core/lib/content/local_content_adapter.dart` | tutorial entry → chapter; example → `ExampleCode` |
| UI | `../qfli_studio_core/lib/pages/local_content_pages.dart` | `LocalTutorialsTab`, `ExampleCodeTab`, `ExampleDetailPage`, `_LessonPage` |
| Validator | `../qfli_studio_core/lib/content/content_validator.dart` | `validateForRelease`, `releaseMinimumPerType = 100` |
| Legacy loader | `../qfli_studio_core/lib/services/tutorial_service.dart` | `bundledLanguages` excludes `go` (unused by Go app) |
| Import/entry | `../qfli_studio_core/lib/services/code_import_service.dart`, `project_templates.dart:78` | Go main file `src/main.go`; `suggestedFileName('go') == 'main.go'` |

### Go selection
`ContentProductTypes.byProduct['goshift'] = {'go'}` (content_repository.dart:30),
and `LocalContentAdapter._filter` uses `ContentFilter.forProduct('goshift')` when
`productKey` is `goshift`. `goProfile.productKey = StudioProductCatalog.goShiftKey`
(`lib/main.dart`). So the Go app shows exactly `type == 'go'` entries. No code
change is needed to swap content.

### No local injection path
`HomePage` builds `LocalTutorialsTab`/`ExampleCodeTab` without passing
`repository` (`home_page.dart:217,226`), so they always fall back to
`AssetContentRepository` reading the shared assets. Injecting Go-local assets
would require editing shared core (conflicts with "preserve existing UI/import
behavior"). ⇒ Go content must be delivered into the shared aggregate files.

## 2. Placeholder evidence (quantified)

Both files: 16 languages × exactly 100 entries = 1600 each. Go:
`go-tutorial-001..100`, `go-example-001..100`.

For `go-tutorial-001..003` (and uniformly across all 100):

- `explain` is the **same** sentence for every lesson (concept label differs only
  in the title/summary prefix), e.g.
  "…该固定序列重复执行，确保可复现的结果…" — a generic filler.
- `code` is the same weighted-sum program with a different seed:
  `values := []int{1,3,5}` vs `{2,4,6}` vs `{3,5,7}` →
  `weighted=22/28/34`. Every lesson is this one algorithm.
- `objective` = absent/null; `prerequisites` = absent/null; `pitfalls` =
  absent/null (the UI `_LessonPage` conditionally hides them, so the placeholder
  stays invisible).
- Every lesson repeats the **same** exercise prompt
  ("为此路径增加一个边界输入…") and the same hint/answer.
- `source` = bare `https://go.dev/doc/` for all 100; `license` identical.
- Example `go-example-0NN` titles are the same "数据建模与不变式 / 边界校验 /
  文件格式校验…" template with only the index changed.

Conclusion: content is template-generated filler; it passes the count gate but
fails every substance/duplication requirement. Length/count alone is not
acceptable proof of quality (R4/AC3/AC4).

## 3. Schema and validator contract (what new content must satisfy)

- Tutorial entry serialized fields consumed:
  `id, language, type, locale, level, title, summary, concepts[], source,
  license, updatedAt, lessons[]`.
- Lesson fields: `id, title, summary, concepts[], explain, code, output,
  objective, prerequisites[], pitfalls[], exercises[]` (`exercises` or legacy
  `tasks`; prompt/hint/answer).
- Example fields: `id, language, type, locale, level, title, summary,
  concepts[], source, license, updatedAt, code, expectedOutput,
  templateType` (legacy `output` accepted).
- `validateForRelease` requires ≥100 per type and non-empty id/language/type/
  locale/level/title/summary/concepts/source/license/updatedAt, non-empty lesson
  id/title/summary/explain/code/output/concepts, non-empty example
  code/templateType. It does **not** check duplication or length.

## 4. Runtime capability boundary (desktop vs mobile)

- Desktop uses the official Go toolchain (`official-go-sdk`); mobile
  (android/ohos/ios) uses the embedded Yaegi interpreter (`embedded-go-runtime`)
  — `lib/go_platform.dart`, `lib/go_runner.dart`.
- Yaegi (vendored, with local fixes) exposes a stdlib subset via
  `stdlib.Symbols`, but support for generics, `//go:embed`,
  `//go:generate`, `go test -race/-bench/-fuzz`, parts of `reflect`/`context`/
  `net`, cgo, and `os/exec` is not assumed. Any claim must be verified against
  **this project's** `native/go_runtime` build, not vendor docs.
- Policy: all generics topics are **desktop-only by default**; other mobile
  candidates are promoted to "mobile-safe" only after a native-runtime run
  passes and the result is recorded.

## 5. Import contract and non-single-file topics

- `CodeImportService.suggestedFileName('go') == 'main.go'`
  (`ProjectTemplate.go` main file `src/main.go`); import writes exactly one file
  and sets `entryFile`. This is unchanged.
- `go test`/`-bench`/`-fuzz`, multi-file packages and `go.mod` projects cannot
  be represented as a one-file import. Each such topic must state the required
  files and commands; it must not claim lossless multi-file import.

## 6. Duplication vs identical output

- The placeholder is proven by one shared `explain` and one weighted-sum `code`
  across all 100 Go lessons. Detection must target that substantive reuse.
- Identical `output` values are legitimate when different samples both yield
  e.g. `true` or empty stdout; a lesson and its own paired example may share
  code. The dedup check must whitelist trivial primitives and ignore these
  cases, relying on recorded semantic review to catch filler.

## 7. Shared-write risk and integration

The two aggregate files are edited by multiple language sessions concurrently.
"atomic rename + pre-read hash" alone cannot exclude a concurrent writer landing
between read and rename. Default delivery is therefore a reviewable Go-slice
patch applied by a single authorized integrator (or all writers under a shared
lock); never last-writer-wins over unknown Go edits. See design.md R8/AC7.

## 8. Durable artifact location

Samples, Go content source and verification tooling live under
`qfli_go/tool/go_curriculum/` (maintainable), not solely under the archived task
`research/`.

## 9. Curriculum map

- `research/curriculum-map.md` (owned by w8:p3) defines the 120 topics
  (T001–T120) across S1–S12 with per-topic runtime markers. Not edited here;
  this audit states the content and verification contract that map must satisfy.
