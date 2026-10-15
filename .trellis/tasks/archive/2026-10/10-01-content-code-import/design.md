# Design

The Go app consumes shared pages from ../qfli_studio_core. Current source now
includes concurrent work for this request. Adopt that authoritative implementation
and review it against the goal; discard our unused staged duplicate implementation.

MD3 ListTile rows and unframed chapter headings keep code out of discovery pages.
Both lesson details and example details render the shared CodeSnippet. The example
detail retains its editable controller; copy and import use its current contents.
HomePage supplies its live ProjectStore, AuthStore, and SettingsStore to both tabs.

CodeSnippet presents two icon commands with localized tooltips, then a filename
dialog. Project import can select an existing local project or create a new one.
CodeImportService handles validation, exclusive file creation, scratch workspaces,
and existing-project imports. Independent editor workspaces live in application
storage and the dialog registers them so saved files can be reopened from the
project list. Filenames are exact, including extensions.

ProjectStore.createProjectFromExample replaces the template entry file with the
requested file and records that relative path in .qfli/project.json. RunnerService
honors this entryFile, preserving project execution with custom filenames.
EditorPage restores prior tabs and then selects initialOpenPath. CodeSnippet also
selects the imported project as the file explorer's remembered root before opening
the editor. Existing regular files require an explicit replacement confirmation;
cancelling that confirmation leaves the form open for filename correction.

All import messages use Simplified Chinese, Traditional Chinese, and English via
StudioLocalizations. Themes and primary navigation follow the existing app.

## Current Change Boundary

Authoritative implementation under review:

- lib/pages/local_content_pages.dart: compact lists and shared code snippets.
- lib/pages/home_page.dart: live editor dependency wiring to offline content.
- lib/widgets/code_snippet.dart: shared code actions, dialog, and editor navigation.
- lib/services/code_import_service.dart: filenames and actual filesystem imports.
- lib/store/project_store.dart: custom example entry and project registration.
- lib/services/project_config.dart: optional explicit project entry metadata.
- lib/services/runner_service.dart: entry metadata recognition.
- lib/editor/editor_page.dart: explicit imported path after prior session restore.
- lib/i18n/studio_localizations.dart: localized import messages.
- test/studio_profile_test.dart: list expectations updated for code in details.

Remaining edits from this continuation:

- CodeSnippet: make the file explorer show the project being opened and fix its
  unused import.
- StudioLocalizations / CodeSnippet: use a dedicated code import failure message.
- EditorPage: fix the existing missing-braces lint in the touched file.
- qfli_go/test/content_code_import_test.dart: filesystem and widget verification.

Navigation, the Go runtime implementation, and unrelated edited modules are
outside this task. No new dependency is needed.

## Review and Recovery

Stage only missing source fixes in qfli_go and apply their reviewed patch to the
sibling via explicit filesystem escalation. Check patch applicability against the
current source before applying, preserving concurrent changes.
