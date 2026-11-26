# Frontend Development Guidelines

> Best practices for frontend development in this project.

---

## Overview

All verification commands in these specs run only in GitHub-hosted Actions.
Read `AGENTS.md` and [Cloud-Only Execution](../backend/cloud-only-execution.md)
before executing any command. Local reads/source edits and `python -B` task
metadata are permitted within ownership; project checks are not.

This directory contains guidelines for frontend development. Fill in each file with your project's specific conventions.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | To fill |
| [Component Guidelines](./component-guidelines.md) | Component patterns, props, composition | To fill |
| [Hook Guidelines](./hook-guidelines.md) | Custom hooks, data fetching patterns | To fill |
| [State Management](./state-management.md) | Local state, global state, server state | To fill |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | To fill |
| [Type Safety](./type-safety.md) | Type patterns, validation | To fill |
| [Content Code Import](./content-code-import.md) | Shared learning pages, imports, project entry and editor contracts | Documented |
| [Editor Terminal and Run](./editor-terminal-run.md) | Continuous transcript, quiet success and tap/long-press entry contracts | Documented |
| [Native Startup](./native-startup.md) | HarmonyOS progress bridge, first-frame deferral and loading layer lifecycle | Documented |

---

## How to Fill These Guidelines

For each guideline file:

1. Document your project's **actual conventions** (not ideals)
2. Include **code examples** from your codebase
3. List **forbidden patterns** and why
4. Add **common mistakes** your team has made

The goal is to help AI assistants and new team members understand how YOUR project works.

---

**Language**: All documentation should be written in **English**.

