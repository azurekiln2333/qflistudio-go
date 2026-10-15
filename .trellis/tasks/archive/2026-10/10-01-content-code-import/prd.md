# Learning Content and Code Import

## Request

Simplify the tutorial and example lists using Material Design 3. Show code only
inside details. Each detail code block must offer import into the editor and
import into a project, allow a custom filename, and open the imported project.

## Acceptance Criteria

- Tutorial and example lists show compact titles and summaries without code.
- Details expose selectable code, copy, import into editor, and import into project.
- Both import actions allow the user to edit the filename before writing.
- Editor import opens a writable file in the existing editor.
- Project import can select an existing local project or create a new project.
- New projects persist in the real project registry; custom filenames replace the
  generated entry file so Go projects do not contain duplicate main functions.
- Existing files are preserved when the requested filename is occupied unless
  the user explicitly confirms replacing that file.
- Successful project import opens that project with the imported file selected,
  even when another editor session was saved previously.
- Cancellation and invalid names do not create files or projects.
- Controls remain usable at narrow phone sizes, desktop sizes, and large text.
- Existing themes, settings, localization, navigation, and edits are preserved.

## Validation

Focused filesystem and widget tests, Dart analysis, application tests, and rendered
desktop and phone screenshots of lists, details, and import dialogs.
