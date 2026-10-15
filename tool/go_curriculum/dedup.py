#!/usr/bin/env python3
"""Detect substantive duplication across Go curriculum topics.

Flags the placeholder pattern the task replaces: one shared ``explain`` body, or
one code/example template that differs only by a literal, spread across many
topics. Trivial identical outputs and a lesson sharing its own example code are
explicitly allowed.

Heuristics (reported, not auto-edited):

* ``explain`` normalized (whitespace/numbers stripped) reused by >= 2 topics.
* ``code`` normalized with all integer/float literals replaced by ``#`` reused
  by >= 2 topics (constant-swap templates). Exact-identical code is also flagged.
* exercise prompt sets reused wholesale across topics.

Standard library only. Exits non-zero if any substantive duplication is found.

Usage:
    python tool/go_curriculum/dedup.py [--topics-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_TOPICS = TOOL_DIR / "topics"

NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
WS_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    return WS_RE.sub(" ", text).strip()


def normalize_code(code: str) -> str:
    return WS_RE.sub(" ", NUMBER_RE.sub("#", code)).strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topics-dir", type=Path, default=DEFAULT_TOPICS)
    args = parser.parse_args(argv)

    explain_groups: dict[str, list[str]] = defaultdict(list)
    code_groups: dict[str, list[str]] = defaultdict(list)
    exercise_groups: dict[str, list[str]] = defaultdict(list)

    topics = []
    for path in sorted(args.topics_dir.glob("T*.json")):
        topic = json.loads(path.read_text(encoding="utf-8"))
        topics.append(topic)
        explain_groups[normalize_text(topic["tutorial"]["explain"])].append(topic["id"])
        code_groups[normalize_code(topic["tutorial"]["code"])].append(topic["id"])
        prompts = "|".join(
            normalize_text(e["prompt"]) for e in topic["tutorial"]["exercises"]
        )
        exercise_groups[prompts].append(topic["id"])

    problems: list[str] = []
    for kind, groups in (
        ("explain", explain_groups),
        ("code-template", code_groups),
        ("exercise-set", exercise_groups),
    ):
        for key, ids in groups.items():
            if len(ids) >= 2:
                problems.append(f"{kind} reused by {ids}: {key[:80]}...")

    if problems:
        for problem in problems:
            print(f"DUP  {problem}")
        print(f"DEDUP: {len(problems)} substantive duplication(s) in {len(topics)} topics")
        return 1
    print(f"DEDUP OK: no substantive duplication in {len(topics)} topics")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
