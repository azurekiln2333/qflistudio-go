#!/usr/bin/env python3
"""Run every single-file Go sample under the host-side Yaegi probe.

Produces per-item evidence for the runtime-honesty gate (R5/AC2): which samples
the pinned Yaegi version accepts and runs with the expected stdout. Evidence
level is HOST interpreter run, not a device run.

Usage:
    python tool/go_curriculum/mobile_check/run_yagi.py [--only T001,T002]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
TOPICS = TOOL / "topics"
SAMPLES = TOOL / "samples"
GO = Path(
    os.environ.get(
        "QFLI_GO_CURRICULUM_GO",
        str(TOOL.parents[1] / "native" / "build" / "go-sdk-1.27.1" / "go" / "bin" / "go.exe"),
    )
)
OUT = TOOL / "evidence" / "mobile-check-host.json"


def load_env() -> dict:
    env = dict(os.environ)
    env["GOMAXPROCS"] = "2"
    env["GOFLAGS"] = "-p=1"
    env["GOTOOLCHAIN"] = "local"
    return env


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="")
    args = parser.parse_args(argv)
    wanted = {x.strip() for x in args.only.split(",") if x.strip()}

    results = []
    failures = 0
    for path in sorted(TOPICS.glob("T*.json")):
        topic = json.loads(path.read_text(encoding="utf-8"))
        if wanted and topic["id"] not in wanted:
            continue
        if topic["importKind"] != "single-file" or len(topic["sampleFiles"]) != 1:
            results.append({"id": topic["id"], "skipped": "not single-file"})
            continue
        sample = SAMPLES / topic["id"] / topic["sampleFiles"][0]
        proc = subprocess.run(
            [str(GO), "run", ".", "-file", str(sample)],
            cwd=Path(__file__).resolve().parent,
            env=load_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        expected = topic["verification"].get("expected", "")
        got = proc.stdout.replace("\r\n", "\n").strip()
        want = expected.replace("\r\n", "\n").strip()
        ok = proc.returncode == 0 and got == want
        if not ok:
            failures += 1
        results.append(
            {
                "id": topic["id"],
                "sample": topic["sampleFiles"][0],
                "yaegiExit": proc.returncode,
                "stdoutMatchesExpected": got == want,
                "ok": ok,
                "stderr": proc.stderr.strip()[:400],
            }
        )
        print(f"{'OK  ' if ok else 'FAIL'} {topic['id']}")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"YAEGI HOST: {len(results)} items, {failures} failed -> {OUT}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
