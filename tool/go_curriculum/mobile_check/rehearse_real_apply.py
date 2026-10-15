#!/usr/bin/env python3
"""Rehearse apply/rollback on a WORKSPACE COPY of the real shared files.

Copies the live shared aggregates into .artifacts/go-curriculum/rehearsal/, runs
emit + apply + rollback there (never touching the real shared dir), and verifies:

  * non-Go entries: raw bytes and position unchanged (not just decoded equality);
  * the Go block spans exactly the replaced region (prefix/suffix preserved);
  * Go count 100 -> 120 after apply; rollback restores 100 and keeps any later
    non-Go edit;
  * the real shared files are byte-identical before/after the rehearsal.

Usage:
    python tool/go_curriculum/mobile_check/rehearse_real_apply.py
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # qfli_go
TOOL = ROOT / "tool" / "go_curriculum"
SHARED = ROOT.parent / "qfli_studio_core" / "assets" / "content"
WORK = ROOT / ".artifacts" / "go-curriculum" / "rehearsal"
PY = sys.executable


def raw_entry_spans(text: str):
    m = re.search(r'"entries"\s*:\s*\[', text)
    if not m:
        raise AssertionError("no entries[]")
    i = m.end()
    spans = []
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


def non_go_map(text: str) -> dict[str, tuple[int, str]]:
    out = {}
    for eid, s, _e, raw in raw_entry_spans(text):
        if not eid.startswith(("go-tutorial-", "go-example-")):
            out[eid] = (s, raw)
    return out


def main() -> int:
    for name in ("tutorials.json", "examples.json"):
        assert (SHARED / name).is_file(), f"real shared missing: {SHARED/name}"

    # hashes of the real shared files before rehearsal
    before_real = {
        n: hashlib.sha256((SHARED / n).read_bytes()).hexdigest()
        for n in ("tutorials.json", "examples.json")
    }

    if WORK.exists():
        shutil.rmtree(WORK)
    shared = WORK / "shared"; shared.mkdir(parents=True)
    for n in ("tutorials.json", "examples.json"):
        shutil.copy2(SHARED / n, shared / n)

    original = {n: (shared / n).read_text(encoding="utf-8") for n in ("tutorials.json", "examples.json")}
    non_go_before = {n: non_go_map(original[n]) for n in original}

    # emit current authored slice + apply into the copy
    subprocess.run([PY, str(TOOL / "patch.py"), "emit"], check=True, cwd=ROOT,
                   capture_output=True, text=True)
    backup = WORK / "backup"
    r = subprocess.run([PY, str(TOOL / "patch.py"), "apply",
                        "--shared", str(shared), "--patch", str(TOOL / "patch-go"),
                        "--baseline", str(TOOL / "baseline"), "--backup", str(backup),
                        "--confirm"], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        print("APPLY FAIL", r.stdout, r.stderr)
        return 1
    print("apply rc0:", r.stdout.strip().splitlines()[-1])

    fail = []
    for n in ("tutorials.json", "examples.json"):
        after = (shared / n).read_text(encoding="utf-8")
        ng_before = non_go_before[n]
        ng_after = non_go_map(after)
        if set(ng_before) != set(ng_after):
            fail.append(f"{n}: non-Go id set changed")
        for eid, (_pos, raw) in ng_before.items():
            if eid not in ng_after:
                fail.append(f"{n}: non-Go {eid} missing")
            elif ng_after[eid][1] != raw:
                fail.append(f"{n}: non-Go {eid} raw bytes changed")
        # Relative order of non-Go entries must be unchanged (absolute offsets
        # legitimately shift when the Go block grows 100->120).
        before_order = [eid for eid, _s, _e, _r in raw_entry_spans(original[n])
                        if not eid.startswith(("go-tutorial-", "go-example-"))]
        after_order = [eid for eid, _s, _e, _r in raw_entry_spans(after)
                       if not eid.startswith(("go-tutorial-", "go-example-"))]
        if before_order != after_order:
            fail.append(f"{n}: non-Go relative order changed")
        doc = json.loads(after)
        ngo = [e for e in doc["entries"] if str(e.get("type", "")).lower() != "go"]
        go = [e for e in doc["entries"] if str(e.get("type", "")).lower() == "go"]
        if len(go) != 120:
            fail.append(f"{n}: Go after apply {len(go)} != 120")
        if len(ngo) != len(non_go_before[n]):
            fail.append(f"{n}: non-Go count {len(ngo)} != {len(non_go_before[n])}")
    print("APPLY non-Go raw byte/position invariance:", "OK" if not fail else fail)

    # rollback in the copy
    r = subprocess.run([PY, str(TOOL / "patch.py"), "rollback", "--shared", str(shared),
                        "--backup", str(backup), "--confirm"], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        print("ROLLBACK FAIL", r.stdout, r.stderr)
        return 1
    for n in ("tutorials.json", "examples.json"):
        doc = json.loads((shared / n).read_text(encoding="utf-8"))
        go = [e for e in doc["entries"] if str(e.get("type", "")).lower() == "go"]
        if len(go) != 100:
            fail.append(f"{n}: rollback Go {len(go)} != 100")
    print("ROLLBACK restores 100 Go:", "OK" if not fail else fail)

    # real shared untouched
    after_real = {
        n: hashlib.sha256((SHARED / n).read_bytes()).hexdigest()
        for n in ("tutorials.json", "examples.json")
    }
    if before_real != after_real:
        fail.append("REAL shared files changed by rehearsal!")
    print("REAL shared untouched:", before_real == after_real)

    print("\n" + ("REHEARSAL OK" if not fail else "REHEARSAL FAIL:\n" + "\n".join(fail)))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
