"""Shared authoring helper for isolated, unpromoted curriculum drafts."""
from __future__ import annotations

import importlib.util
import subprocess
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
spec = importlib.util.spec_from_file_location("curriculum_author", ROOT / "tool/go_curriculum/author.py")
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
author.SAMPLES = HERE / "samples"
author.TOPICS = HERE / "topics"
author.UPDATED = "2026-10-23"
author.TOPICS.mkdir(parents=True, exist_ok=True)


def lesson(number, title, concepts, summary, explain, pitfalls, exercise, answer, code, output):
    topic_id = f"T{number:03d}"
    sample = author.SAMPLES / topic_id
    sample.mkdir(parents=True, exist_ok=True)
    (sample / "main.go").write_text(textwrap.dedent(code).lstrip(), encoding="utf-8", newline="\n")
    subprocess.run([str(ROOT / "native/build/go-sdk-1.27.1/go/bin/gofmt.exe"), "-w", str(sample / "main.go")], check=True)
    topic = author.build_topic(
        topic_id=topic_id, level="intermediate", title=title, summary=summary,
        concepts=concepts, objective=summary, prerequisites=["T035", "T049"],
        pitfalls=pitfalls, exercises=[{"prompt": exercise, "hint": "先保持现有输入的结果，再为新边界增加独立输入。", "answer": answer}],
        explain=explain, output=output,
    )
    author.write_topic(topic)
