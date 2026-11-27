"""Deterministic fixtures for the cloud-only policy and Trellis reference check."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import cloud_policy


class PolicyMatcherTests(unittest.TestCase):
    def test_detects_explicit_local_execution_authorization(self) -> None:
        examples = (
            "You may run tests locally.",
            "Run the build on a local machine.",
            "Local tests are allowed.",
            "Run flutter analyze on the developer workstation.",
            "Run commands locally.",
            "go vet is allowed locally.",
            "Local benchmarks are allowed.",
            "Emulators may execute on the developer machine.",
            "You can 本地运行测试。",
        )
        for example in examples:
            with self.subTest(example=example):
                self.assertTrue(cloud_policy._authorizes_local_execution(example))

    def test_ignores_prohibitions_and_cloud_only_instructions(self) -> None:
        examples = (
            "Never run tests locally.",
            "Do not run builds on the local machine.",
            "Tests are not permitted on a local workstation.",
            "本地禁止运行测试。",
            "Run builds and tests only in GitHub Actions.",
            "Local test execution is forbidden.",
            "A missing hosted check is not permission to run the command locally.",
            "pending verification item, not permission to run the command locally.",
            "Do not run local builds, tests, benchmarks, emulators, or native compilation.",
            "go vet must not execute locally.",
            "Never use local benchmarks.",
            "Local emulators are prohibited.",
            "禁止在本机运行此检查。",
        )
        for example in examples:
            with self.subTest(example=example):
                self.assertFalse(cloud_policy._authorizes_local_execution(example))

    def test_ignores_non_execution_uses_of_local_and_hosted_command_examples(self) -> None:
        examples = (
            "Build entry points set GOTOOLCHAIN=local: an older SDK reports an error.",
            "All build scripts set local/vendor/offline dependency resolution.",
            "Keep these settings local to verification; rerun the SDK assertions in Actions.",
            "Base: omitting -Platform retains the existing Android/OHOS local build.",
            "Use official Go 1.27.1, vendored sources and local/offline build flags.",
        )
        for example in examples:
            with self.subTest(example=example):
                self.assertFalse(cloud_policy._authorizes_local_execution(example))

    def test_detects_authorization_after_local_qualifier(self) -> None:
        self.assertTrue(
            cloud_policy._authorizes_local_execution(
                "Local tests are allowed when the SDK is present."
            )
        )

    def test_separates_prohibition_from_a_later_permission(self) -> None:
        line = "Do not run tests locally. Run them on the developer machine for speed."
        segments = tuple(cloud_policy._segments(line))
        self.assertEqual(len(segments), 2)
        self.assertFalse(cloud_policy._authorizes_local_execution(segments[0]))
        self.assertTrue(cloud_policy._authorizes_local_execution(segments[1]))

    def test_permission_denial_does_not_hide_a_later_authorization(self) -> None:
        self.assertTrue(cloud_policy._authorizes_local_execution(
            "A missing hosted check is not permission to run tests locally, "
            "but go vet is allowed locally."
        ))

    def test_ignores_examples_quoted_text_tables_and_history(self) -> None:
        text = """# Current

All commands below run only in GitHub-hosted Actions.
Historical local evidence does not authorize local reruns.

```text
You may run tests locally.
```

> You may run tests locally.

| Note | You may run tests locally. |

## Historical test results
You may run builds locally.

## Current rules
Never run checks locally.
"""
        active = tuple(cloud_policy._active_lines(text))
        self.assertFalse(any(cloud_policy._authorizes_local_execution(line.text)
                             for line in active))

    def test_flags_only_affirmative_active_prose(self) -> None:
        text = """# Rules

Do not run tests locally. Run tests locally when convenient.
"""
        matches = [line for line in cloud_policy._active_lines(text)
                   if cloud_policy._authorizes_local_execution(line.text)]
        self.assertEqual([line.number for line in matches], [3])


class TrellisManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "AGENTS.md").write_text(
            "Do not run builds or tests locally.\n", encoding="utf-8"
        )
        task = self.root / ".trellis/tasks/current"
        task.mkdir(parents=True)
        (task / "task.json").write_text(
            json.dumps({"status": "in_progress"}), encoding="utf-8"
        )
        self.manifest = task / "check.jsonl"

    def write_records(self, records: list[object]) -> None:
        self.manifest.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )

    def test_accepts_unique_existing_paths_and_archived_targets(self) -> None:
        spec = self.root / ".trellis/spec/backend"
        spec.mkdir(parents=True)
        (spec / "cloud.md").write_text("Contract\n", encoding="utf-8")
        archived = self.root / ".trellis/tasks/archive/2026-11/task.md"
        archived.parent.mkdir(parents=True)
        archived.write_text("Archived evidence\n", encoding="utf-8")
        self.write_records([
            {"file": ".trellis/spec/backend/cloud.md", "reason": "spec"},
            {"file": ".trellis/tasks/archive/2026-11/task.md", "reason": "archive"},
        ])
        self.assertEqual(cloud_policy.validate_repository(self.root), [])

    def test_reports_duplicates_missing_and_unsafe_paths(self) -> None:
        existing = self.root / "README.md"
        existing.write_text("readme\n", encoding="utf-8")
        self.write_records([
            {"file": "README.md"},
            {"file": "readme.md"},
            {"file": "missing.md"},
            {"file": "../outside.md"},
            {"file": "C:/outside.md"},
        ])
        findings = cloud_policy.validate_repository(self.root)
        self.assertEqual(len(findings), 4)
        self.assertTrue(any("duplicate path" in finding for finding in findings))
        self.assertTrue(any("missing or escapes" in finding for finding in findings))
        self.assertEqual(sum("unsafe or non-portable" in finding for finding in findings), 2)

    def test_reports_malformed_json_and_missing_file_field(self) -> None:
        self.manifest.write_text('{bad json}\n{}\n', encoding="utf-8")
        findings = cloud_policy.validate_repository(self.root)
        self.assertEqual(len(findings), 2)
        self.assertTrue(any("invalid JSON" in finding for finding in findings))
        self.assertTrue(any("string 'file'" in finding for finding in findings))

    def test_manifest_findings_are_stable(self) -> None:
        self.write_records([{"file": "missing-a.md"}, {"file": "missing-b.md"}])
        first = cloud_policy.validate_repository(self.root)
        second = cloud_policy.validate_repository(self.root)
        self.assertEqual(first, second)
        self.assertEqual(first, sorted(first))

    def test_scanner_detects_policy_in_active_task_documents(self) -> None:
        task_dir = self.root / ".trellis/tasks/current"
        (task_dir / "task.json").write_text(
            json.dumps({"status": "in_progress"}), encoding="utf-8"
        )
        (task_dir / "design.md").write_text(
            "Run builds on a developer machine.\n", encoding="utf-8"
        )
        findings = cloud_policy.validate_repository(self.root)
        self.assertTrue(any("design.md:1" in finding for finding in findings))

    def test_ignores_completed_task_instructions(self) -> None:
        task_dir = self.root / ".trellis/tasks/current"
        (task_dir / "task.json").write_text(
            json.dumps({"status": "completed"}), encoding="utf-8"
        )
        (task_dir / "design.md").write_text(
            "Run builds on a developer machine.\n", encoding="utf-8"
        )
        self.assertEqual(cloud_policy.validate_repository(self.root), [])

    def test_does_not_scan_archived_task_manifests(self) -> None:
        archived = self.root / ".trellis/tasks/archive/old"
        archived.mkdir(parents=True)
        (archived / "task.json").write_text(
            json.dumps({"status": "in_progress"}), encoding="utf-8"
        )
        (archived / "check.jsonl").write_text('{bad json}\n', encoding="utf-8")
        self.assertEqual(cloud_policy.validate_repository(self.root), [])

    def test_rejects_a_manifest_reference_that_escapes_by_symlink(self) -> None:
        outside = self.root.parent / (self.root.name + "-outside.md")
        outside.write_text("outside\n", encoding="utf-8")
        self.addCleanup(outside.unlink, missing_ok=True)
        link = self.root / "linked.md"
        try:
            link.symlink_to(outside)
        except (NotImplementedError, OSError):
            self.skipTest("symlink creation is unavailable on this hosted platform")
        self.write_records([{"file": "linked.md"}])
        findings = cloud_policy.validate_repository(self.root)
        self.assertTrue(any("missing or escapes checkout" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
