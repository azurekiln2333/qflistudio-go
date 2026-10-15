#!/usr/bin/env python3
"""Post-apply byte-invariance check (run ONLY after an authorized shared apply).

Compares the live shared aggregate against the pre-apply originals captured in
`apply-backup/` and asserts:
  * every byte OUTSIDE the replaced Go run is identical (prefix + suffix);
  * non-Go entry count matches the original (expected 1520/file);
  * Go entry count is 120/file and equals the applied slice;
  * the pre-apply originals still hash to the recorded sha files.

Read-only. Does not modify anything.

Usage:
    python tool/go_curriculum/mobile_check/verify_shared_apply.py \
        --shared ../qfli_studio_core/assets/content \
        --backup tool/go_curriculum/apply-backup
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]


def raw_entry_spans(text: str) -> list[tuple[str, int, int, str]]:
    m = re.search(r'"entries"\s*:\s*\[', text)
    if not m:
        raise AssertionError("no entries[] found")
    i = m.end()
    spans: list[tuple[str, int, int, str]] = []
    depth = 0
    start = None
    in_str = False
    esc = False
    while i < len(text):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    raw = text[start : i + 1]
                    idm = re.search(r'"id"\s*:\s*"([^"]+)"', raw)
                    spans.append(((idm.group(1) if idm else "?"), start, i + 1, raw))
                    start = None
            elif ch == "]" and depth == 0:
                break
        i += 1
    return spans


def go_span(text: str) -> tuple[int, int]:
    """(start,end) covering the contiguous run of Go entries by scanning raw ids.

    Go entries in the aggregate have ids like go-tutorial-NNN / go-example-NNN.
    """
    spans = raw_entry_spans(text)
    go = [s for s in spans if s[0].startswith(("go-tutorial-", "go-example-"))]
    if not go:
        raise AssertionError("no Go entries found")
    return go[0][1], go[-1][2]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shared", type=Path, required=True)
    ap.add_argument("--backup", type=Path, required=True)
    args = ap.parse_args(argv)

    failures: list[str] = []
    for name in ("tutorials.json", "examples.json"):
        original_path = args.backup / f"original-{name}"
        applied_path = args.backup / f"applied-go-{name}"
        sha_path = args.backup / f"sha-{name}.txt"
        if not original_path.is_file() or not applied_path.is_file():
            failures.append(f"{name}: missing backup artifacts under {args.backup}")
            continue
        original = original_path.read_text(encoding="utf-8")
        current = (args.shared / name).read_text(encoding="utf-8")

        # 1. prefix/suffix bytes outside the Go run unchanged
        os_, oe = go_span(original)
        cs, ce = go_span(current)
        if original[:os_] != current[:cs]:
            failures.append(f"{name}: prefix bytes changed")
        if original[oe:] != current[ce:]:
            failures.append(f"{name}: suffix bytes changed")

        # 2. counts
        orig_entries = json.loads(original)["entries"]
        cur_entries = json.loads(current)["entries"]
        orig_non_go = [e for e in orig_entries if str(e.get("type", "")).lower() != "go"]
        cur_non_go = [e for e in cur_entries if str(e.get("type", "")).lower() != "go"]
        cur_go = [e for e in cur_entries if str(e.get("type", "")).lower() == "go"]
        if len(cur_non_go) != len(orig_non_go):
            failures.append(f"{name}: non-Go count {len(cur_non_go)} != {len(orig_non_go)}")
        if len(cur_go) != 120:
            failures.append(f"{name}: Go count {len(cur_go)} != 120")
        applied = json.loads(applied_path.read_text(encoding="utf-8"))
        if cur_go != applied:
            failures.append(f"{name}: live Go slice != applied-go backup")

        # 3. original sha matches recorded
        if sha_path.is_file():
            want = sha_path.read_text(encoding="utf-8").strip()
            got = hashlib.sha256(original_path.read_bytes()).hexdigest()
            if want != got:
                failures.append(f"{name}: original sha mismatch")

        if not any(f.startswith(name) for f in failures):
            print(f"OK {name}: prefix/suffix bytes preserved, "
                  f"non-Go={len(cur_non_go)}, Go={len(cur_go)}")

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        return 1
    print("SHARED APPLY VERIFY OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
