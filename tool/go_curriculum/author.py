#!/usr/bin/env python3
"""Authoring helper: build topic JSON whose tutorial.code matches the sample.

Not part of the verify pipeline; used while writing topics so that
``tutorial.code`` is guaranteed byte-identical to ``samples/T<NNN>/<file>``.
The topic is also written to ``topics/T<NNN>.json``.

Usage is programmatic: import build_topic from another script, or extend the
SPECS map. Kept simple and dependency-free.
"""

from __future__ import annotations

import json
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
SAMPLES = TOOL_DIR / "samples"
TOPICS = TOOL_DIR / "topics"

LICENSE = "Original QFLI curriculum; reference link retained. CC BY 4.0"
SOURCE = "https://go.dev/doc/"
UPDATED = "2026-10-12"


def read_sample(topic_id: str, name: str = "main.go") -> str:
    return (SAMPLES / topic_id / name).read_text(encoding="utf-8")


def build_topic(
    *,
    topic_id: str,
    level: str,
    title: str,
    summary: str,
    concepts: list[str],
    objective: str,
    prerequisites: list[str],
    pitfalls: list[str],
    exercises: list[dict],
    explain: str,
    output: str,
    verification_kind: str = "stdout-exact",
    expected: str | None = None,
    example_title: str | None = None,
    example_summary: str | None = None,
    example_code: str | None = None,
    example_expected: str | None = None,
    runtime: str = "desktop",
    import_kind: str = "single-file",
    run_command: str = "go run .",
    sample_files: list[str] | None = None,
) -> dict:
    code = read_sample(topic_id, (sample_files or ["main.go"])[0])
    number = int(topic_id[1:])
    topic = {
        "id": topic_id,
        "runtime": runtime,
        "importKind": import_kind,
        "runCommand": run_command,
        "verification": {
            "kind": verification_kind,
            "expected": expected if expected is not None else output + "\n",
        },
        "sampleFiles": sample_files or ["main.go"],
        "tutorial": {
            "id": f"go-tutorial-{number:03d}",
            "language": "go",
            "type": "go",
            "locale": "zh-CN",
            "level": level,
            "title": title,
            "summary": summary,
            "concepts": concepts,
            "source": SOURCE,
            "license": LICENSE,
            "updatedAt": UPDATED,
            "objective": objective,
            "prerequisites": prerequisites,
            "pitfalls": pitfalls,
            "exercises": exercises,
            "explain": explain,
            "code": code,
            "output": output,
        },
        "example": {
            "id": f"go-example-{number:03d}",
            "language": "go",
            "type": "go",
            "locale": "zh-CN",
            "level": level,
            "title": example_title if example_title is not None else title,
            "summary": example_summary if example_summary is not None else summary,
            "concepts": concepts,
            "source": SOURCE,
            "license": LICENSE,
            "updatedAt": UPDATED,
            "code": example_code if example_code is not None else code,
            "expectedOutput": example_expected if example_expected is not None else output,
            "templateType": "go",
        },
    }
    return topic


def write_topic(topic: dict) -> None:
    path = TOPICS / f"{topic['id']}.json"
    path.write_text(
        json.dumps(topic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
