#!/usr/bin/env python3
"""Assemble Go curriculum topic files into aggregate content slices.

Reads ``topics/T<NNN>.json`` (schema in ``schema.md``), validates the shape and
field types against the shared content contract, and writes:

  content/go/tutorials.json   list of tutorial entries (aggregate Go slice)
  content/go/examples.json    list of example entries (aggregate Go slice)
  classify.json               topic -> {runtime, importKind, runCommand, verification}

Standard library only. Exits non-zero on the first structural error so a broken
topic cannot silently enter the aggregate.

Usage:
    python tool/go_curriculum/assemble.py [--topics-dir DIR] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LEVELS = {"beginner", "intermediate", "advanced"}
RUNTIMES = {"desktop", "mobile"}
IMPORT_KINDS = {"single-file", "test-package", "module-project"}
VERIFICATION_KINDS = {
    "stdout-exact",
    "stdout-sorted",
    "stdout-normalized",
    "test-pass",
    "bench-exists",
}
TOPIC_RE = re.compile(r"^T(\d{3})$")

TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_TOPICS = TOOL_DIR / "topics"
DEFAULT_OUT = TOOL_DIR / "content" / "go"

TUTORIAL_KEYS = {
    "id", "language", "type", "locale", "level", "title", "summary",
    "concepts", "source", "license", "updatedAt", "objective",
    "prerequisites", "pitfalls", "exercises", "explain", "code", "output",
}
EXAMPLE_KEYS = {
    "id", "language", "type", "locale", "level", "title", "summary",
    "concepts", "source", "license", "updatedAt", "code", "expectedOutput",
    "templateType",
}


class TopicError(Exception):
    pass


def load_topic(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TopicError(f"{path.name}: not valid JSON ({error})") from error
    if not isinstance(data, dict):
        raise TopicError(f"{path.name}: top level must be an object")

    topic_id = data.get("id")
    if not isinstance(topic_id, str) or not TOPIC_RE.match(topic_id):
        raise TopicError(f"{path.name}: id must be T<NNN>")
    if path.stem != topic_id:
        raise TopicError(f"{path.name}: filename must match id {topic_id}")

    runtime = data.get("runtime")
    if runtime not in RUNTIMES:
        raise TopicError(f"{topic_id}: runtime must be one of {sorted(RUNTIMES)}")
    import_kind = data.get("importKind")
    if import_kind not in IMPORT_KINDS:
        raise TopicError(f"{topic_id}: importKind must be one of {sorted(IMPORT_KINDS)}")
    verification = data.get("verification")
    if not isinstance(verification, dict) or verification.get("kind") not in VERIFICATION_KINDS:
        raise TopicError(f"{topic_id}: verification.kind must be one of "
                         f"{sorted(VERIFICATION_KINDS)}")

    tutorial = _require_entry(data.get("tutorial"), topic_id, "tutorial", TUTORIAL_KEYS)
    example = _require_entry(data.get("example"), topic_id, "example", EXAMPLE_KEYS)

    number = int(topic_id[1:])
    if tutorial["id"] != f"go-tutorial-{number:03d}":
        raise TopicError(f"{topic_id}: tutorial.id must be go-tutorial-{number:03d}")
    if example["id"] != f"go-example-{number:03d}":
        raise TopicError(f"{topic_id}: example.id must be go-example-{number:03d}")
    return data


def _require_entry(entry: object, topic_id: str, kind: str, allowed: set[str]) -> dict:
    if not isinstance(entry, dict):
        raise TopicError(f"{topic_id}: {kind} must be an object")
    extra = set(entry) - allowed
    if extra:
        raise TopicError(f"{topic_id}: {kind} has unknown keys {sorted(extra)}")
    for key in allowed:
        if key not in entry:
            raise TopicError(f"{topic_id}: {kind}.{key} is required")
    for key in ("id", "language", "type", "locale", "level", "title", "summary",
                "source", "license", "updatedAt", "code"):
        if not isinstance(entry[key], str) or not entry[key].strip():
            raise TopicError(f"{topic_id}: {kind}.{key} must be a non-empty string")
    if entry["language"] != "go" or entry["type"] != "go":
        raise TopicError(f"{topic_id}: {kind} language/type must be 'go'")
    if entry["level"] not in LEVELS:
        raise TopicError(f"{topic_id}: {kind}.level must be one of {sorted(LEVELS)}")
    if not isinstance(entry["concepts"], list) or not entry["concepts"]:
        raise TopicError(f"{topic_id}: {kind}.concepts must be a non-empty list")
    if kind == "tutorial":
        if not isinstance(entry.get("objective"), str) or not entry["objective"].strip():
            raise TopicError(f"{topic_id}: tutorial.objective is required")
        if not isinstance(entry.get("prerequisites"), list) or not entry["prerequisites"]:
            raise TopicError(f"{topic_id}: tutorial.prerequisites must be non-empty")
        if not isinstance(entry.get("pitfalls"), list) or len(entry["pitfalls"]) < 2:
            raise TopicError(f"{topic_id}: tutorial.pitfalls needs at least 2 items")
        exercises = entry.get("exercises")
        if not isinstance(exercises, list) or not exercises:
            raise TopicError(f"{topic_id}: tutorial.exercises must be non-empty")
        for exercise in exercises:
            if not isinstance(exercise, dict) or not all(
                isinstance(exercise.get(k), str) and exercise[k].strip()
                for k in ("prompt", "hint", "answer")
            ):
                raise TopicError(f"{topic_id}: each exercise needs prompt/hint/answer")
        if not isinstance(entry.get("explain"), str) or not entry["explain"].strip():
            raise TopicError(f"{topic_id}: tutorial.explain is required")
        if not isinstance(entry.get("output"), str):
            raise TopicError(f"{topic_id}: tutorial.output must be a string")
        # The shared release validator requires every lesson.output to be
        # non-empty, including test-pass/bench-exists topics. The pass/fail
        # decision is still driven by verification, but output must carry real
        # result text so it can never silently enter the aggregate empty.
        if not entry["output"].strip():
            raise TopicError(
                f"{topic_id}: tutorial.output must be non-empty "
                f"(even for test-pass/bench-exists; write the real result text)"
            )
    else:
        if not isinstance(entry.get("expectedOutput"), str):
            raise TopicError(f"{topic_id}: example.expectedOutput must be a string")
        if entry.get("templateType") != "go":
            raise TopicError(f"{topic_id}: example.templateType must be 'go'")
    return entry


def collect(topics_dir: Path) -> list[dict]:
    if not topics_dir.is_dir():
        raise TopicError(f"topics dir not found: {topics_dir}")
    topics: list[dict] = []
    seen: set[str] = set()
    for path in sorted(topics_dir.glob("T*.json")):
        topic = load_topic(path)
        if topic["id"] in seen:
            raise TopicError(f"duplicate topic id {topic['id']}")
        seen.add(topic["id"])
        topics.append(topic)
    topics.sort(key=lambda t: t["id"])
    return topics


def to_tutorial_entry(topic: dict) -> dict:
    """Pack a topic's flat tutorial fields into the real aggregate shape.

    The shared contract stores teaching fields inside ``lessons[]``; a topic has
    exactly one lesson, so ``tutorial.*`` becomes ``lessons[0].*`` while the
    identifying fields stay on the entry.
    """
    tutorial = topic["tutorial"]
    entry_id = tutorial["id"]
    lesson = {
        "id": f"{entry_id}-lesson",
        "title": tutorial["title"],
        "summary": tutorial["summary"],
        "concepts": list(tutorial["concepts"]),
        "explain": tutorial["explain"],
        "code": tutorial["code"],
        "output": tutorial["output"],
        "objective": tutorial["objective"],
        "prerequisites": list(tutorial["prerequisites"]),
        "pitfalls": list(tutorial["pitfalls"]),
        "exercises": [dict(e) for e in tutorial["exercises"]],
    }
    return {
        "id": entry_id,
        "language": tutorial["language"],
        "type": tutorial["type"],
        "locale": tutorial["locale"],
        "level": tutorial["level"],
        "title": tutorial["title"],
        "summary": tutorial["summary"],
        "concepts": list(tutorial["concepts"]),
        "source": tutorial["source"],
        "license": tutorial["license"],
        "updatedAt": tutorial["updatedAt"],
        "lessons": [lesson],
    }


def to_example_entry(topic: dict) -> dict:
    example = topic["example"]
    return {
        "id": example["id"],
        "language": example["language"],
        "type": example["type"],
        "locale": example["locale"],
        "level": example["level"],
        "title": example["title"],
        "summary": example["summary"],
        "concepts": list(example["concepts"]),
        "source": example["source"],
        "license": example["license"],
        "updatedAt": example["updatedAt"],
        "code": example["code"],
        "expectedOutput": example["expectedOutput"],
        "templateType": example["templateType"],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topics-dir", type=Path, default=DEFAULT_TOPICS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    try:
        topics = collect(args.topics_dir)
    except TopicError as error:
        print(f"ASSEMBLE FAIL: {error}")
        return 1

    tutorials = [to_tutorial_entry(t) for t in topics]
    examples = [to_example_entry(t) for t in topics]
    classify = [
        {
            "id": t["id"],
            "runtime": t["runtime"],
            "importKind": t["importKind"],
            "runCommand": t["runCommand"],
            "verification": t["verification"],
            "sampleFiles": t.get("sampleFiles", []),
        }
        for t in topics
    ]

    args.out.mkdir(parents=True, exist_ok=True)
    _dump(args.out / "tutorials.json", tutorials)
    _dump(args.out / "examples.json", examples)
    _dump(args.out.parent / "classify.json", classify)
    print(f"ASSEMBLE OK: {len(tutorials)} tutorials, {len(examples)} examples "
          f"from {len(topics)} topics")
    return 0


def _dump(path: Path, data: object) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
